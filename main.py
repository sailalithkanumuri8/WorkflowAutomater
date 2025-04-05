import openai
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

# Set your OpenAI API key
openai.api_key = "sk-proj-FTTMB7yUuGY23El1xv4YT3BlbkFJgfs6YoYZsILqFVUQlkyJ"


def fetch_website_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator=' ')
        return ' '.join(text.split())[:8000]  # Trim to 8K characters
    except Exception as e:
        return f"Error: {str(e)}"


def get_industry_info(website_text):
    prompt = f"""
You are a business classification assistant. Based on the website content below, identify the following:

1. Industry
2. Sector
3. Subsector

Format the output exactly like this:
Industry: ...
Sector: ...
Subsector: ...

Website content:
\"\"\"
{website_text}
\"\"\"
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"Error: {str(e)}"


def update_csv_with_industry_info(file_path):
    # Skip the first 5 rows which contain metadata
    # Look for the actual header row that contains "Company", "Tier", etc.
    header_row = None

    with open(file_path, 'r', encoding='latin1') as f:
        for i, line in enumerate(f):
            if "Company,Tier,Industry,Sector,Sub-Sector" in line:
                header_row = i
                break

    if header_row is None:
        print("Could not find the header row in the file")
        return

    # Read the CSV file starting from the header row
    df = pd.read_csv(file_path, skiprows=header_row, encoding='latin1')

    # Print the first few rows to verify
    print("First few rows of the dataframe:")
    print(df.head())

    # Clean up column names (remove whitespace)
    df.columns = [col.strip() for col in df.columns]

    # Create a new output dataframe with only the columns we need
    output_df = pd.DataFrame()

    # Map the important columns
    important_columns = ['Company', 'URL', 'Industry', 'Sector', 'Sub-Sector']
    for col in important_columns:
        if col in df.columns:
            output_df[col] = df[col]
        else:
            print(f"Warning: Column '{col}' not found in the dataframe")
            output_df[col] = None

    # Rename Sub-Sector to Subsector for consistency
    if 'Sub-Sector' in output_df.columns:
        output_df = output_df.rename(columns={'Sub-Sector': 'Subsector'})

    # Process each row
    for index, row in output_df.iterrows():
        if pd.isna(row['Industry']) or pd.isna(row['Sector']) or pd.isna(row['Subsector']):
            if pd.isna(row['URL']) or not isinstance(row['URL'], str):
                print(f"Skipping row {index}: No valid URL provided")
                continue

            print(f"Processing {row['URL']}...")
            website_text = fetch_website_text(row['URL'])

            if website_text.startswith("Error"):
                print(website_text)
                continue

            result = get_industry_info(website_text)
            print(result)

            if not result.startswith("Error"):
                lines = result.splitlines()
                for line in lines:
                    if "Industry:" in line:
                        output_df.at[index, 'Industry'] = line.replace("Industry:", "").strip()
                    elif "Sector:" in line:
                        output_df.at[index, 'Sector'] = line.replace("Sector:", "").strip()
                    elif "Subsector:" in line:
                        output_df.at[index, 'Subsector'] = line.replace("Subsector:", "").strip()
            time.sleep(3)  # Be polite to OpenAI's API rate limits

    # Save to a new file
    output_path = file_path.replace('.csv', '_processed.csv')
    output_df.to_csv(output_path, index=False)
    print(f"\n✅ Updated CSV saved: {output_path}")


# Run the function
update_csv_with_industry_info("Training.csv")