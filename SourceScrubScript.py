import requests
import pandas as pd
import time
from dotenv import load_dotenv
import os

load_dotenv()

def get_sourcescrub_data_as_csv():
    username = os.getenv("SOURCESCRUB_USERNAME")
    password = os.getenv("SOURCESCRUB_PASSWORD")
    auth_url = "https://identity.sourcescrub.com/connect/token"

    auth_payload = {
        "grant_type": "password",
        "username": username,
        "password": password,
        "scope": "client_api"
    }

    auth_headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    auth_response = requests.post(auth_url, data=auth_payload, headers=auth_headers)

    if auth_response.status_code != 200:
        print(f"Authentication failed: {auth_response.status_code}")
        return

    token_data = auth_response.json()
    access_token = token_data["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    api_base_url = "https://api.sourcescrub.com"

    all_companies = []
    page = 1
    page_size = 100

    while True:
        print(f"Fetching page {page}...")

        endpoint = f"{api_base_url}/companies"
        params = {
            "page": page,
            "pageSize": page_size
        }

        response = requests.get(endpoint, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Failed to get data: {response.status_code}")
            break

        data = response.json()

        if "companies" in data and data["companies"]:
            all_companies.extend(data["companies"])

            if len(data["companies"]) < page_size:
                break

            page += 1

            time.sleep(0.5)
        else:
            break

    if all_companies:
        df = pd.DataFrame(all_companies)
        output_file = "sourcescrub_companies.csv"
        df.to_csv(output_file, index=False)
        print(f"Successfully saved {len(all_companies)} companies to {output_file}")
    else:
        print("No data retrieved")
