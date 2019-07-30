def migration_arrival(bw_list, bw_arrival):

	total_bw = sum(bw_list)

	bw_total = 0
	
	for i in range(len(bw_list)):
		bw_new = (bw_list[i]/total_bw) * bw_arrival
		bw_list[i] -= bw_new

		bw_total += bw_new

	return bw_list, bw_total

def migration_departure(bw_list, bw_depart):

	total_bw = sum(bw_list)

	total_bw_inv = 0

	for i in range(len(bw_list)):
		total_bw_inv += (total_bw/bw_list[i])

	for i in range(len(bw_list)):
		bw_get = ((total_bw/bw_list[i])/total_bw_inv) * bw_depart

		bw_list[i] += bw_get


	return bw_list

def main():
	x = [10,40,30,20]
	y = 15

	print(x)
	print(y)

	print("bw of all containers after a new container arrives")

	print(migration_arrival(x,y))

	x = [10,40,30,20]
	y = 15

	print("bw of all containers after a container leaves")

	print(migration_departure(x,y))

main()	
