import os,sys,re
import time
import docker
import threading
import csv
import psutil
import pandas as pd
import numpy as np
import logging,requests
client = docker.from_env()

# Folder Structure
DIRECTORY='database'
PROJECT_HOME = '/home/test/Container_Work'
HOST_IP = 'http://{}'.format(os.popen("hostname -I | awk '{print $1}'").read().strip() )

logger=logging.getLogger(__name__)

formatter=logging.Formatter('%(asctime)s:%(filename)s:%(funcName)s')

file_handler=logging.FileHandler( os.path.join(PROJECT_HOME,DIRECTORY,'data_manager.log') )
# file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

def excepthook(*args):
  logger.exception('Uncaught exception:', exc_info=args)

sys.excepthook = excepthook

# PROCESS IDs AND EXPOSED PORT NUMBERS FOR EACH CONTAINER
procs,ports={},{}
nw_names=[]

def isRunning(cont_name):
    return cont.attrs.get('State').get('Running')

# Individual Thread for each container
def logDisk(interval=1.0):
    disk_out=open(os.path.join(PROJECT_HOME,DIRECTORY,'sda_disk'),'w')
    disk_out.write("TIME,READ_BYTES,WRITE_BYTES,BUSYTIME\n")
    # starttime= time.time()
    while True:
        T1 = psutil.disk_io_counters(perdisk=True)['sda']
        time.sleep(1)
        T2 = psutil.disk_io_counters(perdisk=True)['sda']        
        disk_out.write(','.join([ str(x) for x in [time.time(), T2.read_bytes - T1.read_bytes , T2.write_bytes-T1.write_bytes, T2.busy_time-T1.busy_time]]).strip()+"\n")
        disk_out.flush()
        # time.sleep(interval - ((time.time() - starttime) % interval))

def logContainer(pid,name,interval=1.0):
    net_out= open( os.path.join(PROJECT_HOME,DIRECTORY,name)+'.network','w' )

    nw_data_columns = [ ('Recv. Bytes',1),
                        ('Recv. Pkts',2),
                        ('Sent Bytes',9),
                        ('Sent Pkts',10) ]

    net_out.write(','.join([x[0] for x in nw_data_columns])+'\n')
    starttime= time.time()
    while True :
        try:
            log_out = os.popen("cat /proc/{}/net/dev | grep eth0".format(pid) ).read()

        except:
            print("Write to {} Failed".format(procs[idx]) )
        net_out.write( ','.join( [log_out.split()[i] for i in [x[1] for x in nw_data_columns] ] )  +'\n')
        net_out.flush()
        time.sleep(interval - ((time.time() - starttime) % interval))

def logDelay(cont_name,port,interval=1):
	#start capturing packets	
	fout = open(os.path.join(PROJECT_HOME,DIRECTORY,cont_name)+'.delays','w')

	# fout.write("DELAY\n")
	# fout.flush()
	#num_pcap=False
	num_idx=0
	starttime= time.time()
	while True:
		try:
			#os.popen("sudo tcpdump -i eth0 -w {0}/{1}_{2}.pcap dst port {3} >> {0}/tmp_out".format( os.path.join(PROJECT_HOME,DIRECTORY),cont_name,int(num_idx),port) )
			os.popen("sudo tcpdump -i eth0 -w {0}/{1}_{2}.pcap dst port {3} 2> /dev/null".format( os.path.join(PROJECT_HOME,DIRECTORY),cont_name,int(num_idx),port) )
			# print("sudo tcpdump -i eth0 -w {0}/{1}_{2}.pcap dst port {3}".format( os.path.join(PROJECT_HOME,DIRECTORY),cont_name,int(num_idx),port))

			time.sleep(interval - ((time.time() - starttime) % interval))

			os.system('sudo pkill tcpdump')
			_=os.popen("tshark -r {0}/{1}_{2}.pcap -T fields -e frame.time_epoch > {0}/{1}.csv 2> /dev/null".format( os.path.join(PROJECT_HOME,DIRECTORY),cont_name,int(num_idx) )).read()

			try:
				df=pd.read_csv('{}/{}.csv'.format(  os.path.join(PROJECT_HOME,DIRECTORY) ,cont_name),header=None).astype(float)
			except:
				# fout.write( '2'+'\n' )
				# fout.flush()
				continue
			delays=[ df[0][i]-df[0][i-1] for i in range(1,len(df[0])) ]
			#fout.write( str( time.time() )+','+str(np.mean(delays))+'\n' )
			fout.write( str(np.mean(delays))+'\n' )
			fout.flush()
		except:
			logger.exception('logDelay ERROR:')

