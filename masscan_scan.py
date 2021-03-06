#!/usr/bin/env python3

import os
import re
import sys
import time
import uuid
import json
import math
import socket
import urllib
import masscan
import pathlib
import requests
import argparse
import traceback
import xml.dom.minidom
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def ip_txt_handle(ips):
    cidr_list = set()
    if 'txt' in ips:
        for ip in open(ips, 'r', encoding = 'utf-8').readlines():
            ip = ip.strip()
            if 'http' in ip:
                ip = ip.replace('http://', '')
                ip = ip.replace('https://', '')
                ip = ip.replace('/', '')
            domain_regex = re.compile(r'(?:[A-Z0-9_](?:[A-Z0-9-_]{0,247}[A-Z0-9])?\.)+(?:[A-Z]{2,6}|[A-Z0-9-]{2,}(?<!-))\Z', re.IGNORECASE)
            if domain_regex.match(ip):
                try:
                    ip = ip.replace('/', '')
                    ip = socket.gethostbyname(ip)
                    cidr_list.add(ip)
                except Exception as e:
                    print('域名%s获取IP失败  ' %(ip))
                    pass
                finally:
                    pass
            else:
                cidr_list.add(ip)
        with open(ips, 'w', encoding = 'utf-8') as writer:
            for ip in cidr_list:
                writer.write(ip + '\n')

def ip_xml_handle(xml_path):
    scan_list = []
    DOMTree = xml.dom.minidom.parse(xml_path)
    data = DOMTree.documentElement
    nodelist = data.getElementsByTagName('host')
    host_info = {}
    for node in nodelist:
        address_node = node.getElementsByTagName('address')
        addr = address_node[0].getAttribute('addr')
        port_node = node.getElementsByTagName('port')
        for port in port_node:
            portid = port.getAttribute('portid')
            scan_list.append(addr + ':' +portid)
    return scan_list

def masscan_scan(ips, ports, url_path, rate, out_port, out_url):
    scan_list = []
    print('Masscan starting.....\n')
    masscan_scan = masscan.PortScanner()
    if 'txt' in ips:
        masscan_scan.scan(ports = ports, arguments = '-sS -Pn -n --randomize-hosts -v --send-eth -iL %s --open --rate %s' % (ips, rate))
    else:
        masscan_scan.scan(hosts = ips, ports = ports, arguments = '-sS -Pn -n --randomize-hosts -v --send-eth --open --rate %s' % (rate))
    try:
        for host in masscan_scan.all_hosts:
            for masscan_proto in masscan_scan[host].keys():
                for masscan_port in masscan_scan[host][masscan_proto].keys():
                    scan_list.append(str(host) + ':' + str(masscan_port))
        print('Masscan scanned.....\n')
        print('Path starting.....\n')
        for ip_port in scan_list:
            with open(out_port, 'a') as writer:
                writer.write(ip_port + '\n')
            check(ip_port, url_path, out_url)
        print('Path scanned.....\n')
    except Exception as e:
        print(e)
        pass
    finally:
        pass

def check(host, url_path, out_path):
    try:
        for path in open(url_path).readlines():
            headers = {
                'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36 115Browser/6.0.3",
                "Connection": "close"
            }
            path = path.strip()
            url = 'http://{0}/{1}'.format(host, path)
            req = requests.get(url,  headers = headers, timeout = 20, verify = False)
            if req.status_code == 200:
                with open(out_path, 'a') as writer:
                    #print(http_url + '\n')
                    writer.write(url + '\n')
                    return True
            return False
    except Exception as e:
        #print(e)
        pass
    finally:
        pass

def main(ips, ports, url_path, rate, out_port, out_url):
    if 'txt' in ips:
        ip_txt_handle(ips)
    port_list = []
    if 'txt' in ports:
        for port in open(ports).readlines():
            port = port.strip()
            port_list.append(port)
        ports =  ",".join(port_list)
    if '.xml' in ips:
        scan_list = ip_xml_handle(ips)
        for ip_port in scan_list:
            with open(out_port, 'a') as writer:
                writer.write(ip_port + '\n')
            check(ip_port, url_path, out_url)
    else:
        masscan_scan(ips, ports, url_path, rate, out_port, out_url)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog = 'scan port', usage = 'python3 ps_masscan.py [options]')
    parser.add_argument('-i', "--ip", type = str, help = '-t 127.0.0.1 or -t ip.txt or ip.xml')
    parser.add_argument('-p', "--ports", type = str, help = '-p 80 or -p port.txt')
    parser.add_argument('-urlpath', "--urlpath", type = str, help ='-urlpath urlpath.txt')
    parser.add_argument('-rate', "--rate", type = int, help ='-rate 1000')
    parser.add_argument('-outport', '--outport', type = str, help = '-outport outport.txt')
    parser.add_argument('-outurl', '--outurl', type = str, help = '-outpurl outport.txt')
    args = parser.parse_args()
    if len(sys.argv) != 13:
        parser.print_help()
        exit()
    main(args.ip, args.ports, args.urlpath, args.rate, args.outport, args.outurl)