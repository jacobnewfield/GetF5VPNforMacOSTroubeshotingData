#!/usr/bin/python
# Created and tested on MacOS 10.13.5 and python 2.7.10
# Author: Jacob Newfield, Enterprise Network Engineer, F5 Networks
# August 25th, 2018
# Disclaimer: This program is not officially tested nor supported by F5 Networks. Use this program at your own risk.
# Sets vpn debug log level; moves existing log files to archive folder; starts tcpdump
DEBUG = 0

### Customize these parameters ###
USERNAME = "seymour"
SERVERIP = "192.168.254.254"
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
HOMEDIR = expanduser("~")
CWD = os.getcwd()
F5GATHERDIR = "%s/Desktop/f5gather" % HOMEDIR
F5LOGDIR = "%s/Library/Logs/F5Networks" % HOMEDIR

# pause between initial and long running tcpdump
PAUSE = False

# Confirm password works
FAIL = True
print "Enter your password"
for x in range(3):
	PASSWORD = getpass.getpass()
	checkpass = subprocess.check_output('sudo -k && echo \'%s\' | sudo -S ls 2>&1 | awk \'{if ($3 ~ /incorrect/) print $3}\'' % PASSWORD, shell=True).strip()
	if checkpass == "incorrect":
		print "Password incorrect"
	else:
		FAIL = False
		break
if FAIL:
	print "Password incorrect\nPassword attempts exceeded\nCheck your password and try again later"
	quit(1)


# functions
def runcommand ( command ):
	executecommand = subprocess.Popen(['%s' % command], shell=True,
							stdout=subprocess.PIPE,
							stderr=subprocess.PIPE,
							)
	executecommand.wait()

def tcpdump( TYPE ):
	"Starts tcpdump capture"
	command = 'tcpdump -s0 -nnn -i any -C %s -W %s host %s -w %s/%s.%s.%s.%s.client.pcap -vvvv' % (PCAPFILESIZE,
                                                                                        NUMPCAPFILES,
                                                                                        SERVERIP,
																						F5GATHERDIR,
																						USERNAME,
                                                                                        HOSTNAME,
																						DATE,
																						TYPE,
																						)
	try:
       		 pcap = subprocess.Popen(['echo %s | sudo -S %s' % (PASSWORD, command)],
                                shell=True,
                                stdout=subprocess.PIPE,
                                #stderr=subprocess.PIPE,
                                )
	except OSError as e:
        	if e.errno == os.errno.ENOENT:
                	#print os.strerror(e.errno)
                	print "The tcpdump command was not found on this device. Install tcpdump and run this program again."
        	else:
                	print "Failed to run tcpdump, errno " + str(e.errno) + ", '" + os.strerror(e.errno) + "'. " + "Fix tcpdump and run this program again."
	time.sleep(0.75)

def killtcpdump( TYPE ):
	"Kill the running tcpdump command(s)"
	command = "echo '%s' | sudo -S printf 'Stopping %s tcpdump...\n' && for pid in $(ps axc|awk '{if ($5==\"tcpdump\") print $1}'); do sudo kill -9 $pid; done;" % (PASSWORD, TYPE)
	killdump = subprocess.Popen(['%s' % command],
        					shell=True,
        					#stdout=subprocess.PIPE,
        					#stderr=subprocess.PIPE,
        					)
	killdump.wait()
	print "%s tcpdump has stopped\n" % TYPE
	time.sleep(0.5)

# Make folders
subprocess.call('mkdir -p %s' % F5GATHERDIR, shell=True)
subprocess.call('mkdir -p %s' % F5LOGDIR, shell=True)
time.sleep(0.5)

# Clear previous logs and tcpdumps
removeprevioustgzfiles = 'if ls %s/*.tgz; then rm -f %s/*.tgz; fi' % (F5GATHERDIR, F5GATHERDIR)
runcommand( removeprevioustgzfiles )

removepreviouspcaps = 'if ls %s/*.client.pcap*; then rm -f %s/*.client.pcap*; fi' % (F5GATHERDIR, F5GATHERDIR)
runcommand( removepreviouspcaps )

