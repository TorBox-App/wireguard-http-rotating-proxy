"""
MITMProxy Wireguard IP Rotator
"""
import logging
# For each file in directory /conf
import os
import random
from subprocess import PIPE, run
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import socket
from mitmproxy.script import concurrent

class Rotator:
    # Pick a random config, dont pick the same one twice until all have been used
    def pick_random_config(self):
        while(len(self.history)<len(self.wireguard_configs)):
            random_config = random.choice(self.wireguard_configs)
            if random_config not in self.history:
                self.history.append(random_config)
                return random_config
        if(len(self.history)==len(self.wireguard_configs)):
            self.history.clear()
            random_config = random.choice(self.wireguard_configs)
            self.history.append(random_config)
            return random.choice(self.wireguard_configs)	

    # Write the config to a file
    def renew_config(self):
        with open("/etc/wireguard/wg0.conf", 'w') as f:
            f.write(self.pick_random_config())

    def connection(self):
        try:
            response = urlopen('http://ifconfig.io/country_code', timeout=1).read().decode('utf-8')
        except HTTPError as error:
            logging.info("HTTPError")
            return False
        except URLError as error:
            if isinstance(error.reason, socket.timeout):
                logging.info("Timeout")
                return False
            else:
                logging.info("HTTPError")
                return False
        else:
            logging.info("All Good:"+response)
            return True

    # Setup Wireguard
    def wireguard(self):
        result = run(['wg', 'show'], stdout=PIPE, stderr=PIPE, universal_newlines=True)
        if('wg0' in result.stdout and result.returncode == 0):
            logging.info("Wireguard is on, turning off")
            result = run(['wg-quick', 'down', '/etc/wireguard/wg0.conf'], stdout=PIPE, stderr=PIPE, universal_newlines=True)
            logging.info(result.returncode)
        self.renew_config()
        logging.info("Turning on Wireguard")
        result = run(['wg-quick', 'up', '/etc/wireguard/wg0.conf'], stdout=PIPE, stderr=PIPE, universal_newlines=True)
        logging.info(result.returncode)
        if not self.connection():
            logging.info("Connection Failed, Setup new config")
            self.wireguard()

    def __init__(self):
        self.num = 0
        self.wireguard_configs = []
        self.history = []
        self.max_requests_per_ip = int(os.getenv('max', '3'))

    # Init
    # Strip the IPv6 Part of the Wireguard config, Requird for Dockerimage 
        for file in os.listdir("/conf/"):
            if file.endswith(".conf"):
                new_config = []
                #Read file contents
                with open("/conf/" + file, 'r') as f:
                        for line in f.read().split('\n'):
                            if any(line.startswith(s) for s in ['Address','DNS','AllowedIPs']) and ',' in line:
                                new_config.append(line.split(',')[0])
                            else:
                                new_config.append(line)
                self.wireguard_configs.append('\n'.join(new_config))
    
        self.wireguard() # Setup Initial Connection


    @concurrent
    def request(self, flow):
        self.num = self.num + 1
        if self.num >= self.max_requests_per_ip:
            logging.info("Time for IP Change")
            self.wireguard()
            self.num = 0
        logging.info("We've seen %d flows" % self.num)

addons = [Rotator()]