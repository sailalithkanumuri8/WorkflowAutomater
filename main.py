import openai
import requests
from bs4 import BeautifulSoup

# Set your OpenAI API key
openai.api_key = "sk-proj-FTTMB7yUuGY23El1xv4YT3BlbkFJgfs6YoYZsILqFVUQlkyJ"


def scrape_website_text(url, max_chars=3000):
    """
    Fetches the content of a website and returns a cleaned text version.
    Optionally limits the text to max_chars to avoid overloading the prompt.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for bad responses
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

    # Parse the webpage using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    # Remove scripts and styles
    for script in soup(["script", "style"]):
        script.decompose()

    text = soup.get_text(separator=" ", strip=True)
    # Limit text length to avoid large prompts
    if len(text) > max_chars:
        text = text[:max_chars]
    return text


def classify_company_website(url):
    """
    Classifies a company website by extracting its industry, sector, and subsector using GPT‑4.
    """
    website_text = scrape_website_text(url)
    if not website_text:
        return "No content fetched from the URL."

    # Create a prompt for GPT‑4 that explains what you need.
    prompt = (
        "Given the following website content from a company, please provide the industry, sector, and subsector. "
        "If any of these cannot be determined, please indicate 'Not available'. "
        "Respond in the following JSON format:\n\n"
        "{\n  \"industry\": \"...\",\n  \"sector\": \"...\",\n  \"subsector\": \"...\"\n}\n\n"
        "Website Content:\n"
        f"\"{website_text}\"\n\n"
        "Please analyze the text carefully and extract the most relevant classifications."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant that specializes in classifying companies by industry, sector, and subsector."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2  # lower temperature for more consistent output
        )
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None

    answer = response["choices"][0]["message"]["content"]
    return answer


if __name__ == "__main__":
    url = input("Enter the company website URL: ").strip()
    classification = classify_company_website(url)
    print("Classification Output:")
    print(classification)