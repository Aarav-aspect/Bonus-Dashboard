import sys
import pandas as pd
from backend import fetch_webfleet_drivers, fetch_optidrive_scores_bulk, fetch_service_resources, WEBFLEET_EMAIL_MAP

df_drivers = fetch_webfleet_drivers()
df_optidrive = fetch_optidrive_scores_bulk()
df_engineers = fetch_service_resources()

if df_optidrive.empty or df_drivers.empty or df_engineers.empty:
    print("One or more datasets are empty. Please check the API.")
    sys.exit(1)

df_optidrive["driverno_clean"] = df_optidrive["driverno"].astype(str).str.strip().str.lower()
df_drivers["driverno_clean"] = df_drivers["Driver No"].astype(str).str.strip().str.lower()

df_merged = df_optidrive.merge(
    df_drivers[["driverno_clean", "Email"]],
    on="driverno_clean",
    how="left",
)

df_merged["Email_Lower"] = df_merged["Email"].fillna("").astype(str).str.lower().str.strip()

df_merged["Mapped_Email"] = df_merged["Email_Lower"].map(
    lambda e: WEBFLEET_EMAIL_MAP.get(e, e)
)

df_engineers["Email_Lower"] = df_engineers["Email"].astype(str).str.lower().str.strip()

sf_emails = set(df_engineers["Email_Lower"].unique())
sf_emails.add("") # ignore empty emails

unmatched = df_merged[~df_merged["Mapped_Email"].isin(sf_emails)]
# drop duplicates based on driverno_clean
unmatched = unmatched.drop_duplicates(subset=["driverno_clean"])

print(f"Found {len(unmatched)} unmatched drivers out of {len(df_optidrive.drop_duplicates(subset=['driverno_clean']))}.")
for i, row in unmatched.iterrows():
    print(f"- Driver No: {row['driverno_clean']}, Webfleet Email: {row['Email']}, Tried mapping to: {row['Mapped_Email']}")
