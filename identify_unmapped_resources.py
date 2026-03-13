import pandas as pd
from backend import fetch_service_resources
from mapping import get_region_for_trade

def identify_unmapped():
    print("Fetching active service resources...")
    df = fetch_service_resources()
    if df.empty:
        print("No resources found.")
        return

    unmapped = []
    
    for _, row in df.iterrows():
        name = row.get("Engineer Name", "Unknown")
        trade_group = row.get("Trade Group", "Unknown")
        trade = row.get("Trade_Lookup__c", "Unknown")
        pc = row.get("Residential_PostalCode__c", "")
        
        # Check if missing
        if not pc or str(pc).strip() == "" or str(pc).lower() == "nan":
            unmapped.append({
                "Name": name,
                "Trade Group": trade_group,
                "Trade": trade,
                "Postal Code": "MISSING",
                "Reason": "Empty Postal Code"
            })
            continue
            
        # Check if "Other" or unmappable
        region = get_region_for_trade(pc, trade_group)
        if region in ["Other", "Leads Without Postcode"]:
            unmapped.append({
                "Name": name,
                "Trade Group": trade_group,
                "Trade": trade,
                "Postal Code": pc,
                "Reason": f"Unmapped ({region})"
            })

    if not unmapped:
        print("All resources are correctly mapped!")
        return

    df_unmapped = pd.DataFrame(unmapped)
    
    # Save to CSV for the user
    df_unmapped.to_csv("unmapped_resources.csv", index=False)
    
    print(f"\nFound {len(unmapped)} unmapped resources.")
    print("\nSummary of Reasons:")
    print(df_unmapped["Reason"].value_counts() if hasattr(df_unmapped["Reason"], "value_counts") else df_unmapped.groupby("Reason").size())
    
    print("\nFirst 20 unmapped resources:")
    print(df_unmapped.head(20).to_string(index=False))
    print("\nFull list saved to: unmapped_resources.csv")

if __name__ == "__main__":
    identify_unmapped()
