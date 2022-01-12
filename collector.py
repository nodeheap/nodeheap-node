#!/usr/bin/env python3
"""
This file contains data collection and packing functions.
"""

from subprocess import Popen, PIPE
import re
import os
import psutil
from datetime import timedelta, datetime
from time import strftime, localtime
import yaml

# Only for development purposes!!!
# Set this value to False for deployment.
# Leaving DEV_MODE at True, could lead to inaccurate data in reporting.
DEV_MODE = False

RELAY = "relay"
SEALER = "sealer"
BRIDGE = "bridge"

CONTINUITY_CHECK_LIMIT = 10

class Collector():
    def __init__(self, config):
        """
        """
        self.config = config

        self.function_call_list = \
            {   SEALER : [
                    [['total_space', 'used_space', 'free_space'], self.du()], 
                    [['cpu_temp', 'cpu_usage'], self.cpu_stats()], 
                    [['uptime'], self.uptime()],
                    [['tx_bytes', 'rx_bytes'], self.network()],
                    [['num_users_logged_in'], self.logged_in_users()], 
                    [['is_node_running'], self.checkIfProcessRunning('Nethermind.Runner')],
                    [['is_tor_running'], self.checkIfProcessRunning('tor')], 
                    [['total_mem', 'mem_used', 'mem_free'], self.memory()],
                    [['last_sealed_block_time', 'is_nethermind_healthy', 'node_error'], self.lastSealedBlock()],
                ],
                RELAY : [
                    [['total_space', 'used_space', 'free_space'], self.du()], 
                    [['cpu_temp', 'cpu_usage'], self.cpu_stats()], 
                    [['uptime'], self.uptime()],
                    [['tx_bytes', 'rx_bytes'], self.network()],
                    [['num_users_logged_in'], self.logged_in_users()], 
                    [['is_node_running'], self.checkIfProcessRunning('Nethermind.Runner')],
                    [['is_tor_running'], self.checkIfProcessRunning('tor')], 
                    [['total_mem', 'mem_used', 'mem_free'], self.memory()]
                ],
                BRIDGE : [
                    [['total_space', 'used_space', 'free_space'], self.du()], 
                    [['cpu_temp', 'cpu_usage'], self.cpu_stats()], 
                    [['uptime'], self.uptime()],
                    [['tx_bytes', 'rx_bytes'], self.network()],
                    [['num_users_logged_in'], self.logged_in_users()], 
                    [['total_mem', 'mem_used', 'mem_free'], self.memory()],
                    [['is_bridge_healthy'], self.isBridgeHealthy()]
                ]
            }


    def logged_in_users(self):
        """
        Get logged in users.
        """
        W = 'w'

        process = Popen([W, '-u', '-h'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        data = stdout.decode('utf-8')

        p = re.compile("(?m)^.*?\W")

        data = p.findall(data)
        return (len(data))


    def uptime(self):
        """
        Get server uptime.
        """
        process = Popen(['cat', '/proc/uptime'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        data = stdout.decode('utf-8')
        data = float(data.split(' ')[0])
        return(int(data))


    def du(self):
        """
        Get disk usage.
        """
        disk = psutil.disk_usage(os.path.realpath('/'))

        disk_total = disk.total
        disk_used = disk.used
        disk_free = disk.free

        return(disk_total, disk_used, disk_free)


    def cpu_stats(self):
        """
        Get CPU data.
        """
        coretemp_avg = 0
        try:
            data = psutil.sensors_temperatures()['coretemp']
            for temp in data:
                coretemp_avg = coretemp_avg + temp.current
            coretemp_avg = int(coretemp_avg/len(data))
        except Exception:
            coretemp_avg = None


        cpu_usage = psutil.cpu_percent()
        return(coretemp_avg, cpu_usage)


    def network(self):
        interface = self.config['net-interface']
        data = psutil.net_io_counters(pernic=True)
        tx = data[interface].bytes_sent
        rx = data[interface].bytes_recv

        return (tx, rx)


    def memory(self):
        memory = psutil.virtual_memory()
        return(memory.total, memory.used, memory.available)


    def checkIfProcessRunning(self, processName):
        '''
        Check if there is any running process that contains the given name processName.
        '''
        #Iterate over the all the running process
        if not DEV_MODE:
            for proc in psutil.process_iter():
                try:
                    # Check if process name contains the given name string.
                    if processName.lower() in proc.name().lower():
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            return False
        else:
            return True


    def lastSealedBlock(self):
        print("Seal check")
        sealed_cnt = 0
        sealed_inv = 0
        s_date = 0
        s_time = 0
        timeZone = 0
        continuity_pass = None
        is_nethermind_healthy = None
        node_error = None
        err_msg = None

        if not DEV_MODE:    
            f = open("/var/log/nethermind.log", "r")

            seal_data_ok = []
            seal_data_inv = []
            for line in f:
                if "Sealed" in line:
                    sealed_cnt = sealed_cnt + 1
                    temp = line.split(' ')
                    s_date = temp[0]
                    s_time = temp[1].split('|')[0]
                    s_block = temp[3]
                    seal_data_ok.append([s_date, s_time, s_block])

                if "seal parameters incorrect" in line:
                    sealed_inv = sealed_inv + 1
                    temp = line.split(' ')
                    s_date = temp[0]
                    s_time = temp[1].split('|')[0]
                    seal_data_inv.append([s_date, s_time])
        else:
            (tm_year, tm_mon, tm_day, tm_hour, tm_min, tm_sec, _, _, _) = localtime()
            s_date = "{}-{}-{}".format(tm_year, tm_mon, tm_day)
            s_time = "{}:{}:{}.0000".format(tm_hour, tm_min, tm_sec)

        timeZone = strftime("%z")
        timeZone = timeZone[:3] + ":" + timeZone[3:]
        time_string = "{}T{}{}".format(s_date, s_time, timeZone)

        """
        Perform a continuity check, by comparing the last 10 sealed blocks.
        In case the checker finds 2 sealed blocks which difference is less
        than the value set in CONTINUITY_CHECK_LIMIT, then alert will be sent
        to the operator.
        """
        print("Performing seal continuity and health check!!!")

        old_block = 0
        for (_, _, s_block) in seal_data_ok[-10:]:
            if (int(s_block) - int(old_block) < CONTINUITY_CHECK_LIMIT):
                err_msg = "Continuity check FAILED (difference {}) at block {}-{}.".format(int(s_block) - int(old_block), int(s_block), int(old_block))
                print(err_msg)
                continuity_pass = False
            else:
                continuity_pass = True
            old_block = s_block

        if (continuity_pass == True):
            is_nethermind_healthy = True
            node_error = None
        else:
            is_nethermind_healthy = False
            node_error = err_msg


        return (time_string, is_nethermind_healthy, node_error)


    def generate_json(self, raw_data):
        """
        Function which will format the input raw_data to JSON format.
        ::raw_data:: - input argument, [[list of JSON strings], (data)]
        
        Return:
            JSON data.
        """

        data = {}
        for (json_vals, values) in raw_data:
            if len(json_vals)>1:
                for json_val, value in zip(json_vals, values):

                    """
                    Don't add the value into JSON response if the
                    value is None.
                    """
                    if value is not None:
                        data[json_val] = value
                    else:
                        continue
            else:
                json_val = json_vals[0]
                value = values

                """
                Don't add the value into JSON response if the
                value is None.
                """
                if value is not None:
                    data[json_val] = value
                else:
                    continue

        return(data)


    def isBridgeHealthy(self):
        """
        Check bridge health.
        If there is no log pushed for more than bridge_check_interval seconds it will
        return False which indicates Bridge health is bad.
        Otherwise return True.
        """

        # If node is running in bridge mode, then read the config.
        # Otherwise return False.
        if (self.config['role'] == 'bridge'):
            docker_compose_path = self.config['docker-yml']
            bridge_check_interval = self.config['bridge-check-interval']
        else:
            return(False)

        compose_path="--file="+str(docker_compose_path)
        process = Popen(['docker-compose', compose_path, 'logs', '--tail=1'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        p = re.compile("(?m)[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}")
        data = stdout.decode('utf-8')
        data = p.findall(data)

        # ['2021-12-08T20:09:20']

        data = data[0].split('T')
        (logYear, logMonth, logDay) = data[0].split('-')
        (logHour, logMinute, logSecond) = data[1].split(':')

        logYear = int(logYear)
        logMonth = int(logMonth)
        logDay = int(logDay)
        logHour = int(logHour)
        logMinute = int(logMinute)
        logSecond = int(logSecond)

        logTime = datetime(logYear, logMonth, logDay, logHour, logMinute, logSecond)
        if (DEV_MODE):
            localTime = datetime(2021, 12, 8, 21, 50, 0)
        else:
            (tm_year, tm_mon, tm_day, tm_hour, tm_min, tm_sec, _, _, _) = localtime()
            localTime = datetime(tm_year, tm_mon, tm_day, tm_hour, tm_min, tm_sec)

        timeDiff = localTime - logTime
        timeDiff = int(timeDiff.total_seconds())

        if (timeDiff >= bridge_check_interval):
            return False
        else:
            return True


    def collect_data(self):
        node_role = self.config['role']
        raw_data = self.function_call_list[node_role]
        data = self.generate_json(raw_data)
        return(data)


if __name__ == "__main__":
    data = collect_data(config)
    print(data)