removeprevioussyslogsfiles = 'if ls %s/*.client.syslogs; then rm -f %s/*.client.syslogs; fi' % (F5GATHERDIR, F5GATHERDIR)
runcommand( removeprevioussyslogsfiles )

removepreviousf5logs = 'if ls %s/*.log; then rm -f %s/*.log; fi' % (F5LOGDIR, F5LOGDIR)
runcommand( removepreviousf5logs )

# Set vpn debug logging
text = """##########################################################################
# This file contain F5Networks client components settings
#
#
# BASIC     31   Value use to provide basic logs which include user friendly messages, warnings, and errors.
#                Valid values are in the range 0 to 31, the highest setting is 31.
# EXTENDED  63   Set to provide extended log level.
#                Valid values are in the range of 32 to 63, the highest setting is 63.
##########################################################################



# default log level for all f5 components
default_log_level=63



# svpn core log level. This setting is used to override the default log level set by default_log_level setting for svpn component
#svpn_log_level=63



# svpn NPAPI plugin log level. This setting is used to override the default log level set by default_log_level setting for svpn NPAPI plugin
#svpn_plugin_log_level=63



# endpoint secutity NPAPI plugin. This setting is used to override the default log level set by default_log_level setting for endpoint secutity NPAPI plugin
#eps_plugin_log_level=63



# EdgeClient. This setting is used to override the default log level set by default_log_level setting for EdegClient application
#edge_client_log_level=63
"""

# Start tcpdump
if DEBUG:
	PCAPFILESIZE = "2"
	NUMPCAPFILES = "3"

tcpdump("INITIAL")
response = raw_input("The INITIAL tcpdump is running \nPress Enter to Stop...\n")
killtcpdump("INITIAL")
if PAUSE:
	response = raw_input("Press Enter to start the LONG RUNNING tcpdump...")
tcpdump("LONGRUNNING")
repsponse = raw_input("LONG RUNNING tcpdump started\nPress Enter to stop...\n")
killtcpdump("LONG RUNNING")

# Get client syslogs
print "\nGathering MacOS system logs..."
getsyslogs = 'log show --style syslog --debug -last 1d > %s/%s.%s.%s.client.syslogs' % (F5GATHERDIR, USERNAME, HOSTNAME, DATE)
runcommand( getsyslogs )

# Gather files
print "Gathering and compressing all files..."
tartcpdumps = 'cd %s && if ls *.client.pcap*; then tar czf %s.%s.%s.client.tcpdumps.tgz *.client.pcap*; fi && cd %s' % (F5GATHERDIR, USERNAME, HOSTNAME, DATE, CWD)
runcommand( tartcpdumps )
tarf5logs = 'cd %s/Library/Logs/F5Networks && tar czf %s/%s.%s.%s.client.f5logs.tgz *.log && cd %s' % (HOMEDIR, F5GATHERDIR, USERNAME, HOSTNAME, DATE, CWD)
runcommand( tarf5logs )
tarsyslogsfile = 'cd %s && if ls *.client.syslogs; then tar czf %s.%s.%s.client.syslogs.tgz *.client.syslogs; fi && cd %s' % (F5GATHERDIR, USERNAME, HOSTNAME, DATE, CWD)
runcommand( tarsyslogsfile )
if DEBUG == 2:
	print "Gather command to run:\n   Command1: %s\n   Command2: %s\n   Command3: %s\n" % (tartcpdumps, tarf5logs, tarsyslogsfile)

# Clean up
removepcaps = 'if ls %s/*.client.pcap*; then rm -f %s/*.client.pcap*; fi' % (F5GATHERDIR, F5GATHERDIR)
runcommand( removepcaps )
removesyslogsfile = 'if ls %s/*.client.syslogs; then rm -f %s/*.client.syslogs; fi' % (F5GATHERDIR, F5GATHERDIR)
runcommand( removesyslogsfile ) 

# Complete
#time.sleep(0.5)
print "\nCompressed tcpdumps, syslogs and f5logs are found under %s/:" % F5GATHERDIR
subprocess.call(['ls -llh %s | awk \'{ if ($5 ~ /[[:digit:]]/) { size=$5 } else { size=$6 }; if ($1 != "total") print "  |--"$NF"  "size}\'' % F5GATHERDIR ], shell=True)
