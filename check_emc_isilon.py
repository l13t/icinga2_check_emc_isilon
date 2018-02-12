#!/usr/bin/python

import pysnmp
import argparse
import sys
import re

from pysnmp.entity.rfc3413.oneliner import cmdgen

snmp_oids = {
 'clusterHealth' : '1.3.6.1.4.1.12124.1.1.2',
 'clusterName' : '1.3.6.1.4.1.12124.1.1.1',
 'configuredNodes' : '1.3.6.1.4.1.12124.1.1.5',
 'onlineNodes' : '1.3.6.1.4.1.12124.1.1.6',
 'nodeName' : '1.3.6.1.4.1.12124.2.1.1',
 'nodeHealth' : '1.3.6.1.4.1.12124.2.1.2',
 'nodeReadOnly' : '1.3.6.1.4.1.12124.2.1.4',
 'diskBay' : '1.3.6.1.4.1.12124.2.52.1.1',
 'diskDeviceName' : '1.3.6.1.4.1.12124.2.52.1.4',
 'diskStatus' : '1.3.6.1.4.1.12124.2.52.1.5',
 'diskSerialNumber' : '1.3.6.1.4.1.12124.2.52.1.7',
 'diskPerfDeviceName' : '1.3.6.1.4.1.12124.2.2.52.1.2',
 'diskPerfOpsPerSecond' : '1.3.6.1.4.1.12124.2.2.52.1.3',
 'ifsTotalBytes' : '1.3.6.1.4.1.12124.1.3.1',
 'ifsUsedBytes' : '1.3.6.1.4.1.12124.1.3.2',
 'diskBay' : '1.3.6.1.4.1.12124.2.52.1.1',
 'diskDeviceName' : '1.3.6.1.4.1.12124.2.52.1.4',
 'diskStatus' : '1.3.6.1.4.1.12124.2.52.1.5',
 'diskSerialNumber' : '1.3.6.1.4.1.12124.2.52.1.7',
 #'' : '',
}

EXIT_STATUS=0

def check_snmp_access(community, snmp_host):
 res = 0
 cmdGen = cmdgen.CommandGenerator()
 errInd, errSt, errIndex, varBindTable = cmdGen.nextCmd(
  cmdgen.CommunityData(community),
  cmdgen.UdpTransportTarget((snmp_host, 161)),
  snmp_oids['clusterName']
 )
 if errInd:
  print 'CRITICAL: Indication Error' 
  res = 1
 else:
  if errSt:
   print('%s at %s' % (errSt.prettyPrint(), errIndex and varBinds[int(errIndex)] or '?'))
   res = 1
  else:
   res = 0
 return res

def check_multi_snmp(community, snmp_host, oid):
 result = {}
 cmdGen = cmdgen.CommandGenerator()
 errInd, errSt, errIndex, varBindTable = cmdGen.nextCmd(
  cmdgen.CommunityData(community),
  cmdgen.UdpTransportTarget((snmp_host, 161)),
  oid
 )
 if errInd:
  print(errInd)
  return '4'
 else:
  if errSt:
   print('%s at %s' % (
    errorStatus.prettyPrint(),
    errorIndex and varBinds[int(errorIndex)-1] or '?'
   )
  )
  else:
   for varBinds in varBindTable:
    for name,val in varBinds:
     name_num = re.sub(re.compile(oid+"."), '', name.prettyPrint())
     result[name_num] = val
   return result

def check_snmp(community, snmp_host, oid):
 result = ''
 cmdGen = cmdgen.CommandGenerator()
 errInd, errSt, errIndex, varBindTable = cmdGen.nextCmd(
  cmdgen.CommunityData(community),
  cmdgen.UdpTransportTarget((snmp_host, 161)),
  oid
 )
 if errInd:
  print(errInd)
  return '4'
 else:
  if errSt:
   print('%s at %s' % (
    errorStatus.prettyPrint(),
    errorIndex and varBinds[int(errorIndex)-1] or '?'
   )
  )
  else:
   #for varBinds in varBindTable:
   varBinds = varBindTable[0]
   for name,val in varBinds:
    #print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))
    result += val.prettyPrint()
   return result

parent_parser = argparse.ArgumentParser(add_help=True, description='Utility to check EMC Isilon storage status', epilog="Written 2015, Dmytro Prokhorenkov")
parent_parser.add_argument('--host', type=str, help="Enter host ip address or domain name")
parent_parser.add_argument('--comm', type=str, help="SNMP community")
parent_parser.add_argument('--check', type=str, help='''prefered check: 
    check_emc_isilon_clusterhealth,
    check_emc_isilon_nodehealth,
    check_emc_isilon_diskusage,
    check_emc_isilon_diskstatus''')
parent_parser.add_argument('--warn', type=int, help="Exit with WARNING status if less than INTEGER units of disk are free", default=20)
parent_parser.add_argument('--crit', type=int, help="Exit with CRITICAL status if less than PERCENT of disk space is free", default=10)
#parent_parser.add_argument('--help', help="show help message")
#parent_parser.print_help()
_args = vars(parent_parser.parse_args())

