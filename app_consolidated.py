# for streamlit code
import streamlit as st
from config import config
import requests
import pandas as pd
from collections import Counter
from urllib.parse import quote
import logging
from config import config
import aisuite as ai
import time
import os
import json

# --- FUNCTIONS.PY ---
# Helper function to read prompt files
def read_prompt_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Error reading prompt file {file_path}: {e}")
        return "Error loading prompt."
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
        "gl": "au",
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
        error_message = response.json().get('error', 'Unknown error occurred')
        logging.error(f"Error retrieving SerpAPI data: {error_message}")
        return error_message

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
        next((item['Competition'] for data in df['SEMRush_Data'] if data for item in data if item['Keyword'] == keyword), 0),
        keyword_counts[keyword])
        for keyword in final_keywords],
        columns=['Keyword', 'Search Volume', 'Competition', 'Frequency']
    )
    final_keywords_df = final_keywords_df.sort_values(by=['Frequency', 'Search Volume'], ascending=[False, False])

    logging.info("Successfully processed SEMRush data and extracted keywords.")
    return final_keywords_df

# --- Step 4: Content Fetching ---
# --- Jina Content Fetching (commented out) ---
# def fetch_content(url, jina_api_key):
#     headers = {
#         'Authorization': f'Bearer {jina_api_key}',
#         'X-Retain-Images': 'none',
#         "X-Return-Format": "application/json",
#         'X-Timeout': str(config["jina_api_timeout"])
#     }
#     try:
#         response = requests.get(f'https://r.jina.ai/{url}', headers=headers)
#         if handle_api_errors(response, "Jina AI Reader"):
#             response_json = response.json()
#             if response_json['code'] == 200:
#                 logging.info(f"Successfully fetched content from {url}.")
#                 return response_json['data']['content']
#             else:
#                 logging.warning(f"Jina API error for {url}: {response_json.get('error', 'Unknown error')}")
#                 return f"ERROR: {url} blocks Jina API or other error occurred."
#         else:
#             return f"ERROR: Failed to use Jina API for {url}."
#
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Request error fetching content from {url}: {e}")
#         return f"ERROR: Request failed for {url}."
#     except Exception as e:
#         logging.error(f"Unknown error fetching content from {url}: {e}")
#         return f"ERROR: Unknown error processing {url}."

# --- Step 4: Firecrawl Content Fetching ---
def fetch_content_firecrawl(url, firecrawl_api_key):
    payload = {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True,
        "mobile": False,
        "skipTlsVerification": False,
        "timeout": 30000,
        "removeBase64Images": True,
        "blockAds": True,
        "proxy": "basic",
    }
    headers = {
        "Authorization": f"Bearer {firecrawl_api_key}",
        "Content-Type": "application/json"
    }
    logging.info(f"Requesting Firecrawl API for URL: {url}")
    try:
        response = requests.post("https://api.firecrawl.dev/v1/scrape", json=payload, headers=headers)
        if handle_api_errors(response, "Firecrawl API"):
            response_json = response.json()
            logging.info(f"Successfully fetched content from {url} with Firecrawl.")
            return response_json["data"]["markdown"]
        else:
            return f"ERROR: Failed to use Firecrawl API for {url}."
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error fetching content from {url} with Firecrawl: {e}")
        return f"ERROR: Request failed for {url}."
    except Exception as e:
        logging.error(f"Unknown error processing {url} with Firecrawl: {e}")
        return f"ERROR: Unknown error processing {url}."

# --- Step 5-10: AI Model Interactions ---  
def interact_with_ai(messages, client, model=config["openai_model"], temperature=config["openai_temperature"]):
    try:
        response = client.chat.completions.create(
            model=model, 
            messages=messages, 
            temperature=temperature,
            )
        result = response.choices[0].message.content
        return result
    except Exception as e:
        logging.error(f"Error during AI interaction: {e}")
        return None
    
