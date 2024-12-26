# for all functionsimport aisuite as ai
import requests
import pandas as pd
from collections import Counter
from urllib.parse import quote
import logging
from config import config


SEMRUSH_API_KEY = "PLACEHOLDER"

# --- Helper Functions ---
def handle_api_errors(response, api_name):
    if response.status_code != 200:
        logging.error(f"Failed to retrieve data from {api_name}. Status code: {response.status_code}")
        return False
    return True

# --- Step 2: SerpAPI Data Retrieval ---
def get_serpapi_data(topic_query, SERPAPI_KEY):
    base_url = "https://serpapi.com/search.json"
    params = {
        "q": topic_query,
        "hl": "en",
        "gl": "us",
        "google_domain": "google.com",
        "api_key": SERPAPI_KEY
    }
    response = requests.get(base_url, params=params)
    if handle_api_errors(response, "SerpAPI"):
        results = response.json()
        data = []
        for result in results.get('organic_results', []):
            data.append({
                'Position': result.get('position'),
                'Link': result.get('link'),
                'Title': result.get('title')
            })
        df_serp = pd.DataFrame(data)
        logging.info("Successfully retrieved SerpAPI data.")
        return df_serp
    else:
        return pd.DataFrame()

# --- Step 3: SEMRush Data Retrieval and Processing ---
def get_semrush_data(url, api_key):
    if not api_key:
        logging.error("SEMRush API key is missing")
        return []
        
    base_url = "https://api.semrush.com/"
    type_param = "url_organic"
    export_columns = "Ph,Po,Nq,Cp,Co"
    
    try:
        full_url = (
            f"{base_url}?type={type_param}&key={api_key}"
            f"&display_limit={config['semrush_display_limit']}&export_columns={export_columns}"
            f"&url={quote(url)}&database={config['semrush_database']}"
            f"&display_filter={config['semrush_display_filter']}&display_sort={config['semrush_display_sort']}"
        )
        response = requests.get(full_url)
        
        if response.status_code == 403:
            logging.error("SEMRush API authentication failed. Please check your API key.")
            return []
        elif not handle_api_errors(response, "SEMRush"):
            return []
            
        decoded_output = response.content.decode('utf-8')
        lines = decoded_output.split('\r\n')
        headers = lines[0].split(';')
        json_data = []
        for line in lines[1:]:
            if line:
                values = line.split(';')
                record = {header: value for header, value in zip(headers, values)}
                json_data.append(record)
        return json_data
        
    except Exception as e:
        logging.error(f"Error in SEMRush API call: {str(e)}")
        return []

def process_semrush_data(df, api_key):
    df['SEMRush_Data'] = df['Link'].apply(lambda x: get_semrush_data(x, api_key))
    logging.info("Successfully retrieved SEMRush data.")
    all_keywords = []
    for data in df['SEMRush_Data']:
        if data:
            all_keywords.extend([item['Keyword'] for item in data])

    keyword_counts = Counter(all_keywords)
    highest_count = max(keyword_counts.values())
    second_highest_count = sorted(set(keyword_counts.values()), reverse=True)[1] if len(set(keyword_counts.values())) > 1 else 0
    top_keywords = [keyword for keyword, count in keyword_counts.items() if count == highest_count or count == second_highest_count]

    if highest_count == 2:
        top_keywords = [keyword for keyword, count in keyword_counts.items() if count in [1, 2]]

    search_volume_keywords = sorted(
        [(item['Keyword'], int(item['Search Volume'])) for data in df['SEMRush_Data'] if data for item in data],
        key=lambda x: x[1],
        reverse=True)[:10]

    final_keywords = set(top_keywords + [keyword for keyword, _ in search_volume_keywords])
    final_keywords_df = pd.DataFrame(
        [(keyword, 
        next((item['Search Volume'] for data in df['SEMRush_Data'] if data for item in data if item['Keyword'] == keyword), 0),
        keyword_counts[keyword])
        for keyword in final_keywords],
        columns=['Keyword', 'Search Volume', 'Frequency']
    )
    final_keywords_df = final_keywords_df.sort_values(by=['Frequency', 'Search Volume'], ascending=[False, False])

    logging.info("Successfully processed SEMRush data and extracted keywords.")
    return final_keywords_df


# --- Step 4: Content Fetching ---
def fetch_content(url, jina_api_key):
    print(f"working on: {url}")
    headers = {
        'Authorization': f'Bearer {jina_api_key}',
        'X-Retain-Images': 'none',
        "Accept": "application/json",
        'X-Timeout': str(config["jina_api_timeout"])
    }
    try:
        response = requests.get(f'https://r.jina.ai/{url}', headers=headers)
        if handle_api_errors(response, "Jina AI Reader"):
            response_json = response.json()
            if response_json['code'] == 200:
                logging.info(f"Successfully fetched content from {url}.")
                return response_json['data']['content']
            else:
                logging.warning(f"Jina API error for {url}: {response_json.get('error', 'Unknown error')}")
                return f"ERROR: {url} blocks Jina API or other error occurred."
        else:
            return f"ERROR: Failed to use Jina API for {url}."

    except requests.exceptions.RequestException as e:
        logging.error(f"Request error fetching content from {url}: {e}")
        return f"ERROR: Request failed for {url}."
    except Exception as e:
        logging.error(f"Unknown error fetching content from {url}: {e}")
        return f"ERROR: Unknown error processing {url}."

# --- Step 5-10: AI Model Interactions ---  
def interact_with_ai(messages, client, model=config["openai_model"], temperature=config["openai_temperature"]):
    try:
        response = client.chat.completions.create(model=model, messages=messages, temperature=temperature)
        result = response.choices[0].message.content
        return result
    except Exception as e:
        logging.error(f"Error during AI interaction: {e}")
        return None