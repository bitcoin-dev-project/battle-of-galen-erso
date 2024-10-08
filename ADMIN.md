# Rough notes how to set this all up:

- `python scripts/fleet.py`:
    - generate network yaml's for battlefield and scrimmage (local dev) with random rpc passwords
    - battlefield has all 10 teams @ all vuln versions (13 currently)
    - scrimmage has just 1 team x 13 vuln nodes
- `warnet deploy namespaces/armies`:
    - deploys 13 team namespaces
    - can be used locally or remotely for either network, but locally only "red" is used
- `warnet admin create-kubeconfigs`
    - Generates config files with TTL of 2 days
    - dont bother saving or committing these to github

## For remote battlefield admin:

- `warnet deploy networks/battlefield`
    - as the admin for your cluster with namespace `"default"`, deploy the network

- `warnet deploy networks/armada --to-all-users`
    - deploys a 3-tank (v27) armada in each users' namespace, connected to `miner.default`

- `bash scripts/miner_wallet.sh`
    - creates wallet in "miner" tank and imports signet signer key as descriptor

- `warnet run scenarios/signet_miner.py --tank=0 generate  --min-nbits --address=tb1qsre7e4ls9z3kh8hn0gqtvds33desz6768cuag8 --ongoing --debug`
    - starts mining blocks. Get a new address first!

## For local scrimmage:

- `warnet deploy networks/scrimmage`
    - as the admin for your cluster with namespace `"default"`, deploy the network

- `warnet auth kubeconfigs/warnet-user-wargames-red-kubeconfig`
- `warnet deploy networks/armada`
    - deploys a 3-tank (v27) armada in ONE users' namespace, connected to `miner.default`

# Admin

```
(.venv) --> warnet status
╭──────────────────────── Warnet Overview ────────────────────────╮
│                                                                 │
│                          Warnet Status                          │
│ ┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓ │
│ ┃ Component ┃ Name                ┃ Status  ┃ Namespace       ┃ │
│ ┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩ │
│ │ Tank      │ miner               │ running │ default         │ │
│ │ Tank      │ tank-0000-red       │ running │ default         │ │
│ │ Tank      │ tank-0001-red       │ running │ default         │ │
│ │ Tank      │ tank-0002-red       │ running │ default         │ │
│ │ Tank      │ tank-0003-red       │ running │ default         │ │
│ │ Tank      │ tank-0004-red       │ running │ default         │ │
│ │ Tank      │ tank-0005-red       │ running │ default         │ │
│ │ Tank      │ tank-0006-red       │ running │ default         │ │
│ │ Tank      │ tank-0007-red       │ running │ default         │ │
│ │ Tank      │ tank-0008-red       │ running │ default         │ │
│ │ Tank      │ tank-0009-red       │ running │ default         │ │
│ │ Tank      │ tank-0010-red       │ running │ default         │ │
│ │ Tank      │ tank-0011-red       │ running │ default         │ │
│ │ Tank      │ tank-0012-red       │ running │ default         │ │
│ │ Tank      │ armada-0            │ running │ wargames-black  │ │
│ │ Tank      │ armada-1            │ running │ wargames-black  │ │
│ │ Tank      │ armada-2            │ running │ wargames-black  │ │
│ │ Tank      │ armada-0            │ running │ wargames-blue   │ │
│ │ Tank      │ armada-1            │ running │ wargames-blue   │ │
│ │ Tank      │ armada-2            │ running │ wargames-blue   │ │
│ │ Tank      │ armada-0            │ running │ wargames-brown  │ │
│ │ Tank      │ armada-1            │ running │ wargames-brown  │ │
│ │ Tank      │ armada-2            │ running │ wargames-brown  │ │
│ │ Tank      │ armada-0            │ running │ wargames-green  │ │
│ │ Tank      │ armada-1            │ running │ wargames-green  │ │
│ │ Tank      │ armada-2            │ running │ wargames-green  │ │
│ │ Tank      │ armada-0            │ running │ wargames-grey   │ │
│ │ Tank      │ armada-1            │ running │ wargames-grey   │ │
│ │ Tank      │ armada-2            │ running │ wargames-grey   │ │
│ │ Tank      │ armada-0            │ running │ wargames-orange │ │
│ │ Tank      │ armada-1            │ running │ wargames-orange │ │
│ │ Tank      │ armada-2            │ running │ wargames-orange │ │
│ │ Tank      │ armada-0            │ running │ wargames-red    │ │
│ │ Tank      │ armada-1            │ running │ wargames-red    │ │
│ │ Tank      │ armada-2            │ running │ wargames-red    │ │
│ │ Tank      │ armada-0            │ running │ wargames-violet │ │
│ │ Tank      │ armada-1            │ running │ wargames-violet │ │
│ │ Tank      │ armada-2            │ running │ wargames-violet │ │
│ │ Tank      │ armada-0            │ running │ wargames-white  │ │
│ │ Tank      │ armada-1            │ running │ wargames-white  │ │
│ │ Tank      │ armada-2            │ running │ wargames-white  │ │
│ │ Tank      │ armada-0            │ running │ wargames-yellow │ │
│ │ Tank      │ armada-1            │ running │ wargames-yellow │ │
│ │ Tank      │ armada-2            │ running │ wargames-yellow │ │
│ │ Scenario  │ No active scenarios │         │                 │ │
│ └───────────┴─────────────────────┴─────────┴─────────────────┘ │
│                                                                 │
╰─────────────────────────────────────────────────────────────────╯

Total Tanks: 44 | Active Scenarios: 0
Network connected                                                       
```

# User

```
(.venv) --> warnet auth kubeconfigs/warnet-user-wargames-red-kubeconfig 
Authorization file written to: /Users/matthewzipkin/.kube/config

warnet's current context is now set to: warnet-user-wargames-red
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
(.venv) --> 

```