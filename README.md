# Warnet: The Battle of Galen Erso

![vulnerability](./images/vulnerability.gif)

Your mission is to attack Bitcoin Core nodes in a private network
running in a Kubernetes cluster. The private network consists of Bitcoin Core
nodes that are vulnerable to fully-disclosed historical attacks or novel
intentional flaws. A **FAKE** website with blog posts about all types of
vulnerabilities available for exploit on Warnet can be seen here:

https://bitcorncore.org/en/blog/

⚠️ This website is for entertainment purposes only ⚠️

## Terminology

- Tanks: Bitcoin Core nodes running in a Warnet network
- Armada: A small set of tanks running the latest Bitcoin Core release under the attacker's control
- Battlefield: A local or remote Kubernetes cluster with vulnerable tanks and armada nodes
    - `signet_large`:
        - The "real game", deployed by an admin to a large cluster
        - Over 100 tanks and 10 teams' armadas running on a private signet chain
    - `regtest_small`:
        - A miniature game you can run locally for testing
        - One team armada node with two vulnerable nodes running on regtest
- Scenario: A python script deployed by an attacker to a battlefield to attack tanks

## Objectives

1. Clone this repo
2. Install and set up Warnet
3. Create attacks
4. Test attacks locally (optional)
5. Attack Bitcoin Core nodes on the main battlefield

## What is Warnet?