if ((_args['host'] == None) or (_args['comm'] == None) or (_args['check'] == None)):
 parent_parser.print_help()
 sys.exit(0)


ipaddr = _args['host']
community = _args['comm']
command = _args['check']

if (command == 'check_emc_isilon_clusterhealth'):
 
 if check_snmp_access(community, ipaddr) != 0:
  sys.exit(2)
 
 ch_status = check_snmp(community, ipaddr, snmp_oids['clusterHealth'])
 cl_name = check_snmp(community, ipaddr, snmp_oids['clusterName'])
 cl_conf_nodes = check_snmp(community, ipaddr, snmp_oids['configuredNodes'])
 cl_online_nodes = check_snmp(community, ipaddr, snmp_oids['onlineNodes'])
 if (ch_status == '0'):
  print "OK: Cluster '" + cl_name + "' status is fine. Online " + cl_online_nodes + " of " + cl_conf_nodes
  EXIT_STATUS=0
 elif (ch_status == '1'):
  print "CRITICAL: Cluster '" + cl_name + "' is in ATTN mode. Online " + cl_online_nodes + " of " + cl_conf_nodes
  EXIT_STATUS=2
 elif (ch_status == '2'):
  print "CRITICAL: Cluster '" + cl_name + "' is DOWN"
  EXIT_STATUS=2
 elif (ch_status == '3'):
  print "CRITICAL: Cluster has some other problems"
  EXIT_STATUS=2
 else:
  print "UNKNOWN: Error with checking cluster"
  EXIT_STATUS=3
 sys.exit(EXIT_STATUS)
elif (command == "check_emc_isilon_nodehealth"):
  
 if check_snmp_access(community, ipaddr) != 0:
  sys.exit(2)
 
 ch_status = check_snmp(community, ipaddr, snmp_oids['nodeHealth'])
 node_name = check_snmp(community, ipaddr, snmp_oids['nodeName'])
 node_ro = check_snmp(community, ipaddr, snmp_oids['nodeReadOnly'])
 if (ch_status == '0'):
  print "OK: Node " + node_name + " is fine."
  EXIT_STATUS=0
 elif (ch_status == '1'):
  print "CRITICAL: Node " + node_name + ". Read-only status " + node_ro
  EXIT_STATUS=2
 elif (ch_status == '2'):
  print "CRITICAL: Node " + node_name + " is DOWN"
  EXIT_STATUS=2
 elif (ch_status == '3'):
  print "CRITICAL: Node " + node_name + " is in INVALID state"
  EXIT_STATUS=2
 else:
  print "UNKNOWN: Error with checking node"
  EXIT_STATUS=3
 sys.exit(EXIT_STATUS)
elif (command == "check_emc_isilon_diskusage"):
   
 if check_snmp_access(community, ipaddr) != 0:
  sys.exit(2)
 
 ch_warn = _args['warn']

 ch_crit = _args['crit']

 totalBytes = int(check_snmp(community, ipaddr, snmp_oids['ifsTotalBytes']))
 usedbytes = int(check_snmp(community, ipaddr, snmp_oids['ifsUsedBytes']))
 usage_per = 100.00 - float(usedbytes / totalBytes) * 100.00
 if (usage_per > ch_warn):
  print "OK: There are " + str(usage_per) + " % of free space on cluster"
  sys.exit(0)
 else:
  if (usage_per > ch_crit):
   print "WARNING: Warning with " + str(usage_per) + " % of free space on cluster"
   sys.exit(1)
  else:
   print "CRITICAL: Critical with " + str(usage_per) + " % of free space on cluster"
   sys.exit(2)
elif (command == 'check_emc_isilon_diskstatus'):
   
 if check_snmp_access(community, ipaddr) != 0:
  sys.exit(2)
 
 diskbay = check_multi_snmp(community, ipaddr, snmp_oids['diskBay'])
 diskdevname = check_multi_snmp(community, ipaddr, snmp_oids['diskDeviceName'])
 diskstat = check_multi_snmp(community, ipaddr, snmp_oids['diskStatus'])
 disksernum = check_multi_snmp(community, ipaddr, snmp_oids['diskSerialNumber'])
 ERROR_CODES = dict()
 for i in diskbay.keys():
  #print diskbay[i]
  #print diskdevname[i]
  #print diskstat[i]
  #print disksernum[i]
  #print '=========='
  if (diskstat[i] != "HEALTHY"):
   ERROR_CODES[diskbay[i]] = "Bay " + str(diskbay[i]) + " | Serianl Num.: " + str(disksernum[i]) + " | Disk status: " + diskstat[i]
 if (ERROR_CODES == {}):
  print "OK: That's all fine with disk health on node"
  sys.exit(0)
 else:
  print "WARNING: There are problems with some drives:"
  for i in ERROR_CODES.keys():
   print ERROR_CODES[i]
   sys.exit(1)
else:
 parent_parser.print_help()
