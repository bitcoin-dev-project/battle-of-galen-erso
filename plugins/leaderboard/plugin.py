#!/usr/bin/env python3

import json
import requests
import sys
from time import sleep
from pathlib import Path
from warnet.process import stream_command
from warnet.k8s import wait_for_ingress_controller, get_ingress_ip_or_host

assert sys.argv[1] == "entrypoint"
plugin_data = json.loads(sys.argv[2])

if __name__ == "__main__":
    command = f"helm upgrade --install leaderboard {Path(__file__).parent / 'charts' / 'leaderboard'}"
    for key in plugin_data.keys():
        command += f" --set {key}={plugin_data[key]}"
    stream_command(command)

    wait_for_ingress_controller()

    while True:
        try:
            ip = get_ingress_ip_or_host()
            url = f"http://{ip}/leaderboard/api/initialize"
            headers = {"x-auth-key": plugin_data["admin_key"]}
            resp = requests.post(url, headers=headers, data={})
            break
        except Exception:
            sleep(5)
