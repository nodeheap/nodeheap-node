#!/usr/bin/env python3
# Requires Python 3.5+
# Set up dependencies via PIP.
# This script should be run as a cron job every 5 minutes.

import requests
import collector as c
import yaml
import logging
import os
import sys


STATS_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
LOGGING_FILE = os.path.join(STATS_DIRECTORY, 'current.log')
CONFIG_FILE = os.path.join(STATS_DIRECTORY, 'node_config.yml')
API_ENDPOINT_FORMAT = 'https://hud-api.nodeheap.com/stats/{}'

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOGGING_FILE),
        logging.StreamHandler()
    ])

def get_data():
    (total_space, used_space, free_space) = c.du()
    (cpu_temp, cpu_usage) = c.cpu_stats()
    uptime = c.uptime()
    (tx, rx) = c.network()
    nlin = c.logged_in_users()
    isNodeRunning = c.checkIfProcessRunning('Nethermind.Runner')
    isTorRunning = c.checkIfProcessRunning('tor')
    lastSealTime = c.lastSealedBlock()
    (total_mem, mem_used, mem_free) = c.memory()

    data = {
        'total_space':total_space,
        'used_space':used_space,
        'free_space':free_space,
        'cpu_temp':cpu_temp,
        'cpu_usage':cpu_usage,
        'uptime':uptime,
        'tx_bytes':tx,
        'rx_bytes':rx,
        'num_users_logged_in':nlin,
        'is_node_running':isNodeRunning,
        'is_tor_running':isTorRunning,
        'total_mem': total_mem,
        'mem_used': mem_used,
        'mem_free': mem_free,
        'last_sealed_block_time': lastSealTime,
    }
    return(data)


def push_data(data):
    config = {}
    with open(CONFIG_FILE) as f:
        config = yaml.safe_load(f)

    api_endpoint = API_ENDPOINT_FORMAT.format(config['node_id'])
    headers = {
        'q-latch': "27sdfh69ej-sdf62palx420",
        'node-secret': config['secret'],
    }

    logging.info('Sending POST request to %s: %s' % (api_endpoint, data))
    response = requests.post(api_endpoint, json=data, headers=headers)
    if response.status_code != 201:
        logging.error('Failed to call API (%s). %s: %s' % (response.status_code, response.reason, response.text))
        raise Exception('API call failed')

    logging.info('Response: %s %s' % (response.status_code, response.text))


if __name__ == "__main__":
    logging.info('Started stats push')
    try:
        data = get_data()
        push_data(data)
        logging.info('Completed push successfully')
        sys.exit(0)
    except Exception as e:
        logging.error('Failed push with exception: %s', e)
        sys.exit(1)
