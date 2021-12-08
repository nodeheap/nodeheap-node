#!/bin/bash

###
### TODO
###
### Check if pip3 is installed.
### In Ubuntu it is python3-pip

echo "Auto nodestats deploy script!"

# Determine which user called the script, 
# as he will be owner of /opt/nodeheap
if [ $SUDO_USER ]; then user=$SUDO_USER; else user=`whoami`; fi

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root" 
  exit 1
fi

echo "Checking for pip3..."
if [ `which pip3` ] 
then
    echo "Found pip3 at: " `which pip3`
else
    echo "pip not found. Installing"
    apt-get install python3-pip
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
echo "Please enter the node role:"
echo "(s)ealer"
echo "(r)elay"
echo "(b)ridge"
echo ""
read ROLE

case $ROLE in

  s)
    echo -n "Sealer mode"
    ROLE="sealer"
    ;;

  r)
    echo -n "Relay mode"
    ROLE="relay"
    ;;

  b)
    echo -n "Bridge mode"
    ROLE="bridge"
    echo ""
    echo "Enter full path to docker-compose.yml (including the .yml filename): "
    read DOCKER_YML_PATH
    ;;

  *)
    echo -n "Unknown mode"
    ROLE=""
    ;;
esac


echo "Preparing config file..."
rm -rf ${CONFIG_FILE}

echo "Autodetecting network interface to monitor..."
NIF=$(/sbin/ip route | awk '/default/ { print $5 }')


echo "node_id: ${NODE_ID}" >> ${CONFIG_FILE}
echo "secret: ${SECRET}" >> ${CONFIG_FILE}
echo "role: ${ROLE}" >> ${CONFIG_FILE}
echo "net-interface: ${NIF}" >> ${CONFIG_FILE}
if [ $ROLE == 'bridge' ]
then
    echo "docker-yml: ${DOCKER_YML_PATH}" >> ${CONFIG_FILE}
    echo "bridge-check-interval: 90" >> ${CONFIG_FILE}
fi


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
