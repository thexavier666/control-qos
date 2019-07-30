1. Run `tcpdump` for `n_sec` seconds on the required IP,port and interface. The port in our case is the port of the nginx web-server running at 124

	Note : Just capture the HTTP packets

	`sudo tcpdump -G n_sec -W 1 -i eth0 -w some_dump.pcap dst port 32769`

2. Use `tshark` to get only the epoch time and dump it to a csv file

	Note : Remove `-Y http` since we have only captured `http` packets using `tcpdump`

	`tshark -r some_dump.pcap -Y http -T fields -e frame.time_epoch >> some_csv.csv`

3. Get only the last 500 lines/requests of the csv file using `tail`. We need to adjust number of lines sampled.

4. Calculate the delay of those requests

	```
	import csv
	import sys

	def main():
		f_name = sys.argv[1]

		csv_fp = csv.reader(open(f_name, 'r'))

		total_delay = 0
		num_row = 1

		init_row = (float)(csv_fp.__next__()[0])

		for row in csv_fp:

			num_row += 1

			total_delay = (float)(row[0]) - init_row

			init_row = (float)(row[0])

		print(total_delay/num_row)
		print(num_row)

	if __name__ == '__main__':
		main()
	```