# --- CONTENT_GENERATION.PY---
# Analyze the content from top-ranking pages.
def generate_content_analysis(topic_query, df_results, client):
    system_prompt = read_prompt_file("prompts/content_analysis_system.txt")
    user_prompt = read_prompt_file("prompts/content_analysis_user.txt")
    
    # Format the content list to include both title and content
    content_list = []
    for i, (title, content) in enumerate(zip(df_results['Title'], df_results['Content'])):
        if content:
            content_list.append(f"SOURCE {i + 1}:\nTITLE: {title}\nCONTENT:\n{content}")
    
    formatted_content_list = "\n\n".join(content_list)
    
    # Format the user prompt with the actual values
    user_prompt = user_prompt.format(topic_query=topic_query, content_list=formatted_content_list)
    
    messages_content_analysis = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return interact_with_ai(messages_content_analysis, client)

# Create a detailed content plan based on analysis.
def generate_content_plan(topic_query, targeting_keywords, content_analysis, client):
    system_prompt = read_prompt_file("prompts/content_plan_system.txt")
    user_prompt = read_prompt_file("prompts/content_plan_user.txt")
    
    # Format the user prompt with the actual values
    user_prompt = user_prompt.format(
        topic_query=topic_query,
        targeting_keywords=targeting_keywords,
        content_analysis=content_analysis
    )
    
    messages_content_plan = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return interact_with_ai(messages_content_plan, client)

def generate_content_draft(content_plan, content_analysis, client):
    """Generate the first draft of the content."""
    system_prompt = read_prompt_file("prompts/content_draft_system.txt")
    user_prompt = read_prompt_file("prompts/content_draft_user.txt")
    
    # Format the user prompt with the actual values
    user_prompt = user_prompt.format(
        content_plan=content_plan,
        content_analysis=content_analysis
    )
    
    messages_content_draft = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return interact_with_ai(messages_content_draft, client)

def proofread_content(content_draft, content_plan, content_analysis, client):
    """Proofread and improve the content draft."""
    system_prompt = read_prompt_file("prompts/proofread_system.txt")
    user_prompt = read_prompt_file("prompts/proofread_user.txt")
    
    # Format the user prompt with the actual values
    user_prompt = user_prompt.format(
        content_draft=content_draft,
        content_plan=content_plan,
        content_analysis=content_analysis
    )
    
    messages_proofread = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return interact_with_ai(messages_proofread, client)

def generate_seo_recommendations(proofread_draft, targeting_keywords, client):
    """Generate SEO optimization recommendations."""
    system_prompt = read_prompt_file("prompts/seo_recommendations_system.txt")
    user_prompt = read_prompt_file("prompts/seo_recommendations_user.txt")
    
    # Format the user prompt with the actual values
    user_prompt = user_prompt.format(
        proofread_draft=proofread_draft,
        targeting_keywords=targeting_keywords
    )
    
    messages_seo = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return interact_with_ai(messages_seo, client)

def generate_final_deliverable(proofread_draft, seo_recommendations, targeting_keywords, df_serp, content_analysis, client, content_plan=None):
    """Compile the final content package with all components by direct concatenation."""
    # Create a final markdown document
    final_markdown = []
    
    # 1. Add the content plan
    if content_plan:
        final_markdown.append(content_plan)
        final_markdown.append("\n\n")
    
    # 2. Add the SEO recommendations
    final_markdown.append(seo_recommendations)
    final_markdown.append("\n\n")
    
    # 3. Add the SERP data in markdown format
    final_markdown.append("## Top Ranking Pages\n\n")
    # Convert DataFrame to markdown table
    serp_table = ["| Position | Title | Link |", "| -------- | ----- | ---- |"]
    for _, row in df_serp.iterrows():
        serp_table.append(f"| {row['Position']} | {row['Title']} | {row['Link']} |")
    final_markdown.append("\n".join(serp_table))
    final_markdown.append("\n\n")
    
    # 4. Add the SEMrush data in markdown format
    final_markdown.append("## Keyword Analysis\n\n")
    # Create a markdown table from the targeting keywords DataFrame
    keyword_table = ["| Keyword | Search Volume | Competition | Frequency |", "| ------- | ------------- | ----------- | --------- |"]
    for _, row in targeting_keywords.iterrows():
        keyword_table.append(f"| {row['Keyword']} | {row['Search Volume']} | {row['Competition']} | {row['Frequency']} |")
    final_markdown.append("\n".join(keyword_table))
    final_markdown.append("\n\n")
    
    # 5. Add the proofread content
    final_markdown.append(proofread_draft)
    
    # Return the concatenated markdown
    return "".join(final_markdown)

