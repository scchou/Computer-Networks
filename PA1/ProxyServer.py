from socket import *
import sys
import threading
from time import gmtime, strftime
import os
import re

print(sys.argv)

if len(sys.argv) <= 1:
    print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server]')
    sys.exit(2)
bind_ip = "localhost"
bind_port = 8839
# Create a server socket, bind it to a port and start listening (localhost)
tcpSerSock = socket(AF_INET, SOCK_STREAM)   # A pair (host, port) is used for the AF_INET address family
# Fill in start.
tcpSerSock.bind((bind_ip, bind_port))
tcpSerSock.listen(1)  # The backlog argument specifies the maximum number of queued connections and should be at least 0
# Fill in end.
print("Listening on %s:%d" % (bind_ip, bind_port))
Cached = {}

while 1:
    # Start receiving data from the client
    print('Ready to serve...')
    tcpCliSock, addr = tcpSerSock.accept()   # The socket must be bound to an address and listening for connections (conn, address)
    print(tcpCliSock, addr)
    print('Received a connection from:', addr)
    message = tcpCliSock.recv(4096)
    print("message=", message)
    if len(message) == 0:
        tcpCliSock.close()
        print("socket closed")

    # Extract the filename from the given message
    print("=========")
    print(message.split()[1].partition("/")[2])
    filename = message.split()[1].partition("/")[2]  # return a 3-tuple : ('', '/', 'url')
    print(filename)
    fileExist = "false"
    filetouse = "/" + filename
    print(filetouse)
    # Check whether the file exist in the cache
    try:
        print("before readlines")
        f = open(filetouse[1:], "r")       # filetouse[1:] is the url
        outputdata = f.readlines()
        fileExist = "true"
        print("File exists!")
        c = socket(AF_INET, SOCK_STREAM)
        filepart = filename.partition('/')   # if filename is espn.com, filepart = ('espn.com','','')
        if 'www.' in filepart[0]:
            hostn = filepart[0].replace("www.","",1)
            host_name = filepart[0]
            local_path = "/"#+ filepart[2]
            print("hostn = ",hostn," local_path = ",local_path)
        else:
            hostn = filepart[0]
            local_path = "/" #+ filename
            print("local_path = ",local_path)
        c.connect((hostn,80))
        print('Socket connected to port 80 of the host')
    
        cached_time = str(strftime("%a, %d %b %Y %H:%M:%S", gmtime()))
        print(cached_time)
        fileobj = c.makefile('r', 0)  #Instead of using send and recv, we can use makefile to send a bunch of commands
        print("=========================== GET & Host in Try ================================")
        print("GET "+local_path + " HTTP/1.0\r\n")
        print("Host: {host}\n\n".format(host=filename))
        print("==============================================================================")
        fileobj.write("GET "+local_path + " HTTP/1.0\r\n")
        # fileobj.write("Content-Type: text/html; charset=utf-8\r\n")
        fileobj.write("Host: {host}\n\n".format(host=filename))
        fileobj.write("If-Modified-Since: " + cached_time + " GMT\r\n")     # Check if the webpage has been modified
        fileobj.write("\n\n")
    
        buff = fileobj.readlines()    
        modified = False
        modified_Date = False
        for line in buff:
            if "304 Not Modified" in line:
                modified = True
            if "Last-Modified" in line:
                modified_Date = True
        if modified or not modified_Date:
            # ProxyServer finds a cache hit and generates a response message
            tcpCliSock.send("HTTP/1.0 200 OK\r\n")
            tcpCliSock.send("Content-Type:text/html\r\n")
            for i in range(len(buff)):
                tcpCliSock.send(buff[i])
                print(buff[i])
            # Fill in end.   
    except IOError:
        if fileExist == "false":
        # Create a socket on the proxyserver
            print("file does not exist")
            c = socket(AF_INET, SOCK_STREAM)
            filenamePart = filename.partition("/")    # (u'www.google.com', u'', u'')
            if not filenamePart[2]:
                print("filenamePart=",filenamePart)
                hostn = filenamePart[0].replace("www.","",1)
                host_name = filenamePart[0]
                local_path = "/" #+ filename
            else:
                local_path = "/" #+ filenamePart[0]
            # if "www." in filenamePart[0]:
            #     hostn = filenamePart[0].replace("www.","")
            #     host_name = filenamePart[0]
            #     local_path = "/"
            # else:
            #     local_path = "/" + filenamePart[0]

            try:
                # Connect to the socket to port 80
                print("hostn=",hostn)
                try:
                    c.connect((hostn,80))
                except:
                    print("stop connecting to port 80")
                    break
                fileobj = c.makefile('r', 0)
                print("=========================================================")
                print("GET {object} HTTP/1.0\r\n".format(object=local_path) + "Host: {host}\n\n".format(host=host_name))
                fileobj.write("GET {object} HTTP/1.0\r\n".format(object=local_path))
                fileobj.write("Host: {host}\n\n".format(host=host_name))
                print("host name is: ",host_name)
                print("local path is: ", local_path)
                print("=========================================================")
                # Read the response into buffer
                buff = fileobj.readlines()
                cached_time = str(strftime("%a, %d %b %Y %H:%M:%S",gmtime()))
                print("cached time =",cached_time)
                Cached[filename] = cached_time      # Cache the time I've link to the page
                # print(Cached)
                tmpFile = open("./"+filename,"wb")  # save buffer
                for line in buff:
                    print(line)
                    tmpFile.write(line)
                    tcpCliSock.send(line)
            except:
                print("Illegal request")
        else:
            tcpCliSock.send("HTTP/1.0 404 sendErrorErrorError\r\n")
            tcpCliSock.send("Content-Type:text/html\r\n")
            tcpCliSock.send("\r\n")
    tcpCliSock.close()
tcpCliSock.close()