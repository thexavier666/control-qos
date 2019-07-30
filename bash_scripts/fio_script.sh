'''
 inside fio_ubuntu:v4
 	
 	/bin/fiojob.sh	=>
		fio /fio_out/job2.fio --directory /fio_out
	
	job2.fio	=>	
		[global]                                                            
		ioengine=libaio                                                     
		iodepth=1                                                           
		rw=randrw                                                           
		bs=2M                                                               
		direct=1                                                            
		numjobs=2                                                           
				                                                              
		[randrw]                                                            
		size=1G	
'''

sudo docker run --rm -v ~/fio_stats:/fio_stats -v /mnt/shared_dir/:/fio_out --name fiojob2  -dP -it fio_ubuntu:v5

# dstat results file name
dstat -nd -T  --disk-avgqu  --output ~/fio_stats/$1 &
sudo docker exec fiojob2 sh /bin/fiojob.sh &

# file to request, and ab result file
ssh kaustavc@10.5.20.124 sh ~/ab_job.sh $2  $3
kill $(pgrep -f dstat)
