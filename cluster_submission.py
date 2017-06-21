# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Cluster Submission is a tool I made to automate the submission of jobs to computer clusters. Its purpose is to maximize the capacity utilization of a fixed number of CPU cores. It does so by actively monitoring user jobs running on the cluster and dynamically submitting new jobs to the cluster whenever previously submitted jobs complete execution. It also automatically re-submits jobs that were submitted to the cluster but were killed i.e. weren't allowed to run to completion.

The tool performs two major functions: job queuing and job submission. The tool is a Python module and the two functions are implemented in the module literally as functions viz. que_jobs() and cluster_submitter().
- que_jobs() is used to submit new jobs to the job queue that is stored in the user's home directory in a file named cluster_que.pickle
- cluster_submitter() grabs jobs from this queue and submits them to the cluster
'''

import os, time, datetime, fnmatch, filelock, cPickle
from copy import deepcopy
from glob import glob

def que_jobs(job_path, nu_jobs, walltime):
	cluster_que_path = os.path.join(os.path.expanduser('~'),'cluster_que.pickle') #location of pickled que
	cluster_que = [] #will contain contents of que
	if os.path.isfile(cluster_que_path): #load que
		with filelock.FileLock(cluster_que_path+'.lock'): cluster_que += cPickle.load(open(cluster_que_path, 'rb')) #que = [{'py_path': '~/wewe/wew.py', 'jobs': 1000, 'walltime': '20:00:00'}, {}, {}]
	new_jobs = [{'job_path': os.path.abspath(os.path.join(root, fil)), 'nu_jobs': nu_jobs, 'walltime': walltime} for root, dirs, files in os.walk('.') for fil in files if fnmatch.fnmatch(os.path.normpath(os.path.join(root, fil)), os.path.normpath(job_path))]
	cluster_que += new_jobs #append new jobs to que
	with filelock.FileLock(cluster_que_path+'.lock'): cPickle.dump(cluster_que, open(cluster_que_path, 'wb')) #save que
	print 'Successfully added these job(s) to ' + cluster_que_path + ': ' + str(new_jobs)

def cluster_submitter(max_jobs = 400, minutes_between_submissions = 1):
	def nu_job_returns(job_path):
		job_folder_path, job_name = os.path.split(job_path)
		job_return_folder = os.path.join(job_folder_path, job_name+'_data')
		return len(['' for fil in os.listdir(job_return_folder) if fnmatch.fnmatch(fil, '*.csv')]) if os.path.isdir(job_return_folder) else 0

	def qsub(job): #create and run cluster.sh script for job submission
		this_dir = os.getcwd()
		job_folder_path, job_name = os.path.split(job['job_path'])
		os.chdir(job_folder_path)
		sh_content='''#!/bin/bash
		#
		#PBS -l walltime='''+job['walltime']+'''
		#PBS -l procs=1
		#PBS -j oe
		#
		cd $PBS_O_WORKDIR
		#
		python '''+job_name+''' ${PBS_JOBID}'''
		submit_file_name = 'cluster_submit_' + job_name + '.sh'
		with open(submit_file_name, 'w') as f:
			f.write(sh_content)
		os.system('qsub -t 1-' + str(job['nu_jobs']) + ' ' + submit_file_name)
		os.remove(submit_file_name)
		os.chdir(this_dir)

	def update_jobs_running_info(jobs_running_info):
		jobs_running_info['nu_resubbed'] = 0
		completed_job_nus = []
		for job_nu in range(len(jobs_running_info['jobs'])):
			job = jobs_running_info['jobs'][job_nu] #job = {'job_path': assd, 'nu_jobs': 12, 'nu_returns': 5}
			job_folder_path, job_name = os.path.split(job['job_path'])
			job_return_folder = os.path.join(job_folder_path, job_name+'_data')

			#updating job_submission_times by looking at log (.sh) files
			for sh_file in [fil for fil in os.listdir(job_folder_path) if fnmatch.fnmatch(fil, '*' + job_name +'.sh*')]:
				if len(job['job_submission_times']) < job['nu_jobs'] and sh_file not in [job_submission_time_info['sh_file'] for job_submission_time_info in job['job_submission_times']]:
					job['job_submission_times'].append({'sh_file': sh_file, 'submission_time': datetime.datetime.now()})
				os.remove(os.path.join(job_folder_path, sh_file))

			#updating the returned jobs
			nu_returns_old = job['nu_returns']
			job['nu_returns'] = nu_job_returns(job['job_path'])
			nu_newly_returned = job['nu_returns'] - nu_returns_old
			if nu_newly_returned > 0:
				job['nu_jobs'] -= nu_newly_returned
				job['job_submission_times'] = job['job_submission_times'][nu_newly_returned:]
				jobs_running_info['nu_jobs'] -= nu_newly_returned
				if job['nu_jobs'] == 0: #noting down completed job index
					completed_job_nus = [job_nu] + completed_job_nus
			else: #if no new returns, find killed jobs and resubmit them
				hh, mm, ss = job['walltime'].split(':')
				walltime_secs = int(hh)*3600 + int(mm)*60 + int(ss)
				while len(job['job_submission_times']) > 0:
					if (datetime.datetime.now() - job['job_submission_times'][0]['submission_time']).total_seconds() > walltime_secs:
						job_to_resub = deepcopy(job)
						job_to_resub['nu_jobs'] = 1
						qsub(job_to_resub)
						job['job_submission_times'] = job['job_submission_times'][1:]
						jobs_running_info['nu_resubbed'] += 1
					else:
						break
		for job_nu in completed_job_nus: #removing completed jobs info
			jobs_running_info['jobs'].pop(job_nu)

	def submit_jobs(nu_jobs, cluster_que, jobs_running_info):
		fully_subbed_job_nus = []
		for job_nu in range(len(cluster_que)):
			job_in_que = deepcopy(cluster_que[job_nu])
			if job_in_que['nu_jobs'] <= nu_jobs:
				fully_subbed_job_nus = [job_nu] + fully_subbed_job_nus
			else:
				job_in_que['nu_jobs'] = nu_jobs
				cluster_que[job_nu]['nu_jobs'] -= nu_jobs
			qsub(job_in_que)
			nu_jobs -= job_in_que['nu_jobs']
			jobs_running_info['nu_jobs'] += job_in_que['nu_jobs']
			job_already_running = False
			for job_running_nu in range(len(jobs_running_info['jobs'])):
				job_running = jobs_running_info['jobs'][job_running_nu]
				if job_in_que['job_path'] == job_running['job_path']: #already running
					job_already_running = True
					job_running['nu_jobs'] += job_in_que['nu_jobs']
			if not job_already_running: #not found running
				job_in_que.update({'nu_returns':nu_job_returns(job_in_que['job_path']), 'job_submission_times': []})
				jobs_running_info['jobs'].append(job_in_que)
			if nu_jobs == 0:
				break
		for job_nu in fully_subbed_job_nus: #deleting fully submitted jobs from que
			cluster_que.pop(job_nu)

	def main(max_jobs, minutes_between_submissions):
		cluster_que_path = os.path.join(os.path.expanduser('~'), 'cluster_que.pickle')
		os.chdir(os.path.split(cluster_que_path)[0])
		jobs_running_info = {'jobs': [], 'nu_jobs': 0, 'nu_resubbed': 0}
		time_of_sub, killed_jobs_resubbed = 'Never', 'Never'
		time_of_next_attempt = datetime.datetime.now()
		nu_jobs_subbed = 0
		cluster_que = [] #will contain contents of que
		while(True):
			update_jobs_running_info(jobs_running_info)
			workers_free = max_jobs - jobs_running_info['nu_jobs']
			if os.path.isfile(cluster_que_path): #load que
				with filelock.FileLock(cluster_que_path+'.lock'): cluster_que = cPickle.load(open(cluster_que_path, 'rb'))
			time_of_attempt = time_of_next_attempt
			if len(cluster_que) > 0 and workers_free > 0:
				nu_running_original = jobs_running_info['nu_jobs']
				submit_jobs(workers_free, cluster_que, jobs_running_info)
				with filelock.FileLock(cluster_que_path+'.lock'): cPickle.dump(cluster_que, open(cluster_que_path, 'wb'))
				nu_jobs_subbed = jobs_running_info['nu_jobs'] - nu_running_original
				time_of_sub = time_of_attempt
			print '\n\n-----------------------------'
			print '\nJobs running: ' + str(jobs_running_info['nu_jobs']) + ' of ' + str(max_jobs) + ' max jobs'
			print '\nJobs awaiting submission: '+ str(sum([job['nu_jobs'] for job in cluster_que]))
			print '\nLast new submission: ' + str(nu_jobs_subbed) + ' jobs at ' + str(time_of_sub)
			if jobs_running_info['nu_resubbed'] > 0:
				killed_jobs_resubbed = str(jobs_running_info['nu_resubbed']) + ' jobs at ' + str(time_of_attempt)
			print '\nKilled jobs re-submitted: ' + killed_jobs_resubbed
			time_of_next_attempt += datetime.timedelta(minutes=minutes_between_submissions)
			print '\nNext submission attempt at: ' + str(time_of_next_attempt) + ' (submission is attempted every ' + str(minutes_between_submissions) + ' minutes)'
			time.sleep((time_of_next_attempt - datetime.datetime.now()).total_seconds())
			
	main(max_jobs, minutes_between_submissions)