# --- Initialization ---
client = ai.Client()

def sidebar_config():
    st.sidebar.title("Configuration")
    
    # API Keys Section
    st.sidebar.header("API Keys")
    st.sidebar.caption("Secret keys are just a click away: https://tinyurl.com/darren-od. Talk to Darren if you need help getting access. ")
    api_keys = {
        'SERPAPI_KEY': st.sidebar.text_input("SerpAPI Key", type="password"),
        'SEMRUSH_API_KEY': st.sidebar.text_input("SEMrush API Key", type="password"),
        'FIRECRAWL_API_KEY': st.sidebar.text_input("Firecrawl API Key", type="password"),
        'OPENAI_API_KEY': st.sidebar.text_input("OpenAI API Key", type="password"),
        'ANTHROPIC_API_KEY': st.sidebar.text_input("Anthropic API Key", type="password"),
        # 'GOOGLE_API_KEY': st.sidebar.text_input("Google API Key", type="password")
    }
    
    # Model Selection
    st.sidebar.header("Model Settings")
    model = st.sidebar.selectbox(
        "Select AI Model",
        options=[
            "openai:gpt-4o-mini",
            "openai:gpt-4o",
            "openai:gpt-4.1",
            "openai:gpt-4.1-mini",
            "anthropic:claude-3-7-sonnet-20250219",
            # "google:gemini-2.5-flash-preview-04-17"
        ],
        index=0
    )
    
    # Database Selection
    st.sidebar.header("SEMrush Settings")
    database = st.sidebar.selectbox(
        "Select SEMrush Database",
        options=["au", "us", "nz", "sg"],
        index=0
    )
    
    return api_keys, model, database

# def load_api_keys():
#     st.session_state.SEMRUSH_API_KEY = st.secrets['SEMRUSH_API_KEY']
#     st.session_state.SERPAPI_KEY = st.secrets['SERPAPI_KEY']
#     st.session_state.OPENAI_API_KEY = st.secrets['OPENAI_API_KEY']
#     st.session_state.JINA_API_KEY = st.secrets['JINA_API_KEY']

