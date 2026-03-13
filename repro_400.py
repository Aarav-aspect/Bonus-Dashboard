import requests
import json

url = "http://localhost:8000/config/thresholds/dynamic/Average%20Site%20Value%20(%C2%A3)?trade_group=Plumbing"
payload = {
    "thresholds": [1100, 1000, 900, 800, 700],
    "scores": [100, 90, 80, 70, 60]
}

print(f"Sending PUT to {url} ...")
try:
    resp = requests.put(url, json=payload)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