def returnMetric(metric_name,cont_name=None):
	possible_metrics=['delay','network','disk','total_network']
	try:
		assert metric_name in possible_metrics, "Invalid metric requested"
		if metric_name=='disk':
			return os.popen("cat {}.csv | tail -1".format(os.path.join(PROJECT_HOME,DIRECTORY,cont_name)) ).read().strip()
		if metric_name=='delay':
			return os.popen("cat {}.delays | tail -1".format( os.path.join(PROJECT_HOME,DIRECTORY,cont_name)) ).read().strip()			
		if metric_name=='network':
			return os.popen("cat {}.network | tail -1".format( os.path.join(PROJECT_HOME,DIRECTORY,cont_name) ) ).read().strip()

		# RETURNS DICTIONARY WITH KEYS 'epoch' , 'recv' and 'send'
		if metric_name=='total_network':
			line= str( os.popen('cat {}/Total_Network | tail -2|head -1'.format( os.path.join(PROJECT_HOME,DIRECTORY)) ).read() )			
			epoch,snt,rcv=[float(x) for x in line.strip().split(',')]
			return {'epoch':epoch,'recv':rcv,'send':snt}			
	except:
		logger.exception("returnMetric ERROR : ")

def logNetwork():
	### DSTAT BUGGY WHEN REPORTING RECV OF HOST RUNNING APACHE SERVER !! SEND IS OK 
	# os.popen("dstat -Tn > {}/Total_Network".format( os.path.join(PROJECT_HOME,DIRECTORY) ) )
			
	tot_net=open(os.path.join(PROJECT_HOME,DIRECTORY,'Total_Network'),'w')
	tot_net.write("BYTES_SENT,BYTES_RECV\n")
	tot_net.flush()
	while(True):		
		try:
			T1=psutil.net_io_counters(pernic=True)['eth0']
			time.sleep(1)
			T2=psutil.net_io_counters(pernic=True)['eth0']
			snt,rcv= T2.bytes_sent-T1.bytes_sent, T2.bytes_recv-T1.bytes_recv			
			tot_net.write("{},{},{}\n".format(time.time(),snt,rcv) ) 	
			tot_net.flush()			
		except:
			logger.exception('logNetwork ERROR: ')			

def startLoggingApache(cont_name):
	try:				
		for cnt in client.containers.list():
			if cnt.name not in nw_names and cnt.image.attrs['ContainerConfig']['Image'][:2]=='ab' :				
				ports[cnt.name]=cnt.attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
				procs[cnt.name]=cnt.attrs['State']['Pid']
				threading.Thread(target=logContainer, args=(procs[cont_name],cont_name) ).start()
				threading.Thread(target=logDelay,args=(cont_name,ports[cont_name]) ).start()        	        					
				logger.info('Started AB - {}'.format(ports[cont_name]) )		
				return ports[cont_name]
	except:
		logger.exception('startLoggingApache ERROR: ')				

def fetchPort(cont_name):
	try:
		running_conts = client.containers.list()
		nw_conts=[x for x in running_conts if x.image.attrs['ContainerConfig']['Image'][:2]=='ab' ]	
		for cnt in nw_conts:
			if cnt.name==cont_name:
				return (cnt.attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort'] )
	except:
		logger.exception('fetchPort ERROR:')						
	return ('{} not found in PORT dict'.format(cont_name) )

if __name__ == '__main__':
	running_conts = client.containers.list()

	#Image Name: conts[i].image.attrs['ContainerConfig']['Image']
	nw_conts=[x for x in running_conts if x.image.attrs['ContainerConfig']['Image'][:2]=='ab' ]
	disk_conts= [x for x in running_conts if x.image.attrs['ContainerConfig']['Image'][:2]=='fi' ]

	nw_names.extend( [x.name for x in nw_conts] )

	for cnt in nw_conts:		
		ports[cnt.name]=cnt.attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
		procs[cnt.name]=cnt.attrs['State']['Pid']		

	threading.Thread(target=logNetwork).start()		
	threading.Thread(target=logDisk).start()

	for cont_name in nw_names:
		threading.Thread(target=logContainer, args=(procs[cont_name],cont_name) ).start()
		threading.Thread(target=logDelay,args=(cont_name,ports[cont_name]) ).start()