def main():
    st.title("Overdose Content Research & Generation Agent")
    
    # Get configuration from sidebar
    api_keys, model, database = sidebar_config()

    # Update config
    config["openai_model"] = model
    config["semrush_database"] = database

    
    for key, value in api_keys.items():
        st.session_state[key] = value
    
    # Set environment variables for API keys
    os.environ['OPENAI_API_KEY'] = st.session_state.OPENAI_API_KEY
    os.environ['ANTHROPIC_API_KEY'] = st.session_state.ANTHROPIC_API_KEY
    # os.environ['GOOGLE_API_KEY'] = st.session_state.GOOGLE_API_KEY

    
    # Step 1: Topic Selection
    topic_query = st.text_input("Enter the topic you want to write about:")
    
    if topic_query:
        # Initialize session state for storing data
        if 'current_topic' not in st.session_state:
            st.session_state.current_topic = None
        if 'df_serp' not in st.session_state:
            st.session_state.df_serp = None
        if 'df_results' not in st.session_state:
            st.session_state.df_results = None
        if 'targeting_keywords' not in st.session_state:
            st.session_state.targeting_keywords = None
            
        # Only fetch new data if topic has changed
        if topic_query != st.session_state.current_topic:

            # Step 2: SERP Data
            with st.spinner("Fetching live SERP Data..."):
                time.sleep(1.5)
                st.session_state.df_serp = get_serpapi_data(topic_query, st.session_state.SERPAPI_KEY)
                if not st.session_state.df_serp.empty:
                    with st.expander(f"SERP Results of: ''{topic_query}''"):
                        st.dataframe(st.session_state.df_serp)
            
        # Step 3: SEMrush Data && Step 4: Content Retrieval
            st.session_state.df_results = st.session_state.df_serp.copy()
            
            with st.spinner("Fetching SEMRush Data..."):
                time.sleep(1.5)
                st.session_state.targeting_keywords = process_semrush_data(
                    st.session_state.df_results, 
                    st.session_state.SEMRUSH_API_KEY
                )
            
            contents = []
            for idx, link in enumerate(st.session_state.df_results['Link']):
                with st.spinner(f"Fetching content from link {idx + 1}/{len(st.session_state.df_results['Link'])}: {link}"):
                    contents.append(fetch_content_firecrawl(link, st.session_state.FIRECRAWL_API_KEY))
            st.session_state.df_results['Content'] = contents
            
            # Update current topic
            st.session_state.current_topic = topic_query

        
        # Display stored data
        with st.expander(f"🔍 Top Ranking Pages, Keyword Data & Page Content"):
            df_dict = st.session_state.df_results.to_dict('records')
            for item in df_dict:
                item['Content'] = [item['Content']]
            st.json(df_dict, expanded=False)
            # st.dataframe(st.session_state.df_results)
        
        with st.expander(f"📊 Data Analysis of Top Ranking Sites"):
            st.dataframe(st.session_state.targeting_keywords)


        
        # Steps 5-10: Content Generation
        if st.button("Generate Content"):
            with st.spinner("Analyzing content..."):
                content_analysis = generate_content_analysis(topic_query, st.session_state.df_results, client)
                with st.expander("🧐 Content Analysis"):
                    st.markdown(content_analysis)
            
            with st.spinner("Creating content plan..."):
                content_plan = generate_content_plan(topic_query, st.session_state.targeting_keywords, content_analysis, client)
                with st.expander("🗂️ Content Plan"):
                    st.markdown(content_plan)
            
            with st.spinner("Writing draft..."):
                content_draft = generate_content_draft(content_plan, content_analysis, client)
                with st.expander("✍️ Content Draft"):
                    st.markdown(content_draft)
            
            with st.spinner("Editorial review..."):
                proofread_draft = proofread_content(content_draft, content_plan, content_analysis, client)
                with st.expander("📝 Refined Article"):
                    st.markdown(proofread_draft)
            
            with st.spinner("Generating SEO recommendations..."):
                seo_recommendations = generate_seo_recommendations(proofread_draft, st.session_state.targeting_keywords, client)
                with st.expander("🤖 SEO Recommendations"):
                    st.markdown(seo_recommendations)
            
            with st.spinner("Preparing final deliverable..."):
                final_deliverable = generate_final_deliverable(
                    proofread_draft, seo_recommendations, st.session_state.targeting_keywords,
                    st.session_state.df_serp, content_analysis, client, content_plan
                )
                
                st.subheader("🎯 Final Deliverable")
                st.caption("Try copy/paste into https://markdownlivepreview.com/ if the output is not formatted properly.")
                st.divider()
                st.markdown(final_deliverable)

                # Add download button for the final deliverable
                st.download_button(
                    label="Download Markdown",
                    data=final_deliverable,
                    file_name=f"{topic_query.replace(' ', '_')}_content.md", # Generate filename
                    mime="text/markdown",
                )

if __name__ == "__main__":
    main()