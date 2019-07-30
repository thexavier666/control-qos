import json
import matplotlib.pyplot as plt

delays,states, pid_ops, sigms=[],[],[],[]

for line in open('State_history','r+'):        
	d1= dict(eval(line.strip()) ) 
	states.extend([d1[k] for k in d1.keys()]  ) 

for line in open('silly_khorana.delays','r+'):                        
	delays.append(float(line.strip()))			

for line in open('PID.actions','r+'):                        
         d1=eval(line.strip())     
         for k,val in d1.items():
         	pid_ops.append(val[0])
         	sigms.append(val[1])                  	 
		#print(k,"->",val )                   
#plt.figure(1)
print("{} , {} , {}".format(len(states),len(delays),len(pid_ops) ) )
plt.figure(1)
plt.plot(states)
plt.plot(pid_ops)

plt.figure(2)
plt.plot(delays)
#plt.plot(sigms) # RANGE TOO HIGH
plt.show()				
