import math,time,os,sys
import docker
import atexit

from simple_pid import PID
import matplotlib.pyplot as plt, numpy as np
from DataManager import returnMetric, startLoggingApache, DIRECTORY, PROJECT_HOME, HOST_IP
from threading import Thread,Lock
import requests
client=docker.from_env()

import logging

logger=logging.getLogger(__name__)  
# formatter=logging.Formatter('%(asctime)s:%(filename)s:%(funcName)s')

file_handler=logging.FileHandler( os.path.join(PROJECT_HOME,DIRECTORY,'local_manager.log') )
# file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

def excepthook(*args):
  logger.exception('Uncaught exception:', exc_info=args)

sys.excepthook = excepthook


## LOGGING FOR METRICS	
# perf_metrics=logging.getLogger(__name__)  
# # formatter=logging.Formatter('%(asctime)s:%(filename)s:%(funcName)s')

# perf_handler=logging.FileHandler( os.path.join(PROJECT_HOME,DIRECTORY,'lm_metrics.log') )
# # file_handler.setFormatter(formatter)

# perf_metrics.addHandler(perf_handler)
# perf_metrics.setLevel(logging.DEBUG)


# GLOBALS

exited=False
pid_interval=1
mu,sdev=(1.3*0.00013148409149053243, 2.9153413273542698e-06)

rm_lock = Lock()

action = {}
challenges={}
cont_delays={}
# nw_conts=[]


# GATEWAY FUNCTIONS:

def spawnCont(image_name,cont_name=None,port=0):
	# LM spawns the container, and informs GM of the new location of this container
	if image_name[:2]=='fi':
		cont= client.containers.run(image='fio_ubuntu:v5',remove=True,detach=True,privileged=True,tty=True,volumes={'/mnt/': {'bind': '/fio_out', 'mode': 'rw' }} )

		#fio_cont_id = os.popen("docker ps | grep fio_ubuntu:v5 | awk '{print $1}'")
		#fio_cont_id_str = fio_cont_id.read().strip()
		#os.popen("docker exec -it {} sh /bin/fiojob.sh".format(fio_cont_id_str))

		fio_cmd_str = "sudo fio --name=/mnt/randwrite_work --rw=randwrite --direct=1 --ioengine=libaio --bs=8M --numjobs=50 --size=8G"

		import subprocess as sp
		sp.Popen(fio_cmd_str,shell=True)

		print("FIO cmd = {}".format(fio_cmd_str))

		logger.info( 'started FIO container {}'.format(cont_name) )

	elif image_name.split('_')[1]=='server:v4':
		cont = client.containers.run(image=image_name,remove=True,name=cont_name,detach=True,ports={'80/tcp':port})				
		logger.info( 'started APACHE container {}'.format(cont_name) )

	return {cont.name:HOST_IP}

def startAB(ab_to,port,file_name,duration=180):
	os.popen('sudo docker run --rm jordi/ab -c 1 -t {0} http://10.72.22.{1}:{2}/hostedFiles/{3} > ~/Container_Work/database/ab_out_{1}_{2}_{3}.txt'.format(duration,ab_to,port,file_name) )	
	logger.info( 'started AB container' )

def killCont(cont_name):
	image=None	
	for cont in client.containers.list():
		if cont.name==cont_name:

			# RETURNS ORIGINAL IMAGE IT WAS BUILT FROM			
			#image=cont.image.attrs['ContainerConfig']['Image'] ANOTHER ALTERNATIVE		
			image=str(cont.image.tags[0] )	 

	os.popen("sudo docker stop {}".format(cont_name) )				
	logger.info('killed {} container {}'.format(image,cont_name) )

	time.sleep(1)
	# print("KILLED")		
	return image

def killAll():
	os.popen("sudo docker stop $(sudo docker ps -q)")	
	logger.info('KILLED all containers')

def restart_program():
    """Restarts the current program, with file objects and descriptors
       cleanup
    """

    try:
        p = psutil.Process(os.getpid())
        for handler in p.get_open_files() + p.connections():
            os.close(handler.fd)		            
    except Exception as e:
        logging.error(e)

    python = sys.executable
    exit_handler()
    os.execl(python, python, *sys.argv)	

