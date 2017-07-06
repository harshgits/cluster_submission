from distutils.core import setup

setup(
    name='cluster_submission',
    version='1.0',
    py_modules=['cluster_submission', 'filelock'],
    description = 'Tool to automate submission of jobs to computer clusters',
    long_description = 
    '''
    Cluster Submission is a tool I made to automate the submission of jobs to computer clusters. Its purpose is to maximize the capacity utilization of a fixed number of CPU cores. It does so by actively monitoring user jobs running on the cluster and dynamically submitting new jobs to the cluster whenever previously submitted jobs complete execution. It also automatically re-submits jobs that were submitted to the cluster but were killed i.e. weren't allowed to run to completion.

    The tool performs two major functions: job queuing and job submission. The tool is a Python module and the two functions are implemented in the module literally as functions viz. que_jobs() and cluster_submitter().
    - que_jobs() is used to submit new jobs to the job queue that is stored in the user's home directory in a file named cluster_que.pickle
    - cluster_submitter() grabs jobs from this queue and submits them to the cluster
    ''',
    author = 'Harsh Chaturvedi',
    author_email = 'chaturhar(at)gmail(dot)com',
    url = 'https://github.com/harshgits/cluster_submission',
    license = 'MIT License',
      )