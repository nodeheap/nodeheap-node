# NodeHeap

## Getting Started

So you decided to use NodeHeap to monitor your node and Shyft operations? Good choice.

As we're in Beta, you'll need to give us some information out of band.
1) Sealer node name
2) Coinbase address (to track balance)
3) E-mails of those you want to access our dashboard (we use Google SSO)
4) Phone numbers that you want to receive text alerts

### Sending stats to NodeHeap from your node

To push stats up to the NodeHeap service at a regular interval, you'll need to run a cronjob on your node.

#### Automatic deploy

1) Clone this repository into a `nodeheap` directory on your node. 
2) Execute `deploy.sh` as a superuser. e.g. `sudo ./deploy.sh` 
3) Follow the instructions for `crontab`


#### Manual deploy
1) Clone this repository into a `nodeheap` directory on your node and copy it to `/opt/nodeheap`.
2) Copy `node_config.yml.example` to `node_config.yml` and fill in your node's details inside the new file (ID and secret).
3) `pip install -r requirements.txt`
4) `chmod +x push_node_stats.py`
5) Run `sudo ./push_node_stats.py`. Note that you'll need to have `python3` and a few `pip` dependencies installed. Reach out if this doesn't run successfully. If you get complaints about a log file, try running with `sudo`.
6) Set a cronjob to run that push script every 5 minutes. The easiest way is to run (from superuser) `crontab -e` and add an entry. This will look something like `*/5 * * * * /opt/nodeheap/push_node_stats.py 2>&1 | logger -t nodeheap`. The last portion redirects the output to `/var/log/syslog`, otherwise cron tries to "mail" the output.
7) To make sure it's working, tail the logs in the directory (via `tail -f current.log`) and wait.
8) Refresh the NodeHeap page and see that your stats are coming in.

## Sit back and relax

NodeHeap will send notifications when your node is not sending stats, offline, not sealing, disconnected from Tor, or the balance is not changing as expected.

## Future

Feature requests welcome. We'll be working on improving our look and experience. We are also moving to expand to relays.


\- The NodeHeap team
