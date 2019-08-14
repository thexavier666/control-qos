from bottle import run,route
from DataManager import returnMetric,fetchPort,startLoggingApache, DIRECTORY, PROJECT_HOME, HOST_IP
from LocalManager import exit_handler,recentPID, spawnCont, killCont,killAll , startAB, initialBandwidth, addABServer
import os


# Folder Structure Paths
# directory='database'
# PROJECT_HOME = '/home/kaustavc/cd container_qos_ndl'

def startLocalManager(policy_status):    
    # os.popen("sudo python3 {0} >> {1}/dm_errors".format('~/cd container_qos_ndl/code/LocalManager.py','~/cd container_qos_ndl/database') )
    os.popen("sudo python3 {0} {1}".format('~/container_qos_ndl/code/LocalManager.py', policy_status))
    return "Local Manager Started!"

def startDataManager():
	os.popen("sudo python3 {}".format('~/container_qos_ndl/code/DataManager.py'))
	return "DM Started!"

def killLocalManager():
    # shutdown gracefully
    exit_handler()
    runs = os.popen('pgrep -f  LocalManager.py').read()
    os.popen('sudo kill -9 {}'.format(' '.join(runs.split('\n')) ) )    
    return "CLOSED LM"

def clearDB():
    os.popen('sudo rm {}/{}/*'.format(PROJECT_HOME,DIRECTORY) )    

def networkLoad():
	return str(returnMetric(metric_name='total_network') )

# def startABLoads(target_IP,target_port,duration=60):
#     os.popen('echo kaustav123 | sudo docker run --rm jordi/ab -c 1 -t {} http://{}:{}/hostedFiles/file1m'.format(duration,target_IP,target_port)).read()


if __name__ == '__main__':    
	# startLocalManager()


	# 	GM CONTROL OPERATIONS  ------------------------

	route('/startLM/<policy_status>')(startLocalManager)
	route('/startDM')(startDataManager)
	route('/killLM')(killLocalManager)

	# Spawn a container using image name and optionally container_name (during migration)
	route('/LM/start/<image_name>')(spawnCont)
	route('/LM/start/<image_name>/<cont_name>')(spawnCont)
	route('/LM/start/<image_name>/<cont_name>/<port>')(spawnCont)
	route('/LM/start/<image_name>/<port>')(spawnCont)

	# AB Functions:    
	route('/LM/startab/<ab_to>/<port>/<file_name>')(startAB)
	route('/LM/startab/<ab_to>/<port>/<file_name>/<duration>')(startAB)	


	# clear database
	route('/LM/cleardb')(clearDB)

	# stop a running container
	route('/LM/kill/<cont_name>')(killCont)
	route('/LM/killall')(killAll)


	# GM MONITORING OPERATIONS  ------------------------

	route('/LM/networkload')(networkLoad)
	route('/LM/initialbw')(initialBandwidth)

	route('/LM/addABServer')(addABServer)

	# DM MONITORING OPERATIONS  ------------------------
	route('/DM/fetchPort/<cont_name>')(fetchPort)  
	route('/DM/startLoggingApache/<cont_name>')(startLoggingApache)  


	run(host='10.72.22.{}'.format(HOST_IP.split('.')[-1] ),port=1111,reloader=True,debug=True)

	

	'''
	# Issuing Request from another machine: 
	requests.get('http://10.5.20.81:8080/LM',proxies={'http':None})
	'''
