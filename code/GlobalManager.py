from bottle import run,route
import requests
import os,sys
import logging

#  CONT_NAME -> HOST IP
ipaddress={}
host_ips = ['http://10.5.20.81','http://10.5.20.82','http://10.5.20.83']

logger=logging.getLogger(__name__)


def get_net_cont_port():
	return 2000

# formatter=logging.Formatter('%(asctime)s:%(filename)s:%(funcName)s')

file_handler=logging.FileHandler('./global_manager.log')
# file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

def excepthook(*args):
	logger.exception('Uncaught exception:', exc_info=[x for x in args])

sys.excepthook = excepthook

## DEBUG FUNCTIONS:

def checkLocations():
	return ipaddress

## --------------------------

# Start Containers
# num_net = how many net containers to start
def InitiateSystem(num_net,policy_status):	
	responses=[]	

	# 81
	# -------------------------------------------------------

	# start fio
	responses.append( requests.get('http://10.5.20.81:1111/LM/start/fio_ubuntu:v5',proxies={'http':None}) )

	num_net_containers = int(num_net)
	net_containers_port = get_net_cont_port()

	for i in range(num_net_containers):
		responses.append( requests.get('http://10.5.20.81:1111/LM/start/ab_server:v4/{}'.format(net_containers_port),proxies={'http':None}) )
		net_containers_port += 5

	# start LM
	requests.get('http://10.5.20.81:1111/startLM/{}'.format(policy_status),proxies={'http':None})			

	# 82
	# -------------------------------------------------------

	net_containers_port = get_net_cont_port()

	for i in range(num_net_containers // 2):
		requests.get('http://10.5.20.82:1111/LM/startab/81/{}'.format(net_containers_port),proxies={'http':None})
		net_containers_port += 5

	
	# start LM
	requests.get('http://10.5.20.82:1111/startLM/{}'.format(policy_status),proxies={'http':None})	

	# 83
	# -------------------------------------------------------

	net_containers_port = get_net_cont_port() + (5 * (num_net_containers // 2))

	for i in range(num_net_containers // 2):
		requests.get('http://10.5.20.83:1111/LM/startab/81/{}'.format(net_containers_port),proxies={'http':None})
		net_containers_port += 5

	
	# start LM
	requests.get('http://10.5.20.83:1111/startLM/{}'.format(policy_status),proxies={'http':None})


	# -------------------------------------------------------

	for resp in responses:
		for cont_name,ip in resp.json().items():
			ipaddress[cont_name]=ip			


def ClearSystem():	
	requests.get('http://10.5.20.81:1111/killLM',proxies={'http':None})
	requests.get('http://10.5.20.82:1111/killLM',proxies={'http':None})
	requests.get('http://10.5.20.83:1111/killLM',proxies={'http':None})

def RebootLM():
	requests.get('http://10.5.20.81:1111/startLM',proxies={'http':None})  
	requests.get('http://10.5.20.82:1111/startLM',proxies={'http':None})  				
	requests.get('http://10.5.20.83:1111/startLM',proxies={'http':None})  				

def ClearDB():
	requests.get('http://10.5.20.81:1111/LM/cleardb',proxies={'http':None})
	requests.get('http://10.5.20.82:1111/LM/cleardb',proxies={'http':None})	
	requests.get('http://10.5.20.83:1111/LM/cleardb',proxies={'http':None})	

	requests.get('http://10.5.20.81:1111/LM/killall',proxies={'http':None})	
	requests.get('http://10.5.20.82:1111/LM/killall',proxies={'http':None})	
	requests.get('http://10.5.20.83:1111/LM/killall',proxies={'http':None})	

	ipaddress.clear()

def UpdateIP(cont_name,new_IP):
	# Update GM's knowledge of the location if this container
	ipaddress[cont_name]=new_IP		

def StartAB(ab_from,ab_to,port,duration=30 ):
	requests.get('http://10.5.20.{}:1111/LM/startab/{}/{}/{}'.format(ab_from,ab_to,port,duration) )
	# print("SENT TO LM")	

def Migrate(cont_name, IP_from, IP_to):	
	try:
		image_name = requests.get('http://{}:1111/LM/kill/{}'.format(IP_from,cont_name),proxies={'http':None}).text
		requests.get('http://{}:1111/LM/start/{}/{}'.format(IP_to,image_name,cont_name) ,proxies={'http':None})	
		ipaddress[cont_name]='http://'+IP_to		
	except:
		logger.exception('Migrate exception')	

def Migrate_apache(cont_name):
	try:
		ip_loads={}

		# FIND CURRENT OUTGOING LOAD FOR EACH HOST
		for ip in host_ips:
			if ip == ipaddress[cont_name]:
				continue
			ip_loads[ip]=eval (requests.get('{}:1111/LM/networkload'.format(ip),proxies={'http':None}).content )['send']					

		ideal_host = min(ip_loads,key=ip_loads.get ).split('/')[2]
		ip_frm=ipaddress[cont_name].split('/')[2]
		Migrate(cont_name,ip_frm,ideal_host)			
	except:
		logger.exception('Migrate_apache exception:')		
	return "MIGRATE {} to {}".format(cont_name,ideal_host)


if __name__ == '__main__':
	route('/GM/InitiateSystem/<num_net>/<policy_status>')(InitiateSystem)   
	route('/GM/ClearSystem')(ClearSystem)
	route('/GM/RebootLM')(RebootLM)

	route('/GM/UpdateIP/<cont_name>/<new_IP>')(UpdateIP)	
	#route('/GM/StartABLoads')(StartABLoads)

	route('/GM/Migrate/<cont_name>/<IP_from>/<IP_to>')(Migrate)

	route('/GM/ClearDB')(ClearDB)


	route('/GM/abload/<ab_from>/<ab_to>/<port>')(StartAB)
	route('/GM/abload/<ab_from>/<ab_to>/<port>/<duration>')(StartAB)

	## DECISION FUNCTIONS  ------------------------
	route('/GM/Migrate_apache/<cont_name>')(Migrate_apache)

	## DEBUG FUNCTIONS  ------------------------  
	route('/GM/IPS')(checkLocations)
	## -----------------------
	run(host='10.5.20.124',port=1234,reloader=True,debug=True)
	
	'''
	AB CONTAINER:
	sudo docker run --rm jordi/ab -c 1 -t 20 http://10.5.20.81:32804/hostedFiles/file1m
	
	LAUNCH AB:
	os.popen('echo kaustav123 | sudo docker run --rm jordi/ab -c 1 -t 20 http://10.5.20.82:32783/hostedFiles/file1m').read()
	'''

