#!/usr/bin/python
# Created and tested on BIG-IP v13.1.0.8 and python 2.6.6
# Author: Jacob Newfield, Enterprise Network Engineer, F5 Networks
# September 3, 2018
# Disclaimer: This program is not officially tested nor supported by F5 Networks. Use this program at your own risk.
# Captures bbrdump, vpn stats, tcpdump (initial and long running) and logs
DEBUG = 0

### Customize these parameters ###
USERNAME = "seymour"
CLIENTIP = "192.168.254.253"
SERVERSIDEIP = "192.168.254.254"
PCAPFILESIZE = 200
NUMPCAPFILES = 20

from os.path import expanduser
import subprocess
import datetime
import os
import errno
import time
import socket
import getpass

# General parameters
HOSTNAME = socket.gethostname().split('.')[0]
now = datetime.datetime.now()
DATE = now.strftime("%Y-%m-%dT%H%M%S%Z%z")
HOMEDIR = expanduser("/var/tmp")
CWD = os.getcwd()
F5GATHERDIR = "%s/f5gather" % HOMEDIR
LOGDIR = "/var/log"

# pause between initial and long running tcpdump
PAUSE = False

# functions
def runcommand( command ):
    executecommand = subprocess.Popen(['%s' % command], shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            )
    executecommand.wait()

def tcpdump( TYPE ):
    "Starts tcpdump capture"
    command = 'tcpdump -s0 -nnn -i any -C %s -W %s host %s or host %s -w %s/%s.%s.%s.%s.server.pcap -vvvv' % (PCAPFILESIZE,
                                                                                        NUMPCAPFILES,
                                                                                        CLIENTIP,
											SERVERSIDEIP,
                                                                                        F5GATHERDIR,
											USERNAME,
                                                                                        HOSTNAME,
											TYPE,
                                                                                        DATE,
											)
	try:
       		 pcap = subprocess.Popen(['%s' % command],
                                shell=True,
                                stdout=subprocess.PIPE,
                                #stderr=subprocess.PIPE,
                                )
	except OSError as e:
        	if e.errno == os.errno.ENOENT:
                	print "The tcpdump command was not found on this device. Install tcpdump and run this program again."
        	else:
                	print "Failed to run tcpdump, errno " + str(e.errno) + ", '" + os.strerror(e.errno) + "'. " + "Fix tcpdump and run this program again."

def killtcpdump( TYPE ):
	"Kill the running tcpdump command(s)"
	command = "for pid in $(ps axc|awk '{if ($5==\"tcpdump\") print $1}'); do kill -9 $pid; done;"
	killdump = subprocess.Popen(['%s' % command],
        					shell=True,
        					#stdout=subprocess.PIPE,
        					#stderr=subprocess.PIPE,
        					)
	killdump.wait()
	print "%s tcpdump has stopped" % TYPE
	time.sleep(0.5)

# Make folders
makefolders = subprocess.Popen('mkdir -p %s' % F5GATHERDIR, shell=True)
makefolders.wait()

# Clear previous captures
removeprevioustgzfiles = 'if ls %s/*.tgz; then rm -f %s/*.tgz; fi' % (F5GATHERDIR, F5GATHERDIR)
runcommand( removeprevioustgzfiles )
removepreviousqkviews = 'if ls %s/*.qkview; then rm -f %s/*.qkview; fi' % (F5GATHERDIR, F5GATHERDIR)
runcommand( removepreviousqkviews )
removepcaps = 'if ls %s/*.pcap*; then rm -f %s/*.pcap*; fi' % (F5GATHERDIR, F5GATHERDIR)
runcommand( removepcaps )
removebbrdump = 'if ls %s/*.bbrdump; then rm -f %s/*.bbrdump; fi' % (F5GATHERDIR, F5GATHERDIR)
runcommand( removebbrdump )
removekeysfile= 'if ls %s/*.keys; then rm -f %s/*.keys; fi' % (F5GATHERDIR, F5GATHERDIR)
runcommand( removekeysfile )
removetmstatsfile = 'if ls %s/*.errors; then rm -f %s/*.errors; fi' % (F5GATHERDIR, F5GATHERDIR)
runcommand( removetmstatsfile )

