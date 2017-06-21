# Cluster Submission

Cluster Submission is a tool I made to automate the submission of jobs to computer clusters. Its purpose is to maximize the capacity utilization of a fixed number of CPU cores. It does so by actively monitoring user jobs running on the cluster and dynamically submitting new jobs to the cluster whenever previously submitted jobs complete execution. It also automatically re-submits jobs that were submitted to the cluster but were killed i.e. weren't allowed to run to completion.

The tool performs two major functions: job queuing and job submission. The tool is a Python module and the two functions are implemented in the module literally as functions viz. que_jobs() and cluster_submitter().
- que_jobs() is used to submit new jobs to the job queue that is stored in the user's home directory in a file cluster_que.pickle
- cluster_submitter() grabs jobs from this queue and submits them to the cluster

## Getting Started

### Prerequisites

- A UNIX cluster that supports the use of PBS for job scheduling
- Any [Anaconda Python 2.7.x](https://www.continuum.io/downloads) distribution
- The filelock module (included)


### Installing

Simply place the Cluster_submission.py and filelock.py files in the site-packages folder in your home directory on the cluster e.g. ~/.local/lib/python2.7/site-packages/


### How To Use

I've written Cluster Submission primarily for myself and other individuals working on stochastic simulations that need to be run several times independently. The jobs therefore best suited for use with Cluster Submission are of the "embarrassingly parallel" variety i.e. parallel jobs that don't need to communicate with each other. For non-embarrassingly parallel jobs, you're far better off using MPI or similar tools.

We will now demonstrate the use of the module with a test. In a new terminal on the cluster, navigate to the test/ folder provided with this installation. Launch the Python interpreter in a screen with the "screen python" (no quotes) command. Run the following code in the interpreter to start the submitter.

```
from cluster_submission import cluster_submitter
cluster_submitter()
```

This should launch the submitter which will display information about the number of jobs running, jobs awaiting submission and so on. The maximum number of running jobs is set to 400 and the interval between submission attempts is set to 1 minute. These can be changed via the max_jobs and minutes_between_submission arguments that may be passed to cluster_submitter(). The submitter should stay running in the background. If you need to log out of your account, you can keep the submitter running in the background by detaching from the screen via the C-a d command before logging out. For more about using screen see http://aperiodic.net/screen/quick_reference

The submitter is now running and actively monitoring the queue (~/cluster_que.pickle) for new jobs to submit. We will now add some jobs to this queue. In a new terminal, launch a python interpreter with the "python" (no quotes) command (no screen needed here). We will add 1000 jobs of test_job.py to the queue via the following code:

```
from cluster_submission import que_jobs
que_jobs(job_path = 'test_job.py', nu_jobs = 1000, walltime = '00:01:00')
```

Each run of test_job.py should take about 15 seconds to complete but we've specified a walltime of 1 minute to account for overheads such as import time etc. This code should submit 1000 jobs of test_job.py to the que. cluster_submitter() (which is running in another terminal) will "grab" 400 of these and submit them to different procs on the cluster. It will check for completed jobs once every minute by looking for output files in the test_job_data/ folder. Whenever it notices completed jobs, it will grab that many new jobs from the queue and submit them to the cluster. If any jobs get killed mid execution, it will automatically resubmit them. If everything is works as it should, and the cluster isn't already running at capacity, you should have 1000 data files back in the data folder in a couple of minutes.

You need to run que_jobs() every time you want to add new jobs to the queue. You only need to run cluster_submitter() once and keep it running in the background.