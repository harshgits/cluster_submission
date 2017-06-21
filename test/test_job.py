from time import sleep
from random import random
from numpy import savetxt, array
import os, sys

def main():
	sleep(15) #sleep for 15 seconds

	#saving a random number as the result
	if not os.path.isdir(str(__file__) + '_data'): os.makedirs(str(__file__) + '_data')
	savetxt(fname = os.path.join(str(__file__) + '_data', str(sys.argv[-1]) + '.csv'), X = array([[random()]]), header = 'result', delimiter = ',', fmt = '%s', comments = '')

if __name__=='__main__':
    main()