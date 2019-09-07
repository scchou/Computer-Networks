from socket import *
from utils import *
import time, struct, sys, random
import os
import math

import os
import errno
from collections import OrderedDict 

addr, port = '127.0.0.1', 6000
file_name = sys.argv[1]

#create UDP socket to receive file on
local_socket = socket(AF_INET, SOCK_DGRAM)
count = 0
filesize = os.path.getsize(file_name)
# print(filesize)   # byte
packets = int(math.ceil(filesize/float(DATA_LENGTH)))
# print("packets=",int(packets))
local_socket.setblocking(0)
pkt_dict=dict()

for count, value in enumerate(read_file(file_name, chunk_size=DATA_LENGTH)):
	pkt_dict[count] = value

curr = 0 # sequence number of packet
ack_seqnum = 0

base = 0

ack_dict = {}
ack_seqnum = 0
all_recevied = False
starttime_table = OrderedDict()
elapsedtime_table = OrderedDict()

while curr < packets or all_recevied == False:

	if curr - base < WND_SIZE and curr != packets :  # send packets if packets are in the window
		if packets <= 1:
			flag = SPECIAL_OPCODE
		else:
			if curr == 0:
				flag = START_OPCODE
			elif curr == packets-1:
				flag = END_OPCODE
			else:
				flag = DATA_OPCODE
		# print("curr =",curr, "base =", base , "curr - base = ", curr-base)
		pkt = make_packet(curr,pkt_dict[curr],flag)   			# checksum included
		# print("packet sent",curr)
		local_socket.sendto(pkt,(addr,port))
		starttime_table[curr] = time.clock()
		curr += 1

# Receive ACK
	try:
		# while True:
		msg, address = local_socket.recvfrom(MAX_SIZE)
		ack_csum, ack_rsum, ack_seqnum, ack_flag, ack_data = extract_packet(msg)
		# print("ack_seqnum=",ack_seqnum, "flag=",flag)
		elapsedtime_table = {}
		starttime_table = {ack_seqnum-1:time.clock()}

		# if elapsedtime_table.get(ack_seqnum-1,None):
		# 	# print("before pop ack_seqsum-1:", ack_seqnum-1)
		# 	for i in elapsedtime_table.keys():
		# 		if i <= ack_seqnum -1:
		# 			elapsedtime_table.pop(i)
		# 			starttime_table.pop(i)

		if ack_dict.get(ack_seqnum):
			ack_dict[ack_seqnum] += 1
		else:
			ack_dict[ack_seqnum] = 1

		base = ack_seqnum

		if ack_dict[ack_seqnum] >= 3:     # handle 3 duplicates
			curr = base 				  # retransmit from window base
			ack_dict[ack_seqnum] = 0
		# print("ack_dict=",ack_dict)
		if ack_dict.get(packets,None) == 1:
			all_recevied = True
			break

	except error, e:
		err = e.args[0]
		if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
			time.sleep(0.1)
			# print 'No ACK data available'
			curr_time = time.clock()
			elapsedtime_table = {i:(curr_time-starttime_table[i]) for i in starttime_table.keys()}
			# print("elapsed time =",elapsedtime_table)
			if list(elapsedtime_table.items())[0][1] > TIMEOUT:
				elapsedtime_table = {}
				starttime_table = {}
				# print("Timeout happens")
				if ack_seqnum == 0:
					curr = 0
				else:
					# print("ack_seqnum = ", ack_seqnum)
					curr = ack_seqnum
				# elapsed_table = {}
				# starttime_table = {}
			continue
		else:
			# a "real" error occurred
			print e
			sys.exit(1)
# print(ack_dict)




