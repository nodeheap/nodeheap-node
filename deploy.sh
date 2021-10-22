#!/bin/bash

echo "Auto nodestats deploy script!"

# Determine which user called the script, 
# as he will be owner of /opt/nodeheap
if [ $SUDO_USER ]; then user=$SUDO_USER; else user=`whoami`; fi

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root" 
  exit 1
fi

echo "Downloading Python pip3 requirements..."
pip3 install -r requirements.txt

NODEHEAP_LOC=/opt/nodeheap
CONFIG_FILE=${NODEHEAP_LOC}/node_config.yml

mkdir -p ${NODEHEAP_LOC}
echo "Deploying script to ${NODEHEAP_LOC}"
cp collector.py push_node_stats.py ${NODEHEAP_LOC}/

## Read Variables
echo
echo "Specify the node-id:"
read NODE_ID

echo
echo "Specify the secret:"
read SECRET

echo 
echo "Is this node a sealer ? (y/n)"
echo "*** If the answer is no, the node will be treated as a relay!"
read ROLE

if [ "$ROLE" == y ]
then
  ROLE="sealer"
else
  ROLE="relay"
fi


echo "Preparing config file..."
rm -rf ${CONFIG_FILE}

echo "Autodetecting network interface to monitor..."
NIF=$(/sbin/ip route | awk '/default/ { print $5 }')


echo "node_id: ${NODE_ID}" >> ${CONFIG_FILE}
echo "secret: ${SECRET}" >> ${CONFIG_FILE}
echo "role: ${ROLE}" >> ${CONFIG_FILE}
echo "net-interface: ${NIF}" >> ${CONFIG_FILE}

echo "Please follow these steps to modify the cronjob:"
echo "- sudo crontab -e"
echo "- Append the following line to cron, save, and exit."
echo "*/5 * * * * ${NODEHEAP_LOC}/push_node_stats.py 2>&1 | logger -t nodeheap"
echo
echo "Restart cron service with"
echo "sudo systemctl restart cron.service"
echo "or"
echo "sudo systemctl restart crond.service"

touch ${NODEHEAP_LOC}/current.log

#Set permissions
chown ${user}:${user} -R ${NODEHEAP_LOC}
chmod +x ${NODEHEAP_LOC}/push_node_stats.py
