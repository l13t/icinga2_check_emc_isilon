#!/usr/bin/env python3

import argparse
import re
import sys

from pysnmp.entity.rfc3413.oneliner import cmdgen

__author__ = 'Dmytro Prokhorenkov'
__version__ = 1.1

snmp_oids = {
    'clusterHealth': '1.3.6.1.4.1.12124.1.1.2',
    'clusterName': '1.3.6.1.4.1.12124.1.1.1',
    'configuredNodes': '1.3.6.1.4.1.12124.1.1.5',
    'diskBay': '1.3.6.1.4.1.12124.2.52.1.1',
    'diskDeviceName': '1.3.6.1.4.1.12124.2.52.1.4',
    'diskPerfDeviceName': '1.3.6.1.4.1.12124.2.2.52.1.2',
    'diskPerfOpsPerSecond': '1.3.6.1.4.1.12124.2.2.52.1.3',
    'diskSerialNumber': '1.3.6.1.4.1.12124.2.52.1.7',
    'diskStatus': '1.3.6.1.4.1.12124.2.52.1.5',
    'ifsTotalBytes': '1.3.6.1.4.1.12124.1.3.1',
    'ifsUsedBytes': '1.3.6.1.4.1.12124.1.3.2',
    'nodeHealth': '1.3.6.1.4.1.12124.2.1.2',
    'nodeName': '1.3.6.1.4.1.12124.2.1.1',
    'nodeReadOnly': '1.3.6.1.4.1.12124.2.1.4',
    'onlineNodes': '1.3.6.1.4.1.12124.1.1.6',
}

EXIT_STATUS = 0


def check_snmp_access(community, snmp_host):
    res = 0
    cmdGen = cmdgen.CommandGenerator()
    errInd, errSt, errIndex, varBindTable = cmdGen.nextCmd(
        cmdgen.CommunityData(community),
        cmdgen.UdpTransportTarget((snmp_host, 161)),
        snmp_oids['clusterName'],
        lookupMib=False
    )
    if errInd:
        print('UNKNOWN: Indication Error')
        res = 1
    else:
        if errSt:
            print('%s at %s' % (errSt.prettyPrint(),
                                errIndex and varBindTable[int(errIndex)] or '?'))
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
        oid,
        lookupMib=False
    )
    if errInd:
        print(errInd)
        return '4'
    else:
        if errSt:
            print('%s at %s' % (
                errSt.prettyPrint(),
                errIndex and varBindTable[int(errIndex)-1] or '?'
            )
            )
        else:
            for varBinds in varBindTable:
                for name, val in varBinds:
                    name_num = re.sub(re.compile(oid+"."), '', name.prettyPrint())
                    result[name_num] = val
            return result


def check_snmp(community, snmp_host, oid):
    result = ''
    cmdGen = cmdgen.CommandGenerator()
    errInd, errSt, errIndex, varBindTable = cmdGen.nextCmd(
        cmdgen.CommunityData(community),
        cmdgen.UdpTransportTarget((snmp_host, 161)),
        oid,
        lookupMib=False
    )
    if errInd:
        print(errInd)
        return '4'
    else:
        if errSt:
            print('%s at %s' % (
                errSt.prettyPrint(),
                errIndex and varBindTable[int(errIndex)-1] or '?'
            )
            )
        else:
            # for varBinds in varBindTable:
            varBinds = varBindTable[0]
            for name, val in varBinds:
                # print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))
                result += val.prettyPrint()
            return result


parent_parser = argparse.ArgumentParser(add_help=True,
                                        description='Utility to check EMC Isilon storage status',
                                        epilog='{0}: v.{1} by {2}'.format('check_oom.py', __version__, __author__))
parent_parser.add_argument('--host', type=str, help="Enter host ip address or domain name")
parent_parser.add_argument('--comm', type=str, help="SNMP community")
parent_parser.add_argument('--check', type=str, help='''prefered check:
    check_emc_isilon_clusterhealth,
    check_emc_isilon_nodehealth,
    check_emc_isilon_diskusage,
    check_emc_isilon_diskstatus''')
parent_parser.add_argument('--warn', type=int,
                           help="Exit with WARNING status if less than INTEGER units of disk are free",
                           default=20)
