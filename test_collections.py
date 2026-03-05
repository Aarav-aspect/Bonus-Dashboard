import sys
from backend import sf_client
import json

sf = sf_client()
try:
    q = "SELECT SUM(Customer_Invoice__r.Job__r.Cost_Materials_Total__c) materials FROM asp04__Payment__c WHERE asp04__Payment_Date__c = THIS_MONTH"
    print(f"Executing: {q}")
    res = sf.query(q)
    print(json.dumps(res, indent=2))
except Exception as e:
    print(e)
