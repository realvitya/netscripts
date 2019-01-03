#!/usr/bin/env python

#
# This script is intended to generate interface ranges from individual interface list.
# Written by Viktor Kertesz <vkertesz2@gmail.com>
# Version 1.0
# Example: Gi1/0/1, Gi1/0/2, Gi1/0/3 = Gi1/0/1-3
# Different type of interfaces or ports are supported (maximum 4 parts: Gi101/1/0/1)
# You may copy interfaces from any text, script recognize interfaces.
# e.g. copy from show vlan brief output
#
# Input is read on standard input or by specifying file
# int2range [options] [interfacefile]
# Options:
# -p "{prefix}"    : Write prefix instead of "interface range" (empty is "")
# Empty inputfile means read from standard input

import os
import sys
import re
import string

#from operator import itemgetter
#for backward compatibility:
def itemgetter(*items):
    if len(items) == 1:
        item = items[0]
        def g(obj):
            return obj[item]
    else:
        def g(obj):
            return tuple(obj[item] for item in items)
    return g

def to_port(port):
    output=port[0]
    if port[1]>=0:
        output+=str(port[1])
        if port[2]>=0:
            output+="/"+str(port[2])
            if port[3]>=0:
                output+="/"+str(port[3])
                if port[4]>=0:
                    output+="/"+str(port[4])
    return output

def int2range(ports_in=[], prefix = "interface range "):
        ports = []
        port_regex=re.compile(r"(?i)([a-z]+)([0-9]+)(?:/([0-9]+))?(?:/([0-9]+))?(?:/([0-9]+))?")
	output = []
	outline = ""

        if ports_in == []:
            return output
        for line in ports_in:
               matches = port_regex.findall(line)
               for match in matches:
                   iface=match[0]
                   if len(match[1])>0:
                       port1=int(match[1])
                   else:
                       port1=-1
                   if len(match[2])>0:
                       port2=int(match[2])
                   else:
                       port2=-1
                   if len(match[3])>0:
                       port3=int(match[3])
                   else:
                       port3=-1
                   if len(match[4])>0:
                       port4=int(match[4])
                   else:
                       port4=-1

                   ports.append((iface,port1,port2,port3,port4))

        ports=sorted(ports, key=itemgetter(0,1,2,3,4)) # Sort interfaces
        rangestart=ports[0] # contains interface rangestart (Gi0/0)
        rangeindex=1 # counts number of ranges on line (gi0/0-1,g0/3-5 = 2)
        currentport=rangestart
        lastportindex = 1
	outline="%s%s" % (prefix,to_port(rangestart))
        i = 0 # range counter
        portindex = 0
        for port in ports[1:]:
            
            # interface name
            if rangestart[0] != port[0]:
                if i > 0: # it's a range
                    outline += "-%d" % currentport[lastportindex]
                    i = 0 # reset range counter
                if rangeindex >= 5:
                    rangeindex = 1
                    output.append(outline)
                    outline = "%s%s" % (prefix,to_port(port))
                else:
                    rangeindex += 1
                    outline += ", %s" % to_port(port)
                rangestart=port
                currentport=port
                continue # move ahead for next port


            # interface numbers
            for portindex in range(1,5):
                if currentport[portindex] == port[portindex]:
                    pass
                elif port[portindex] == (currentport[portindex] + 1) and portindex == 4:
                    i += 1
                    currentport = port
                    lastportindex = portindex
                    break
                elif port[portindex] == (currentport[portindex] + 1) and port[portindex+1] < 0: # portindex < 4
                    # check if we found the last sane index
                    i += 1
                    currentport = port
                    lastportindex = portindex
                    break
                else:
                    if i > 0: # it's a range
                        outline += "-%d" % currentport[lastportindex]
                        i = 0 # reset range counter
                    if rangeindex >= 5:
                        rangeindex = 1
                        output.append(outline)
                        outline = "%s%s" % (prefix,to_port(port))
                    else:
                        rangeindex += 1
                        outline += ", %s" % to_port(port)
                    rangestart=port
                    currentport=port
                    break # move ahead for next port

        if i > 0:
            outline += "-%d" % currentport[lastportindex]
        output.append(outline)
        return output

def main():
    	lines = []
        prefix = "interface range "
        try:
            if len(sys.argv)>1:
                if sys.argv[1] == "-p":
                    del sys.argv[1]
                    prefix = sys.argv[1]
		    del sys.argv[1]
	    if len(sys.argv)>1:
		if sys.argv[1] == "-h" or sys.argv[1] == "--help":
		    print "Help:"
            	    print "int2range [-p {prefix}] [inputfile]"
		    print
            	    print "Empty inputfile means read from standard input"
            	    print "If prefix is omitted, cisco standard will be used (interface range )"
		    return 1
            if len(sys.argv)>1:
                f=open(sys.argv[1],"r")
            else:
		print "Hit ENTER and CTRL-D to indicate end of input!"
                f=sys.stdin
        except:
            print "Error opening %s" % input
            raise

	#  Read file/stdin
        while True:
            line = f.readline()
            if not line:
                break
            lines.append(line)

        f.close()

	for range in int2range(prefix=prefix,ports_in=lines):
	    print range
	return

if __name__ == "__main__":
        main()
