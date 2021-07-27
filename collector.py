#!/usr/bin/env python3
from subprocess import Popen, PIPE
import re
import os
import psutil
from datetime import date, timedelta, datetime

def logged_in_users():
    W = 'w'

    process = Popen([W, '-u', '-h'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    data = stdout.decode('utf-8')

    p = re.compile("(?m)^.*?\W")

    data = p.findall(data)
    return (len(data))


def uptime():
    process = Popen(['cat', '/proc/uptime'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    data = stdout.decode('utf-8')
    data = float(data.split(' ')[0])
    return(int(data))


def du():
    disk = psutil.disk_usage(os.path.realpath('/'))

    disk_total = disk.total
    disk_used = disk.used
    disk_free = disk.free

    return(disk_total, disk_used, disk_free)


def cpu_stats():
    coretemp_avg = 0
    data = psutil.sensors_temperatures()['coretemp']
    for temp in data:
        coretemp_avg = coretemp_avg + temp.current
    coretemp_avg = int(coretemp_avg/len(data))

    cpu_usage = psutil.cpu_percent()
    return(coretemp_avg, cpu_usage)


def network(interface='eno1'):
    data = psutil.net_io_counters(pernic=True)
    tx = data[interface].bytes_sent
    rx = data[interface].bytes_recv
    return (tx, rx)


def memory():
    memory = psutil.virtual_memory()
    return(memory.total, memory.used, memory.available)


def checkIfProcessRunning(processName):
    '''
    Check if there is any running process that contains the given name processName.
    '''
    #Iterate over the all the running process
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def lastSealedBlock():
    sealed_cnt = 0
    sealed_inv = 0
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
            i_date = temp[0]
            i_time = temp[1].split('|')[0]
            seal_data_inv.append([i_date, i_time])

    # 2021-06-23 02:14:19.2989|Invalid block header (0x2f69f24ae1f6dc8f9c6681166f599217d5ce702e589cb5810d1d9a6de0043fdc) - seal parameters incorrect
    # Adjust the time zone if required.
    time_string = "{}T{}+00:00".format(s_date, s_time)
    return (time_string)


if __name__ == "__main__":
    print(logged_in_users())
    print(uptime())
    print(du())
    print(cpu_stats())
    print(network())
    print(memory())
    print(checkIfProcessRunning('Nethermind.Runner'))
    print(checkIfProcessRunning('tor'))
    print(lastSealedBlock())
