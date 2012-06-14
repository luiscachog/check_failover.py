#!/usr/bin/env python



__author__ = "Luis Alberto Cacho"
__copyright__ = "Copyright 2012, CookieLabs"
__credits__ = ["Luis Alberto Cacho"]
__license__ = "GPL"
__maintainer__ = "Luis Alberto Cacho"
__email__ = "lcacho@cookielabs.net"
__status__ = "Production"
__version__ = "1.0.1"
__date__ = "01/06/2012"

"""

FILE		: check_failover.py
USAGE		: ./check_failover.py
DESCRIPTION	: Nagios plugin to check status for each of the Red Hat cluster services.

OPTION(S)	: -i / --init & -v / --version & -h / --help
REQUIREMENTS	: RedHat cluster. Tested with clustat 2.0.52
BUGS		: Search for XXX in the script.
AUTHOR(s)	: Luis Alberto Cacho (lcacho@cookielabs.net)
COMPANY		: CookieLabs
VERSION		: 1.0.1
CREATED		: 01/06/2012

"""

import os, re, sys, getopt, string, pickle, socket

#====================#
# Nagios exit status #
#====================#
STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3
STATE_DEPENDENT = 4

#=================##
# Global variables #
#=================##
VERSION = "1.0.1"
DATA_FILE = '/usr/local/nagios/var/failover'
FAILOVER_COUNT_FILE = ''
STATUS_COUNT_FILE = ''
LOGGER='/usr/bin/logger -t check_failover '
CLUSTAT = '/usr/sbin/clustat'
UNAME = 'uname -n'
IP_ROUTE = 'ip route list |  grep default | awk \'{print $3}\''
TIMES_REPEAT = 10
STATUS = 0
MESSAGE =" "
MSG=" "

#===========#
# Functions #
#===========#
def usage():
	print 'check_failover.py version %s' % (VERSION)
	print 'This is a Nagios check to see if each of Red Hat cluster services has moved to another node.'
	print '''
Copyright (C) 2012  Cookielabs www.cookielabs.net

Usage : check_failover.py

Options: -i / --init	-- Initialize for first run or use to re-initialize.
	 -h / --help	-- Displays this help message.
	 -v / --version	-- Displays version.
'''
	sys.exit(STATE_OK)


def get_data():
	pipe = os.popen(CLUSTAT)
	output = pipe.readlines()
	exit_status = pipe.close()

	# Next 2 lines is cutting out everything above the dashed lines.
	LOCATION = output.index(' ------- ----                   ----- ------                   -----         \n')
	TAIL = output[LOCATION + 1:]

	# As I don't know any better, the following 3 lines takes :
	# ['  SERVICE                  NODE-NAME                       STATUS         \n']
	# and makes it:
	# ['SERVICE', 'NODE-NAME', 'STATUS']
	TAIL = str(TAIL)
	TAIL = TAIL.split()
	TAIL = TAIL[1:-1]

	COUNTER = 0
	DATA=[]

	# I only want the 3 columns of clustat output (under Service Name).
	while COUNTER < len(TAIL):
		DATA.append(TAIL[COUNTER])
		COUNTER = COUNTER + 1
		DATA.append(TAIL[COUNTER])
		COUNTER = COUNTER + 1
		DATA.append(TAIL[COUNTER])
		COUNTER = COUNTER + 3
	return DATA


def initialize():
	print 'Initializing now ...'
	try:
		INIT_FILE = open(DATA_FILE, 'w')
	except IOError:
		print 'Unable to write to file.  Make sure the Nagios user can read/write to %s.' % (DATA_FILE)
		sys.exit(STATE_CRITICAL)
	DATA = get_data()
	pickle.dump(DATA, INIT_FILE)
	INIT_FILE.close()
	os.popen("echo 0 > "+FAILOVER_COUNT_FILE+" ")
	MESSAGE = 'Initialization completed OK'
	print MESSAGE
	os.popen(LOGGER+MESSAGE)
	send_sms(MESSAGE)
	sys.exit(STATE_OK)

def initialize_status_file():
	os.popen("echo 0 > "+STATUS_COUNT_FILE+" ")

def converttoStr(s):
	try:
		ret = int(s)
	except ValueError:
		ret = float(s)
	return ret

