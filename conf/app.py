# For each file in directory /config
import os
import random
from subprocess import PIPE, run
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import socket

wireguard_configs = []
history = []
# Init
# Strip the IPv6 Part of the Wireguard config, Requird for Dockerimage 
def init():
    for file in os.listdir("/config"):
        if file.endswith(".conf"):
            new_config = []
            #Read file contents
            with open("/config/" + file, 'r') as f:
                    for line in f.read().split('\n'):
                        if any(line.startswith(s) for s in ['Address','DNS','AllowedIPs']) and ',' in line:
                            new_config.append(line.split(',')[0])
                        else:
                            new_config.append(line)
            wireguard_configs.append('\n'.join(new_config))

# Pick a random config, dont pick the same one twice until all have been used
def pick_random_config():
    while(len(history)<len(wireguard_configs)):
        random_config = random.choice(wireguard_configs)
        if random_config not in history:
            history.append(random_config)
            return random_config
    if(len(history)==len(wireguard_configs)):
        history.clear()
        random_config = random.choice(wireguard_configs)
        history.append(random_config)
        return random.choice(wireguard_configs)	

# Write the config to a file
def renew_config():
    with open("/config/wg0.conf", 'w') as f:
        f.write(pick_random_config())

def connection():
    try:
        response = urlopen('http://ifconfig.io/country_code', timeout=1).read().decode('utf-8')
    except HTTPError as error:
        print("HTTPError")
        return False
    except URLError as error:
        if isinstance(error.reason, socket.timeout):
            print("Timeout")
            return False
        else:
            print("HTTPError")
            return False
    else:
        print("All Good:",response)
        return True

# Setup Wireguard
def wireguard():
    result = run(['wg', 'show'], stdout=PIPE, stderr=PIPE, universal_newlines=True)
    if('wg0' in result.stdout and result.returncode == 0):
        print("Wireguard is, turning off")
        result = run(['wg-quick', 'down', '/config/wg0.conf'], stdout=PIPE, stderr=PIPE, universal_newlines=True)
        print(result.returncode, result.stdout, result.stderr)
    renew_config()
    print("Turning on Wireguard")
    result = run(['wg-quick', 'up', '/config/wg0.conf'], stdout=PIPE, stderr=PIPE, universal_newlines=True)
    print(result.returncode, result.stdout, result.stderr)
    if not connection():
        print("Connection Failed, Setup new config")
        wireguard()



#init()
#wireguard()
