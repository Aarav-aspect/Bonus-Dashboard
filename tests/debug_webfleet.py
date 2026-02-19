
import requests
from requests.auth import HTTPBasicAuth
import toml

def debug_webfleet():
    try:
        with open("secrets.toml", "r") as f:
            secrets = toml.load(f)
            wf = secrets["webfleet"]
    except Exception as e:
        print(f"Error loading secrets: {e}")
        return

    params = {
        "action": "showDriverReportExtern",
        "account": wf["account"],
        "apikey": wf["apikey"],
        "lang": "en",
        "outputformat": "json",
        "useUTF8": "true",
        "useISO8601": "true",
    }
    
    base_url = "https://csv.webfleet.com/extern"
    
    print(f"Requesting Webfleet API: {base_url}")
    print(f"Params: {params}")
    print(f"Auth: user={wf['username']}, pass={wf['password']}")
    
    try:
        r = requests.get(
            base_url,
            params=params,
            auth=HTTPBasicAuth(wf["username"], wf["password"]),
            timeout=20,
        )
        print(f"Status Code: {r.status_code}")
        print(f"Response Content: {r.text[:500]}...") # Print first 500 chars
    except Exception as e:
        print(f"Request Error: {e}")

if __name__ == "__main__":
    debug_webfleet()
