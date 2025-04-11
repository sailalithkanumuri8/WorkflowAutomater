import openai
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse
import os
from dotenv import load_dotenv
from SourceScrubScript import get_sourcescrub_data_as_csv
from SalesForceUploadScript import integrate_to_salesforce

load_dotenv()
openai.api_key = os.getenv('OPEN_AI_API_KEY')

def fetch_website_text(url):
    try:
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        for element in soup(["script", "style", "nav", "footer"]):
            element.decompose()

        text = soup.get_text(separator=' ', strip=True)
        return ' '.join(text.split())[:8000]
    except Exception as e:
        return f"Error: {str(e)}"


def get_industry_info(website_text):
    prompt = f"""Analyze this website content and return:
    1. Primary industry
    2. Business sector
    3. Specific subsector

    Format strictly as:
    Industry: [value]
    Sector: [value]
    Subsector: [value]

    Content: {website_text[:6000]}"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"API Error: {str(e)}"


def determine_investment_tier(industry_data, website_text):
    prompt = f"""Evaluate this company's investment potential using:
    - Industry: {industry_data.get('Industry', 'N/A')}
    - Sector: {industry_data.get('Sector', 'N/A')}
    - Sub Sector: {industry_data.get('Sub Sector', 'N/A')}
    - Company Profile: {website_text[:3000]}

    Assessment Criteria:
    1. Market Growth (High/Medium/Low)
    2. Competitive Position (Leader/Established/Niche)
    3. Regulatory Risk (Low/Medium/High)
    4. Tech Advantage (Strong/Moderate/Weak)

    Return ONLY the tier number (1, 2, or 3) based on:
    1 = Strong potential
    2 = Moderate potential
    3 = High risk"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print(f"Tier API Error: {str(e)}")
        return "Error"


def process_company_data(row):
    result = {'Industry': None, 'Sector': None, 'Sub Sector': None, 'Tier': None}
    try:
        website_text = fetch_website_text(row['Website'])
        print(f"Fetched website text for {row['Website']}: {website_text[:100]}...")

        if pd.isna(row['Industry']):
            industry_response = get_industry_info(website_text)
            print(f"Industry response: {industry_response}")

            if "Industry:" in industry_response:
                for line in industry_response.split('\n'):
                    if 'Industry:' in line:
                        result['Industry'] = line.split(': ')[1].strip()
                    elif 'Sector:' in line:
                        result['Sector'] = line.split(': ')[1].strip()
                    elif 'Sub Sector:' in line:
                        result['Sub Sector'] = line.split(': ')[1].strip()

        if pd.isna(row['Tier']) or str(row['Tier']) not in {'1', '2', '3'}:
            industry_data = {
                'Industry': result['Industry'] or row['Industry'],
                'Sector': result['Sector'] or row['Sector'],
                'Sub Sector': result['Sub Sector'] or row['Sub Sector']
            }
            tier = determine_investment_tier(industry_data, website_text)
            print(f"Tier response: {tier}")
            result['Tier'] = tier if tier in {'1', '2', '3'} else '3'

    except Exception as e:
        print(f"Processing error for {row['Website']}: {str(e)}")

    return result


def update_csv_with_industry_info(file_path, target_companies):
    header_row = 0
    with open(file_path, 'r', encoding='latin1') as f:
        for i, line in enumerate(f):
            if "Company Name" in line and ("Tier" in line) and ("Industry" in line):
                header_row = i
                break

    df = pd.read_csv(file_path, skiprows=header_row, encoding='latin1')
    df.columns = [col.strip() for col in df.columns]

    print("Columns in DataFrame:", df.columns.tolist())

    if 'URL' in df.columns and 'Website' not in df.columns:
        df['Website'] = df['URL']

    required_cols = ['Company Name', 'Website', 'Industry', 'Sector', 'Sub Sector', 'Tier']
    for col in required_cols:
        if col not in df.columns:
            df[col] = None

    target_df = df[df['Company Name'].isin(target_companies)]
    print(f"Found {len(target_df)} target companies to process")

    if len(target_df) == 0:
        print("No target companies found in the CSV file. Check company names.")
        return

    for index, row in target_df.iterrows():
        if pd.isna(row['Website']) or not urlparse(row['Website']).scheme:
            print(f"Skipping {row['Company Name']} - Invalid or missing website URL")
            continue

        print(f"\nProcessing {row['Company Name']}: {row['Website']}")
        processed_data = process_company_data(row)

        for col in ['Industry', 'Sector', 'Sub Sector', 'Tier']:
            csv_col = 'Sub Sector' if col == 'Sub Sector' else col
            if processed_data[col] and pd.isna(row[csv_col]):
                print(f"Updating {csv_col} for {row['Company Name']}: {processed_data[col]}")
                df.at[index, csv_col] = float(processed_data[col]) if processed_data[col] and processed_data[col].isdigit() else processed_data[col]

        df.to_csv('Intermediate_Results.csv', index=False)

        time.sleep(5)

    print("\nProcessed data for target companies:")
    print(target_df)

    output_path = file_path.replace('.csv', '_processed.csv')
    df.to_csv(output_path, index=False)
    print(f"\n✅ Processing complete. Saved to {output_path}")

if __name__ == '__main__':
    # get_sourcescrub_data_as_csv()
    target_companies = [
        "Boyette Electric Inc",
        "GREATMARK INVESTMENT PARTNERS INC",
        "G-Force Manufacturing"
    ]
    update_csv_with_industry_info("Testing.csv", target_companies)
    # integrate_to_salesforce("Intermediate_Results.csv")