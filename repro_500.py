import requests
import json

# Repro for the 500 Error when saving from Grid
url = "http://localhost:8000/config/thresholds/dynamic/Average%20Site%20Value%20(%C2%A3)?trade_group=Drainage"
payload = {
    "thresholds": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "scores": [100.0, 90.0, 80.0, 70.0, 60.0, 50.0, 40.0, 30.0, 20.0, 10.0]
}

print(f"Sending PUT to {url} ...")
try:
    # Need to simulate the authentication if the endpoint requires it
    # We will assume a Dev login first to get a token
    dev_url = "http://localhost:8000/api/auth/dev/login"
    session = requests.Session()
    session.post(dev_url, json={"role": "admin"})

    resp = session.put(url, json=payload)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
