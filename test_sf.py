import os
import sys
from simple_salesforce import Salesforce
import json
from dotenv import load_dotenv

load_dotenv()

sf = Salesforce(
    username=os.environ["SF_USERNAME"],
    password=os.environ["SF_PASSWORD"],
    security_token=os.environ["SF_SECURITY_TOKEN"],
    domain="login"
)

res = sf.query("SELECT Id, asp04__Amount__c, Customer_Invoice__r.Trade_Group_lookup__c FROM asp04__Payment__c WHERE asp04__Payment_Date__c = THIS_MONTH LIMIT 5")
print(json.dumps(res, indent=2))
