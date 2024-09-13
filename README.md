# Warnet: The Battle of Atlanta 2024

The object of the game is to attack Bitcoin Core nodes in a private network
running in a Kubernetes cluster.

An attack is considered successful when a target node is no longer in sync with
the most-work chain. This could be the result of:
- An eclipse attack
- An out-of-memory error kills the node process
- A CPU denial-of-service prevents the node from verifying new blocks

## What is Warnet?

Warnet is a system written in Python to deploy, manage, and interact with
Bitcoin p2p networks inside a Kubernetes cluster. The official battlefield
will be a remote cluster with 100 Bitcoin nodes (referred to as "Tanks")
running on a custom Signet chain. Many of these nodes will be old versions of
Bitcoin Core with
[publicly disclosed vulnerabilities](https://bitcoincore.org/en/blog/).

To help facilitate Tank-attacking strategies on the battlefield, a smaller
12-node network can be run on a regtest chain locally by attackers while
developing.

Attackers will not be able to generate their own blocks on the battlefield
Signet chain, but have unlimited permission on their local regtest networks.

## The Arsenal

The primary method of interacting with the network is by deploying a Scenario.
A Scenario is a Python script written with the same structure and library as
a Bitcoin Core functional test, utilizing a copy of the `test_framework`. The
primary difference is that the familiar `self.nodes[]` list contains references
to containerized Bitcoin Core nodes running inside the cluster rather than
locally accessible bitcoind processes.

An additional list `self.tanks[str]` is available to address Bitcoin nodes
by their kubernetes pod name (as opposed to their numerical index).

A handful of example scenarios are included in the `scenarios/` directory.
In particular, `scenarios/reconnaissance.py` is written with verbose comments
to demonstrate how to execute RPC commands on available nodes, as well as how
to utilize the framework's `P2PInterface` class to send arbitrary messages
to targeted nodes.

## Prepare For War

To deploy attacks on the remote battlefield you will only need to have Warnet,
Helm, and Kubectl installed locally. To experiment locally with a mini-network
you will also need Kubernetes installed (which requires a Docker daemon in
addition to either Docker Desktop or MiniKube).

Documentation for Warnet is available in its repository:

https://github.com/bitcoin-dev-project/warnet

### Install Warnet

Using a Python virtual environment is strongly recommended.

```
git clone <this repo>
cd <this repo>
python -m venv .venv
source .venv/bin/activate
pip install warnet
```

### Setup Warnet

Warnet itself can guide you through the setup process, you can choose to skip
the local backend and work only on the remote cluster by making selections in
the menu.

```
(.venv) $ warnet setup

                 ╭───────────────────────────────────╮
                 │  Welcome to Warnet setup          │
                 ╰───────────────────────────────────╯

    Let's find out if your system has what it takes to run Warnet...

[?] Which platform would you like to use?:
 > Minikube
   Docker Desktop
   No Backend (Interacting with remote cluster, see `warnet auth --help`)
```

### Additional tools

Whether you run Kubernetes locally or use the remote cluster, we recommend the
terminal user interface [k9s](https://github.com/derailed/k9s) to monitor
cluster status.

## Local Simulation

### Start and Stop the Network

Deploy the 12-node network included in this repository with the command:

```
warnet deploy ./networks/regtest_12
```

You can see the topology of this network as well as which tanks are running
which Bitcoin Core versions in `networks/regtest_12/network.yaml`

The local network can be shut down with the command:

```
warnet down
```

### Monitor the Network

You can open the web based visualizer with Grafana dashboards and Fork Observer
at `localhost:2019` by executing the command:

```
warnet dashboard
```

See the [Warnet documentation](https://github.com/bitcoin-dev-project/warnet/blob/main/docs/warnet.md)
for more CLI commands to retrieve logs, p2p messages, and other status
information.

Example:

```
(.venv) $ warnet status
╭─────────────── Warnet Overview ───────────────╮
│                                               │
│                 Warnet Status                 │
│ ┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓ │
│ ┃ Component ┃ Name                ┃ Status  ┃ │
│ ┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩ │
│ │ Tank      │ tank-0000           │ running │ │
│ │ Tank      │ tank-0001           │ running │ │
│ │ Tank      │ tank-0002           │ running │ │
│ │ Tank      │ tank-0003           │ running │ │
│ │ Tank      │ tank-0004           │ running │ │
│ │ Tank      │ tank-0005           │ running │ │
│ │ Tank      │ tank-0006           │ running │ │
│ │ Tank      │ tank-0007           │ running │ │
│ │ Tank      │ tank-0008           │ running │ │
│ │ Tank      │ tank-0009           │ running │ │
│ │ Tank      │ tank-0010           │ running │ │
│ │ Tank      │ tank-0011           │ running │ │
│ │ Scenario  │ No active scenarios │         │ │
│ └───────────┴─────────────────────┴─────────┘ │
│                                               │
╰───────────────────────────────────────────────╯

Total Tanks: 12 | Active Scenarios: 0
Network connected  
```

### ATTACK!

Add or modify the files in `scenarios/` and deploy them to the network:

```
(.venv) $ warnet run ./scenarios/reconnaissance.py 
Successfully started scenario: reconnaissance
Commander pod name: commander-reconnaissance-1726250994
```

Follow the output of the scenario:

```
(.venv) $ warnet logs -f
[?] Please choose a pod: 
 ❯ commander-reconnaissance-1726250994
   tank-0000
   tank-0001
   tank-0002
   tank-0003
   tank-0004
   tank-0005
   tank-0006
   tank-0007
   tank-0008
   tank-0009
   tank-0010
   tank-0011

Reconnaissance Adding TestNode #0 from pod tank-0000 with IP 10.1.35.165
Reconnaissance Adding TestNode #1 from pod tank-0001 with IP 10.1.35.166
Reconnaissance Adding TestNode #2 from pod tank-0002 with IP 10.1.35.168
Reconnaissance Adding TestNode #3 from pod tank-0003 with IP 10.1.35.170
Reconnaissance Adding TestNode #4 from pod tank-0004 with IP 10.1.35.169
Reconnaissance Adding TestNode #5 from pod tank-0005 with IP 10.1.35.171
Reconnaissance Adding TestNode #6 from pod tank-0006 with IP 10.1.35.172
Reconnaissance Adding TestNode #7 from pod tank-0007 with IP 10.1.35.173
Reconnaissance Adding TestNode #8 from pod tank-0008 with IP 10.1.35.174
Reconnaissance Adding TestNode #9 from pod tank-0009 with IP 10.1.35.175
Reconnaissance Adding TestNode #10 from pod tank-0010 with IP 10.1.35.176
Reconnaissance Adding TestNode #11 from pod tank-0011 with IP 10.1.35.177
Reconnaissance User supplied random seed 131260415370612
Reconnaissance PRNG seed is: 131260415370612
Reconnaissance Getting peer info
Reconnaissance tank-0001 /Satoshi:27.0.0/
Reconnaissance tank-0002 /Satoshi:27.0.0/
Reconnaissance tank-0003 /Satoshi:27.0.0/
Reconnaissance tank-0005 /Satoshi:25.1.0/
Reconnaissance 10.1.35.173:60926 /Satoshi:0.21.1/
Reconnaissance tank-0006 /Satoshi:24.2.0/
Reconnaissance tank-0004 /Satoshi:26.0.0/
Reconnaissance 10.1.35.177:60262 /Satoshi:0.16.1/
Reconnaissance 10.1.35.174:48636 /Satoshi:0.20.0/
Reconnaissance tank-0011 /Satoshi:0.16.1/
Reconnaissance tank-0010 /Satoshi:0.17.0/
Reconnaissance Attacking 10.102.248.229:18444
Reconnaissance Got notfound message from 10.102.248.229:18444
Reconnaissance Stopping nodes
Reconnaissance Cleaning up /tmp/bitcoin_func_test_uixks5tx on exit
Reconnaissance Tests successful
```

## Fight On The Battlefield

When you are ready to launch your attack for real, start by "switching context"
from your local cluster to the remote cluster. You will have a config file
provided by the administrator:

** // TODO **

```
warnet auth ...
```





