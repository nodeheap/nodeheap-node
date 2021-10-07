#!/usr/bin/env python3
# Requires Python 3.5+
# Set up dependencies via PIP.
# This script should be run as a cron job every 5 minutes.

import requests
from collector import Collector
import yaml
import logging
import os
import sys


STATS_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
LOGGING_FILE = os.path.join(STATS_DIRECTORY, 'current.log')
CONFIG_FILE = os.path.join(STATS_DIRECTORY, 'node_config.yml')
API_ENDPOINT_FORMAT = 'https://api.nodeheap.com/stats/{}'

global config

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOGGING_FILE),
        logging.StreamHandler()
    ])



def load_config():
    """
    Function to load configuration
    """
    config = {}
    with open(CONFIG_FILE) as f:
        config = yaml.safe_load(f)

    return config


def push_data(data):
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
    config = load_config()
    c = Collector(config)
    try:
        data = c.collect_data()
        push_data(data)
        logging.info('Completed push successfully')
        sys.exit(0)
    except Exception as e:
        logging.error('Failed push with exception: %s', e)
        sys.exit(1)