def conteo(COUNT_FILE):
	try:
		f = open (COUNT_FILE, "r")
	except IOError:
                print 'Unable to write to file.  Make sure the Nagios user can read/write to %s.' % (COUNT_FILE)
                sys.exit(STATE_CRITICAL)
	
	file_number = f.read()
	
	number_int = converttoStr(file_number)
	number_int = number_int + 1

	STR = "echo "+str(number_int)+" > "+COUNT_FILE+" "

	os.popen(STR)
	f.close()

	return number_int

def get_Hostname():
	hostname = socket.gethostname()
	return hostname

def get_IPAddr():
	ip = socket.gethostbyaddr(socket.gethostname())
	ip = str(ip[2])
	ip = ip[2:-2]

	return ip

#======#
# Main #
#======#

#===========================#
# Check options / arguments #
#===========================#
try:
	options, argument = getopt.getopt(sys.argv[1:],'ihv', ["init", "help", "version"])
except getopt.error:
	usage()

for a in options[:]:
	if a[0] == '-i' or a[0] == '--init':
		initialize()
for a in options[:]:
	if a[0] == '-h' or a[0] == '--help':
		usage()
for a in options[:]:
	if a[0] == '-v' or a[0] == '--version':
		print 'check_failover.py version %s' % (VERSION)
		sys.exit(STATE_OK)

if len(argument) != 0:
	print "Incorrect amount of arguments."
	print "See 'check_failover.py -h' for more details"
	sys.exit(STATE_CRITICAL)

if DATA_FILE == '':
	print 'First set "DATA_FILE" variable in script.  Make sure the Nagios user can read/write to it.'
	sys.exit(STATE_CRITICAL)

if os.path.exists(DATA_FILE) != 1:
	print 'Could not find data file.'
	print 'Make sure the Nagios user can read/write to %s and that you have initialized with -i / --init' % (DATA_FILE)
	sys.exit(STATE_CRITICAL)

if os.path.exists(FAILOVER_COUNT_FILE) != 1:
        print 'Could not find data file.'
        print 'Make sure the Nagios user can read/write to %s and that you have initialized with -i / --init' % (FAILOVER_COUNT_FILE)
        sys.exit(STATE_CRITICAL)

if os.path.exists(STATUS_COUNT_FILE) != 1:
        print 'Could not find data file.'
        print 'Make sure the Nagios user can read/write to %s and that you have initialized with -i / --init' % (STATUS_COUNT_FILE)
        sys.exit(STATE_CRITICAL)


#==================================#
# Get old and new data and compare #
#==================================#
CURRENT_DATA = get_data()
INIT_FILE = open(DATA_FILE, 'r') # Should add exception here ...
OLD_DATA = pickle.load(INIT_FILE)

M = []
DICT_CURRENT = {}
DICT_OLD = {}


HOSTNAME = get_Hostname()
IP_Addr= get_IPAddr()

for k in range(0, len(CURRENT_DATA), 3):
	DICT_CURRENT[CURRENT_DATA[k]] = CURRENT_DATA[k+1]
	DICT_OLD[OLD_DATA[k]] = OLD_DATA[k+1]

	if CURRENT_DATA[k+2] == 'started':
		if DICT_CURRENT[CURRENT_DATA[k]] == DICT_OLD[OLD_DATA[k]]:
			MESSAGE = "OK - Service: "+CURRENT_DATA[k]+" its in Node: "+DICT_CURRENT[CURRENT_DATA[k]]+" "
			STATUS = STATE_OK
		else:
			MESSAGE = "CRITICAL - Service: "+CURRENT_DATA[k]+"  its migrated to Node: "+DICT_CURRENT[CURRENT_DATA[k]]+". Check Server:  IP="+IP_A
ddr+" Hostname="+HOSTNAME+""
if conteo(FAILOVER_COUNT_FILE) > TIMES_REPEAT:
	initialize()
	STATUS = STATE_CRITICAL
else:
	MESSAGE = "CRITICAL - Service: "+CURRENT_DATA[k]+" its "+CURRENT_DATA[k+2]+". Check Server: IP="+IP_Addr+" Hostname="+HOSTNAME+""
	STATUS = STATE_CRITICAL

	M.append(MESSAGE)
	STATUS = STATUS + STATUS
	MESSAGE = ', '.join(map(str,M))

if STATUS == 0:
        print MESSAGE
        os.popen(LOGGER+MESSAGE)
	sys.exit(STATE_OK)
else:
        print MESSAGE
        os.popen(LOGGER+MESSAGE)
	sys.exit(STATE_CRITICAL)


