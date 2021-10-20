# NodeHeap

## Getting Started

So you decided to use NodeHeap to monitor your node and Shyft operations? Good choice.

Your home is at [nodeheap.com](https://www.nodeheap.com/). From there, you can add people to your team, enable text alerts, add nodes, etc.

A lot of functionality is unlocked just like that! Read further for lower-level monitoring of individual nodes.

### Sending stats to NodeHeap from your node

To get a deeper level of monitoring, you can push stats up to the NodeHeap service from your node at a regular interval via cronjob. This lets you detect if your node is up, having connectivity or hardware problems, and anything else you'd want to monitor. This will generally also alert you faster (~5 mins) if something is amiss.

To start, go to Settings->Nodes on your dashboard. Add a node there, and you'll see the ID and secret you'll need going forward.

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
6) Set a cronjob to run that push script every 5 minutes (it must be 5 minutes). The easiest way is to run (from superuser) `crontab -e` and add an entry. This will look something like `*/5 * * * * /opt/nodeheap/push_node_stats.py 2>&1 | logger -t nodeheap`. The last portion redirects the output to `/var/log/syslog`, otherwise cron tries to "mail" the output.
7) To make sure it's working, tail the logs in the directory (via `tail -f current.log`) and wait.
8) Refresh the NodeHeap page and see that your stats are coming in.

#### Logs

You can inspect logs from the script at `/opt/nodeheap/current.log`. Logs from the cronjob can be found at `/var/log/syslog`. The relevant lines can be found by doing `grep` on `nodeheap`.

## Sit back and relax

NodeHeap will send notifications when your node is not sending stats, offline, not sealing, disconnected from Tor, or the balance is not changing as expected.

## Roadmap

Feature requests welcome.

- Add webhooks to initiate an action (e.g. restart node) upon getting a notification (e.g. node is down)
- Generate custom reports as a CSV
- Add support for more nodes: backup sealers
- Tax compliance: view live tax liability, export daily mining & price data to accountant
- Bridge activity: volume across the bridge
- Add wallets to watch


\- The NodeHeap team