# Before tmctl vpn stats
vpnstatsbefore = 'tmctl -d blade -w 200 tmm/ppp/errors -P > %s/%s.%s.%s.tmctl-ppp-before.errors' % (F5GATHERDIR, USERNAME, HOSTNAME, DATE)
runcommand( vpnstatsbefore )

# Start bbrdump
bbrdump = subprocess.Popen('bbrdump -a %s > %s/%s.%s.%s.bbrdump' % (CLIENTIP, F5GATHERDIR, USERNAME, HOSTNAME, DATE), shell=True)
print "bbrdump is running"

# Start INITIAL tcpdump
if DEBUG:
	PCAPFILESIZE = "2"
	NUMPCAPFILES = "3"

tcpdump("INITIAL")
response = raw_input("The INITIAL tcpdump is running \nPress Enter to Stop...\n")
killtcpdump("INITIAL")
if PAUSE:
	response = raw_input("Press Enter to start the LONG RUNNING tcpdump...")
# Start LONG RUNNING tcpdump
tcpdump("LONGRUNNING")
response = raw_input("LONG RUNNING tcpdump started\nPress Enter to stop LONG RUNNING tcpdump...\n")
killtcpdump("LONG RUNNING")

# Stop bbrdump
killbbrdump = "for pid in $(ps axc|awk '{if ($5==\"bbrdump\") print $1}'); do sudo kill -9 $pid; done;"
runcommand( killbbrdump )
print "bbrdump has stopped"

# After tmctl vpn stats 
vpnstatsafter = 'tmctl -d blade -w 200 tmm/ppp/errors -P > %s/%s.%s.%s.tmctl-ppp-after.errors' % (F5GATHERDIR, USERNAME, HOSTNAME, DATE)
runcommand( vpnstatsafter )

# Get keys
grepkeys = "grep Session-ID /var/log/ltm | sed 's/.*(RSA.*)/\1/' > %s/%s.%s.%s.keys" % (F5GATHERDIR, USERNAME, HOSTNAME, DATE)
runcommand( grepkeys )

# Compress logs
print "Compressing logs..."
removelogs = '[ -e %s/*.server.logs.tgz ] && rm -f %s/*.server.logs.tgz' % (F5GATHERDIR, F5GATHERDIR) 
runcommand( removelogs )

compresslogs = 'tar -czf %s/%s.%s.%s.server.logs.tgz %s' % (F5GATHERDIR, USERNAME, HOSTNAME, DATE, LOGDIR)
runcommand( removelogs )

# Generate qkview
print "Generating qkview. This may take a few minutes..."
qkview = 'qkview -s0 -f %s/%s.%s.%s.tar.qkview' % (F5GATHERDIR, USERNAME, HOSTNAME, DATE)
runcommand( qkview )

# Gather the files
print "Gathering files..."
tarcapturefiles = 'cd %s && tar -czf f5gather.%s.%s.%s.server.tgz *.server.pcap* *.bbrdump *.errors *.keys && cd %s' % (F5GATHERDIR, USERNAME, HOSTNAME, DATE, CWD)
runcommand( tarcapturefiles)

tarlogfiles = 'tar -czf %s/%s.%s.%s.server.logs.tgz %s' % (F5GATHERDIR, USERNAME, HOSTNAME, DATE, LOGDIR)
runcommand( tarlogfiles )
if DEBUG == 2:
	print "Gather command to run:\n%s && %s" % (tarcapturefiles, tarlogfiles)

# Clean up
cleanup = 'cd %s && rm -f *.server.pcap* *.bbrdump *.errors *.keys cd %s' % (F5GATHERDIR, CWD)
runcommand( cleanup )

# Complete
print "Done\nCompressed logs, tcpdumps, bbrdump and vpn error stats are found under %s/:" % F5GATHERDIR
subprocess.call(['ls -llh %s | awk \'{if ($5 ~ /[[:digit:]]/) {size=$5} else {size=$6}; if ($1 != "total") print "  |--"$NF"  "size}\'' % F5GATHERDIR ], shell=True)
