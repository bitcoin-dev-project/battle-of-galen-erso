#!/usr/bin/env python3

import json
import os
import requests
from pathlib import Path
from warnet.k8s import wait_for_ingress_controller, get_ingress_ip_or_host

wait_for_ingress_controller()
ip = get_ingress_ip_or_host()

dashboard_file = Path(os.path.dirname(__file__)) / '..' / 'dashboards' / 'battle-dashboard.json'
url = f"http://{ip}/grafana/api/dashboards/db"
auth = ("admin", "password")
headers = {"Content-Type": "application/json"}

with open(dashboard_file) as f:
    data = json.load(f)

payload = {
    "dashboard": data,
    "overwrite": True
}

resp = requests.post(url, headers=headers, auth=auth, data=json.dumps(payload))
print(resp.status_code, resp.text)