def addABServer():
	new_apache= spawnCont('ab_server:v4')
	try:
		cont_name = list ( new_apache.keys() )[0]				

		port_file=os.path.join(PROJECT_HOME,DIRECTORY,cont_name)		
		os.popen('wget --no-proxy http://10.5.20.81:1111/DM/startLoggingApache/{}'.format(cont_name) )
		# time.sleep(1)
		# new_port=os.popen('cat {} '.format(port_file) ).read().strip()				

		running_conts = client.containers.list()
		nw_conts=[x for x in running_conts if x.image.attrs['ContainerConfig']['Image'][:2]=='ab' ]

		for other_nw in nw_conts:
			if other_nw.name==cont_name:
				new_port=other_nw.attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
		
		logger.info("Done adding  Apache")				

		# os.popen('wget --no-proxy http://10.5.20.82:1111/LM/startab/81/{}'.format(new_port) )
		logger.info("Started logging {}".format(cont_name))

		# restart_program()		

	except:
		logger.exception('addABServer ERROR: ')				

# -------------------------------------------------------

def initialBandwidth():
	running_conts = client.containers.list()
	nw_conts=[x.name for x in running_conts if x.image.attrs['ContainerConfig']['Image'][:2]=='ab' ]
	num_servers=len(nw_conts)

	try:
		init_bw=int(900/num_servers)
		
		for cont in nw_conts:		
			allocateBandwidth(cont,init_bw)
		logger.info('Given Initial Bandwidth = {}'.format(init_bw))
	except:
		logger.exception('LM : initialBandwidth ERROR {}'.format(nw_conts) )
							
def allocateBandwidth(cont_name,new_bandwidth):	
	try:
		port= int( requests.get('{}:1111/DM/fetchPort/{}'.format(HOST_IP,cont_name) , proxies={'http':None}).text )
		os.popen('sudo sh {0}/ratelimit.sh iface=eth0 src_port={1} bw_ceil={2}MBit bw_rate={2}MBit'.format( os.path.join(PROJECT_HOME,'bash_scripts'),port, new_bandwidth) )
		# logger.info('sudo sh {0}/ratelimit.sh iface=eth0 src_port={1} bw_ceil={2}MBit bw_rate={2}MBit'.format( os.path.join(PROJECT_HOME,'bash_scripts'),port, new_bandwidth))
	except:
		logger.exception('LM : allocateBandwidth ERROR ')
		# logger.info('http://{}:1111/DM/fetchPort/{}'.format(HOST_IP,cont_name))


def resolve(cont_name):
	try:
		#  ACQUIRE LOCK 
		rm_lock.acquire()

		logger.info("{} Challenged ".format(cont_name) )
		if cont_name not in challenges:
			challenges[cont_name]=0
		else:
			challenges[cont_name]+=1			

		last_pid={}
		sum_pid=0

		running_conts = client.containers.list()
		nw_conts=[x.name for x in running_conts if x.image.attrs['ContainerConfig']['Image'][:2]=='ab' ]

		for other_nw in nw_conts:
			pid_i=recentPID(other_nw)
			last_pid[other_nw]=max(1,pid_i)
			sum_pid+=max(1,pid_i)

		running_conts = client.containers.list()
		nw_conts=[x.name for x in running_conts if x.image.attrs['ContainerConfig']['Image'][:2]=='ab' ]

		# CAPACITY = 900 MBit			 						
		for other_nw in nw_conts:
			new_bw= (last_pid[other_nw]/sum_pid) * 900 
			allocateBandwidth(cont_name=other_nw,new_bandwidth=new_bw)		
			logger.info("Assigned new BW {} to {}".format(new_bw,other_nw) ) 			
			if other_nw==cont_name:
				action[other_nw]=[0]*5

		logger.info('\n')
		# RELEASE LOCK		
		time.sleep(5)
		rm_lock.release()

		others_fine=True
		# check if other containers are now suffering:
		for other_pid in action.keys():
			if other_pid==cont_name: continue
			if sum(action[other_pid])>=490:
				others_fine=False
		
		# MIGRATE
		if(challenges[cont_name]==3):
			# mig_conf=requests.get('http://10.5.20.124:1234/GM/Migrate_apache/{}'.format(cont_name) ,proxies={'http':None}).text
			logger.info("MIGRATE {}".format(cont_name) )			

	except:		
		logger.exception("Resolve {}".format(cont_name) )

	return others_fine

def sigmoid(pid_op):	
	sigm = 100*math.exp(0.06*pid_op-6)/(1+math.exp(0.06*pid_op-6))
	return sigm


