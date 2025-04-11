import os;
from dotenv import load_dotenv
from simple_salesforce import Salesforce
import csv

load_dotenv()

def integrate_to_salesforce(csv_file_path):
    sf_username = os.getenv('SALESFORCE_USERNAME')
    sf_password = os.getenv('SALESFORCE_PASSWORD')
    sf_security_token = os.getenv('SALESFORCE_SECURITY_TOKEN')

    sf = Salesforce(username=sf_username, password=sf_password, security_token=sf_security_token)

    with open(csv_file_path, 'r') as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            account_data = {
                'Name': row['Company Name'],
                'Industry': row['Industry'],
                'Website': row['Website'],
                'Tier__c': row['Tier'],
                'BillingCity': row['City'],
                'BillingState': row['State'],
                'BillingCountry': row['Country']
            }

            try:
                result = sf.Account.upsert(f"Website/{account_data['Website']}", account_data)
                print(f"Upserted account: {account_data['Name']}")
            except Exception as e:
                print(f"Error upserting account {account_data['Name']}: {str(e)}")