parent_parser.add_argument('--crit', type=int,
                           help="Exit with CRITICAL status if less than PERCENT of disk space is free",
                           default=10)
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
        print("OK: Cluster '" + cl_name + "' status is fine. Online " + cl_online_nodes + " of " + cl_conf_nodes)
        EXIT_STATUS = 0
    elif (ch_status == '1'):
        print("CRITICAL: Cluster '" + cl_name + "' is in ATTN mode. Online " + cl_online_nodes + " of " + cl_conf_nodes)
        EXIT_STATUS = 2
    elif (ch_status == '2'):
        print("CRITICAL: Cluster '" + cl_name + "' is DOWN")
        EXIT_STATUS = 2
    elif (ch_status == '3'):
        print("CRITICAL: Cluster has some other problems")
        EXIT_STATUS = 2
    else:
        print("UNKNOWN: Error with checking cluster")
        EXIT_STATUS = 3
    sys.exit(EXIT_STATUS)
elif (command == "check_emc_isilon_nodehealth"):

    if check_snmp_access(community, ipaddr) != 0:
        sys.exit(2)

    ch_status = check_snmp(community, ipaddr, snmp_oids['nodeHealth'])
    node_name = check_snmp(community, ipaddr, snmp_oids['nodeName'])
    node_ro = check_snmp(community, ipaddr, snmp_oids['nodeReadOnly'])
    if (ch_status == '0'):
        print("OK: Node " + node_name + " is fine.")
        EXIT_STATUS = 0
    elif (ch_status == '1'):
        print("CRITICAL: Node " + node_name + ". Read-only status " + node_ro)
        EXIT_STATUS = 2
    elif (ch_status == '2'):
        print("CRITICAL: Node " + node_name + " is DOWN")
        EXIT_STATUS = 2
    elif (ch_status == '3'):
        print("CRITICAL: Node " + node_name + " is in INVALID state")
        EXIT_STATUS = 2
    else:
        print("UNKNOWN: Error with checking node")
        EXIT_STATUS = 3
    sys.exit(EXIT_STATUS)
elif (command == "check_emc_isilon_diskusage"):

    if check_snmp_access(community, ipaddr) != 0:
        sys.exit(2)

    ch_warn = _args['warn']

    ch_crit = _args['crit']

    totalBytes = int(check_snmp(community, ipaddr, snmp_oids['ifsTotalBytes']))
    usedbytes = int(check_snmp(community, ipaddr, snmp_oids['ifsUsedBytes']))
    usage_per = round(100.00 - ((float(usedbytes) / float(totalBytes)) * 100.00), 1)
    if (usage_per > ch_warn):
        print("OK: There is " + str(usage_per) + "% free space on /isi")
        sys.exit(0)
    else:
        if (usage_per > ch_crit):
            print("WARNING: There is " + str(usage_per) + "% free space on /isi")
            sys.exit(1)
        else:
            print("CRITICAL: there is " + str(usage_per) + "% free space on /isi")
            sys.exit(2)
elif (command == 'check_emc_isilon_diskstatus'):

    if check_snmp_access(community, ipaddr) != 0:
        sys.exit(2)

    diskbay = check_multi_snmp(community, ipaddr, snmp_oids['diskBay'])
    diskdevname = check_multi_snmp(
        community, ipaddr, snmp_oids['diskDeviceName'])
    diskstat = check_multi_snmp(community, ipaddr, snmp_oids['diskStatus'])
    disksernum = check_multi_snmp(
        community, ipaddr, snmp_oids['diskSerialNumber'])
    ERROR_CODES = dict()
    # print(diskbay.keys())
    for i in diskbay.keys():
        if ("DEAD" in str(diskstat[i])):
            ERROR_CODES[diskbay[i]] = "Bay " + str(diskbay[i]) + " | Serial Num.: " + str(disksernum[i]) + \
                                      " | Disk status: " + diskstat[i]
            print("CRITICAL: " + ERROR_CODES[i])
            sys.exit(2)
        if ("SMARTFAIL" in str(diskstat[i])):
            ERROR_CODES[diskbay[i]] = "Bay " + str(diskbay[i]) + " | Serial Num.: " + str(disksernum[i]) + \
                                      " | Disk status: " + diskstat[i]
            print("WARNING: " + ERROR_CODES[i])
            sys.exit(1)
        if ("L3" or "HEALTHY" in str(diskstat[i])):
            print("OK: All disks reported as HEALTHY")
        sys.exit(0)
    else:
        for i in ERROR_CODES.keys():
            print("UNKNOWN: " + ERROR_CODES[i])
            sys.exit(1)
else:
    parent_parser.print_help()