def run_pid(cont_name,interval=1):
	starttime=time.time()
	time.sleep(interval - ((time.time() - starttime) % (interval) ) )

	this_pid=PID(2,0.05,0.0001,setpoint=mu,output_limits=(-50,200))
	this_pid.sample_time=pid_interval		

	logger.info("started  PID for {}".format(cont_name) )

	while not exited:
		try:
			# state = returnMetric(cont_name=cont_name,metric_name='delay')		
			state =os.popen("cat {}.delays | tail -1".format( os.path.join(PROJECT_HOME,DIRECTORY,cont_name)) ).read().strip()
			# logger.info('Delay for {} = {}'.format(cont_name,state) )
			if not len(state)>0:
				continue						 
			state= float(state)	
		except:
			continue			

		try:
			cont_delays[cont_name].append(state);
			cont_delays[cont_name].pop(0)

			# AVERAGING DISABLED TO MAKE PID MORE REACTIVE
			# state= np.mean(cont_delays[cont_name])
			
			state = (state-mu)/sdev
			pid_op = this_pid(this_pid.setpoint-state)

			sigm = sigmoid(pid_op)

			# window of last five PID outputs:
			action[cont_name].append(sigm)
			action[cont_name].pop(0)

			# check if current container is suffering
			if sum(action[cont_name])>=490:				
				others_fine = resolve(cont_name)				
				if others_fine:
					challenges[cont_name]=0

			if challenges[cont_name]==3:								
			 	# DECIDE BEST HOST -> MIGRATE
				#requests.get('http://10.5.20.124:1234/GM/Migrate_apache/{}'.format(cont_name),proxies={'http':None}).text
				logger.info("Migrate called for {}".format(cont_name))

		except:
			logger.exception("PID Error : {}".format(cont_name) )			
		time.sleep(interval - ((time.time() - starttime) % interval))	

def recentPID(cont_name):
	if cont_name not in action:
		return 0
	else:
		return action[cont_name][-1]

def exit_handler():
	exited= True
	runs = os.popen('pgrep -f  DataManager.py').read()
	os.popen('sudo kill -9 {}'.format(' '.join(runs.split('\n')) ) )
	os.system('sudo pkill tcpdump')
	os.system('sudo kill -9 $(pgrep -f dstat)')
	# print("CLOSED")
	logger.info('LM CLOSED')	

if __name__ == '__main__':
	atexit.register(exit_handler)
	os.popen("sudo python3 {0} ".format('~/Container_Work/code/DataManager.py') )
	logger.info("STARTED DM")

	pid_hist = open( os.path.join(PROJECT_HOME,DIRECTORY,'PID.actions'),'w')
	state_hist=open( os.path.join(PROJECT_HOME,DIRECTORY,'State_History'),'w')
	challenge_state=open( os.path.join(PROJECT_HOME,DIRECTORY,'Challenges'),'w')

	running_conts=client.containers.list()
	try:
		# nw_conts.extend( [x.name for x in running_conts if x.image.attrs['ContainerConfig']['Image'][:2]=='ab' ] )
		nw_conts=[x.name for x in running_conts if x.image.attrs['ContainerConfig']['Image'][:2]=='ab' ]
	except:
		logger.exception('EXTENDING nw_conts' )
	logger.info('initialized NW CONTS - {}'.format(nw_conts) )		

	initialBandwidth()	
							

	# 1 : turning on policy
	if sys.argv[1] == '1':

		# Start PIDs for each container
		for cont in nw_conts:			
			action[cont]=[0]*5
			cont_delays[cont] = [0]*5
			challenges[cont]=0
			Thread(target=run_pid, args=(cont,pid_interval ) ).start()
	elif sys.argv[1] == '0':
		logger.info('policy not set, no PID running')
	else:
		logger.exception('Local Manager : Wrong argument {}'.format(sys.argv[1]))
		#exit(1)


	while True:
		# TERMINATE ALL THREADS ON SIGKILL
		if any(action):
			pid_hist.write(str(action)+'\n')
			pid_hist.flush()
		
		if any(cont_delays):
			state_hist.write(str(cont_delays)+'\n')
			state_hist.flush()		

		if any(challenges):
			challenge_state.write(str(challenges)+'\n')
			challenge_state.flush()
		time.sleep(2)

