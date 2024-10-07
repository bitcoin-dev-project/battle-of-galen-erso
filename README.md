# Warnet: The Battle of Galen Erso

Your mission is to attack Bitcoin Core nodes in a private network
running in a Kubernetes cluster.

## Terminology

- Tanks - Bitcoin Core nodes running in a Warnet network
- Battlefield - A remote cluster with 100 tanks
- Scenario - A program that deploys to the battlefield to attack the tanks

## Objectives

1. Install and set up Warnet
2. Create attacks
3. Test attacks locally
4. Attack Bitcoin Core nodes on the battlefield

## Intelligence Brief -- What is Warnet?

Warnet is a system written in Python to deploy, manage, and interact with
Bitcoin p2p networks inside a Kubernetes cluster. The official battlefield
will be a remote cluster with 100 Bitcoin nodes (referred to as "Tanks")
running on a custom Signet chain. Many of these nodes will be old versions of
Bitcoin Core with
[publicly disclosed vulnerabilities](https://bitcoincore.org/en/blog/).

To help facilitate Tank-attacking strategies on the battlefield, a smaller
12-node network can be run on a regtest chain locally by attackers while
developing scenarios.

### Install Warnet

Documentation for Warnet is available in its repository:

https://github.com/bitcoin-dev-project/warnet

### Setup Warnet

Warnet itself will guide you through the setup process.

> [!TIP]
> **There are several options to carefully choose when setting up Warnet!**
> - You only need to install minikube or docker desktop's kubernetes if you plan to run the 12-node regtest network locally for experimentation and development.
> - Accessing the remote 100-node signet battlefield does not require a local kubenetes distribution, but will still require installation of `kubectl`.

#### One Warnet is installed, execute `warnet setup`

Example:

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

#### K9s

Whether you run Kubernetes locally or use the remote cluster, we recommend the
terminal user interface [k9s](https://github.com/derailed/k9s) to monitor
cluster status.

![k9s screenshot](./images/k9s-screenshot.png)

#### ktop

If you want to observe resource usage on a cluster with metrics enabled, you
may want to consider using [ktop](https://github.com/vladimirvivien/ktop)

![ktop screenshot](./images/ktop-screenshot.png)

## Network Operations

### Start and Stop the Network

You can see the topology of the network which will be deployed, and make
modifications to it by looking at: `networks/regtest_12/network.yaml`
This will also allow you to see which tanks are running which version of
Bitcoin Core.

Deploy the 12-node network included in this repository to a local Kubernetes
cluster with the command:

```
warnet deploy ./networks/regtest_12
```

The local network can be shut down with the command:

```
warnet down
```

### Network Reconnaissance

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

## Ordnance

### Attack Development

The primary method of interacting with the network and mounting an attack is by
deploying a Scenario.

A Scenario is a Python script written with the same structure and library as
a Bitcoin Core functional test, utilizing a copy of the `test_framework`.
The primary difference is that the familiar `self.nodes[]` list contains
references to containerized Bitcoin Core nodes running inside the
cluster rather than locally accessible bitcoind processes.

An additional list `self.tanks[str]` is available to address Bitcoin nodes
by their Kubernetes pod name (as opposed to their numerical index).

A handful of example scenarios are included in the [`scenarios/`](/scenarios/) directory.
In particular, [`scenarios/reconnaissance.py`](/scenarios/reconnaissance.py) is written with verbose comments
to demonstrate how to execute RPC commands on available nodes, as well as how
to utilize the framework's `P2PInterface` class to send arbitrary messages
to targeted nodes.

### Attack Deployment

To create an attack modify the existing files in `scenarios/` or create new
ones and deploy them to the network. The `--debug` flag will print the log output
of the scenario back to the terminal, and delete the container when it finishes
running by either success, failure, or interruption by `ctrl-C`

Example:

```
(.venv) --> warnet run scenarios/reconnaissance.py --debug
...
Successfully deployed scenario commander: reconnaissance
Commander pod name: commander-reconnaissance-1727792531
initContainer in pod commander-reconnaissance-1727792531 is ready
Successfully copied data to commander-reconnaissance-1727792531(init):/shared/warnet.json
Successfully copied data to commander-reconnaissance-1727792531(init):/shared/archive.pyz
Successfully uploaded scenario data to commander: reconnaissance
Waiting for commander pod to start...
Reconnaissance Adding TestNode #0 from pod tank-0000 with IP 10.1.38.68
Reconnaissance Adding TestNode #1 from pod tank-0001 with IP 10.1.38.69
Reconnaissance Adding TestNode #2 from pod tank-0002 with IP 10.1.38.70
Reconnaissance Adding TestNode #3 from pod tank-0003 with IP 10.1.38.71
Reconnaissance Adding TestNode #4 from pod tank-0004 with IP 10.1.38.72
Reconnaissance Adding TestNode #5 from pod tank-0005 with IP 10.1.38.73
Reconnaissance Adding TestNode #6 from pod tank-0006 with IP 10.1.38.74
Reconnaissance Adding TestNode #7 from pod tank-0007 with IP 10.1.38.75
Reconnaissance Adding TestNode #8 from pod tank-0008 with IP 10.1.38.76
Reconnaissance Adding TestNode #9 from pod tank-0009 with IP 10.1.38.77
Reconnaissance Adding TestNode #10 from pod tank-0010 with IP 10.1.38.78
Reconnaissance Adding TestNode #11 from pod tank-0011 with IP 10.1.38.79
Reconnaissance User supplied random seed 131260415370612
Reconnaissance PRNG seed is: 131260415370612
Reconnaissance Getting peer info
Reconnaissance tank-0001 /Satoshi:27.0.0/
Reconnaissance tank-0002 /Satoshi:27.0.0/
Reconnaissance tank-0003 /Satoshi:27.0.0/
Reconnaissance tank-0005 /Satoshi:25.1.0/
Reconnaissance 10.1.38.75:59622 /Satoshi:0.21.1/
Reconnaissance tank-0006 /Satoshi:24.2.0/
Reconnaissance tank-0004 /Satoshi:26.0.0/
Reconnaissance 10.1.38.79:36980 /Satoshi:0.16.1/
Reconnaissance 10.1.38.76:40020 /Satoshi:0.20.0/
Reconnaissance tank-0010 /Satoshi:0.17.0/
Reconnaissance tank-0011 /Satoshi:0.16.1/
Reconnaissance Attacking 10.111.179.151:18444
Reconnaissance Got notfound message from 10.111.179.151:18444
Reconnaissance Stopping nodes
Reconnaissance Cleaning up /tmp/bitcoin_func_test_4zh_53n0 on exit
Reconnaissance Tests successful
Deleting pod...
pod "commander-reconnaissance-1727792531" deleted

```

## Rules of Engagement

An attack is considered successful when a target node is no longer in sync with
the most-work chain. This could be the result of:
- An eclipse attack
- An out-of-memory error killing the node process (the nodes are programmed not to restart)
- A CPU denial-of-service preventing the node from verifying new blocks

Attackers will not be able to generate their own blocks on the battlefield
Signet chain, but have unlimited permission on their local regtest networks.

## On The Battlefield

When you are ready to launch your attack for real, start by "switching context"
from your local cluster to the remote cluster. You will have a config file
provided by the administrator:

```
warnet auth /path/to/battlefield-100-large-kubeconfig.yaml
```

Good luck!