Warnet is a system written in Python to deploy, manage, and interact with
Bitcoin p2p networks inside a Kubernetes cluster. The official battlefield
will be a remote cluster with over 100 Bitcoin nodes (referred to as "Tanks")
running on a custom signet chain (where only the network administrator can
generate blocks). Many of these nodes will be old versions of
Bitcoin Core with
[publicly disclosed vulnerabilities](https://bitcoincore.org/en/blog/). There will
also be additional nodes that have been compiled with intentional flaws and
[FAKE disclosures](https://bitcorncore.org/en/blog/)

To help facilitate Tank-attacking strategies on the battlefield, a smaller
regtest network can be run locally by attackers while
developing scenarios. Local deployment requires installing kubernetes (either
Docker Desktop or minikube) which is NOT required to run attacks on the remote
battlefield.

## Install and Set Up Warnet

1. Clone this directory
```
git clone https://github.com/bitcoin-dev-project/battle-of-galen-erso
cd battle-of-galen-erso
```

2. Create a python virtual environment
```
python -m venv .venv && source .venv/bin/activate
```

3. Install Warnet FROM PIP (NOT GITHUB)
```
pip install warnet
```

> [!WARNING]
> Make sure you installed Warnet correctly -- ONLY versions >= 1.1.18 will work.
> If you do not see the correct version, reinstall Warnet or ask for help.

```
$ warnet version
warnet version 1.1.18
```

4. Set up Warnet
This command will determine some options and then install Warnet's dependencies
into your local virtual environment. You must allow Warnet setup to install
kubectl and helm or already have them installed on your system.
```
warnet setup
```

> [!WARNING]
> If you plan on testing locally you will need Docker Desktop (MacOS) or Minikube (Linux).
> If you do NOT want to run a local cluster for testing, you can choose "No Backend"
> and connect directly to the remote cluster to enter the game, WITHOUT installing
> or running Docker Desktop or Minikube.

## Additional tools

### K9s

Whether you run Kubernetes locally or use the remote cluster, we recommend the
terminal user interface [k9s](https://github.com/derailed/k9s) to monitor
cluster status.

![k9s screenshot](./images/k9s-screenshot.png)

### ktop

If you want to observe resource usage on a cluster with metrics enabled, you
may want to consider using [ktop](https://github.com/vladimirvivien/ktop)

![ktop screenshot](./images/ktop-screenshot.png)

## Enter the game

The administrator will give everyone on your team a `kubeconfig` file which will
give your Warnet client access to small set of Bitcoin nodes.
You have full control over these nodes, they are your armada.
```
warnet auth /path/to/warnet-user-wargames-kubeconfig
```

> [!WARNING]
> Do not execute `warnet auth` if you plan to test locally.
> Read through the [local testing section](#local-testing) first.

If you are also running the local test environment you can switch back to your
original kubernetes context with the command:
```
warnet auth --revert
```

## Explore the network

You can open the network dashboard in a web browser:
```
warnet dashboard
```

You'll notice links to three services there:

### Grafana

From the Grafana landing page, select `Dashboards` and then `Battle of Galen Erso Dashboard`.
This dashboard displays metrics about the network including memory usage for target nodes.
This may helpful if you are attempting an OOM attack!

### Fork Observer

This interface indicates which nodes have fallen behind the chain tip or have
crashed entirely. It is also useful to look up which versions of Bitcoin Core
each target tank is running.

![fork observer screenshot](./images/fo.png)

### Leaderboard

A scoreboard display that aggregates data from Fork Observer and awards points to
teams when they succeed in crashing Bitcoin Core nodes.

## Attack!

> [!TIP]
> **On the battlefield, these commands will only be able to retrieve data from**
> **tanks in your armada. In local regtest mode, you will have access to all tanks.**

See the [Warnet documentation](https://github.com/bitcoin-dev-project/warnet/blob/main/docs/warnet.md)
for all available CLI commands to retrieve logs, p2p messages, and other status
information.

### Examples:
#### Status

```
(.venv) --> warnet status
╭────────────────────── Warnet Overview ───────────────────────╮
│                                                              │
│                        Warnet Status                         │
│ ┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━┓ │
│ ┃ Component ┃ Name                ┃ Status  ┃ Namespace    ┃ │
│ ┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━┩ │
│ │ Tank      │ armada-0            │ running │ wargames-red │ │
│ │ Tank      │ armada-1            │ running │ wargames-red │ │
│ │ Tank      │ armada-2            │ running │ wargames-red │ │
│ │ Scenario  │ No active scenarios │         │              │ │
│ └───────────┴─────────────────────┴─────────┴──────────────┘ │
│                                                              │
╰──────────────────────────────────────────────────────────────╯

Total Tanks: 3 | Active Scenarios: 0
Network connected
```

#### bitcoin-cli
```
(.venv) --> warnet bitcoin rpc armada-0 -getinfo
Chain: signet
Blocks: 0
Headers: 0
Verification progress: 100.0000%
Difficulty: 4.656542373906925e-10

Network: in 0, out 1, total 1
Version: 270000
Time offset (s): 0
Proxies: n/a
Min tx relay fee rate (BTC/kvB): 0.00001000

Warnings: (none)
```

## Ordinance

### Attack Development

The primary method of interacting with the network and mounting an attack is by
deploying a scenario.

A scenario is a Python script written with the same structure and library as
a Bitcoin Core functional test, utilizing a copy of the `test_framework`, which is
[included](/scenarios/test_framework) in this repo and may be modified if necessary.
The primary difference is that the familiar `self.nodes[]` list contains
references to containerized Bitcoin Core nodes running inside the
cluster rather than locally accessible bitcoind processes.

An additional list `self.tanks[str]` is available to address Bitcoin nodes
by their Kubernetes pod name (as opposed to their numerical index).

Objects in `self.nodes[]` and `self.tanks[]` are RPC proxy objects which interpret
all calls as RPC commands to be forwarded to the bitcoin core node.

Example:
```python
self.tanks["armada-0"].getpeerinfo()
```

If you are unfamiliar with the Bitcoin Core RPC interface you can get help directly
from a Bitcoin Core node:

```
(.venv) $ warnet bitcoin rpc armada-0 help
```

There are also several resources online to learn about the available RPC commands:

https://chainquery.com/bitcoin-cli

https://developer.bitcoin.org/reference/rpc/


**The only tanks you as an attacker have RPC access to are in your own armada**

A handful of example scenarios are included in the [`scenarios/`](/scenarios/) directory.
In particular, [`scenarios/reconnaissance.py`](/scenarios/reconnaissance.py) is written with verbose comments
to demonstrate how to execute RPC commands on available nodes, as well as how
to utilize the framework's `P2PInterface` class to send arbitrary messages
to targeted nodes.

Tanks in the kubernetes network have URIs that include a namespace. URIs for all
tanks can be seen in the "description" field in the fork-observer web UI.

Example:
```python
attacker = P2PInterface()
attacker.peer_connect(
    dstaddr=socket.gethostbyname("tank-0000-red.default.svc"),
    dstport=38333,
    net="signet",
    timeout_factor=1
)()
attacker.wait_until(lambda: attacker.is_connected, check_connected=False)

# Create a malicious p2p packet and send...
```

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

You can also query the scenario with `-- --help` to learn about its arguments.

Example:

```
(.venv) --> warnet run scenarios/miner_std.py -- --help
usage: warnet run /path/to/miner_std.py [options]

Generate blocks over time

options:
  -h, --help           show this help message and exit
  --allnodes           When true, generate blocks from all nodes instead of just nodes[0]
  --interval INTERVAL  Number of seconds between block generation (default 60 seconds)
  --mature             When true, generate 101 blocks ONCE per miner
  --tank TANK          Select one tank by name as the only miner
```

## Rules of Engagement

An attack is considered successful when a target node is no longer in sync with
the most-work chain. This could be the result of:
- An eclipse attack
- An out-of-memory error killing the node process (the nodes are programmed not to restart)
- A CPU denial-of-service preventing the node from verifying new blocks

Attackers will not be able to generate their own blocks on the battlefield
signet chain, but have unlimited permission on their local scrimmage signet network.

## Funds

On the battlefield, only the administrator can generate blocks. They will periodically
run a script that funds everyone's armada nodes with whatever spendable balance
the miner has. That script will ensure every armada node has a wallet called "armada".

> [!TIP]
> Your armada nodes will have a wallet called "armada" with lots of test BTC!

## HINTS

💡 Block interval in this game is 1 minute!

💡 You may be unfamiliar with the Bitcoin Core functional test framework. To get
some clues about its usage in p2p scenarios, review some of the existing tests!

Examples:
- [send `addr` messages](https://github.com/bitcoin/bitcoin/blob/28.x/test/functional/p2p_addrfetch.py)
- [create orphan transactions](https://github.com/bitcoin/bitcoin/blob/28.x/test/functional/p2p_orphan_handling.py)
- [send invalid blocks](https://github.com/bitcoin/bitcoin/blob/28.x/test/functional/p2p_invalid_block.py)

Also look at the stubbed and example scenarios in the `scenarios` directory for inspiration.

## Run your first attack

We will try to take down the 5k-inv node. To find out which node that is we can use 
forkobserver by using `warnet dashboard`.

On fork-observer, the "description" field will show what version of bitcoin is running. 
Find the 5k-inv node and update `scenarios/my_first_attack_5kinv.py` with the name of this node. 
Look for a variable called `victim`. On  Battlefield you will have been a color to attack 
and locally in Scrimmage there will only be red. The link "disclosing" this particular attack can be found:
[5K Inv Disclosure](https://bitcorncore.org/en/2024/10/23/fake-disclosure-5kinv/).

From the root of this repo, run this scenario with:

```
warnet run scenarios/my_first_attack_5kinv.py --debug
```

After the 5000 INVs have been sent, you should observe that this node becomes unresponsive on fork-observer.

## Local Testing

If you have Docker Desktop
[with Kubernetes enabled](https://docs.docker.com/desktop/features/kubernetes/)
or Minikube installed locally, you can deploy a single-team network on a regtest
chain, giving you full administrative control and the ability to interact with
the target nodes as well.


Deploy the local test network by running the included script:
```
./scripts/deploy.sh regtest_small
```

And then follow all the same directions above. This script will also generate
a new kubeconfig for the single team `aqua` for your local network which you can load
with:

```
warnet auth ./kubeconfigs/warnet-user-wargames-aqua-kubeconfig
```

To return to the admin position you must reset your kubernetes context with:
```
warnet auth --revert
```

Shut down the local network (from the admin position):
```
warnet down
```

> [!WARNING]
> Be careful you are not authorized to your team's actual armada on the battlefield!
> You may inadvertently shut down your own attacker nodes!

