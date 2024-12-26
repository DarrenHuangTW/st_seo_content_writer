# for streamlit code
import streamlit as st
from config import config
from archived.functions import (
    get_serpapi_data,
    process_semrush_data,
    fetch_content,
)
from archived.content_generation import (
    generate_content_analysis,
    generate_content_plan,
    generate_content_draft,
    proofread_content,
    generate_seo_recommendations,
    generate_final_deliverable
)
import aisuite as ai
import time

# --- Initialization ---
client = ai.Client()

def sidebar_config():
    st.sidebar.title("Configuration")
    
    # API Keys Section
    st.sidebar.header("API Keys")
    api_keys = {
        'SERPAPI_KEY': st.sidebar.text_input("SerpAPI Key", type="password"),
        'SEMRUSH_API_KEY': st.sidebar.text_input("SEMrush API Key", type="password"),
        'OPENAI_API_KEY': st.sidebar.text_input("OpenAI API Key", type="password"),
        'JINA_API_KEY': st.sidebar.text_input("Jina API Key", type="password")
    }
    
    # Model Selection
    st.sidebar.header("Model Settings")
    model = st.sidebar.selectbox(
        "Select OpenAI Model",
        options=["openai:gpt-4o-mini", "openai:gpt-4o"],
        index=0
    )
    
    # Database Selection
    st.sidebar.header("SEMrush Settings")
    database = st.sidebar.selectbox(
        "Select SEMrush Database",
        options=["us", "au", "nz"],
        index=0
    )
    
    return api_keys, model, database

# def load_api_keys():
#     st.session_state.SEMRUSH_API_KEY = st.secrets['SEMRUSH_API_KEY']
#     st.session_state.SERPAPI_KEY = st.secrets['SERPAPI_KEY']
#     st.session_state.OPENAI_API_KEY = st.secrets['OPENAI_API_KEY']
#     st.session_state.JINA_API_KEY = st.secrets['JINA_API_KEY']

def main():
    st.title("Content Generation Assistant")
    
    # Get configuration from sidebar
    api_keys, model, database = sidebar_config()

    # Update config
    config["openai_model"] = model
    config["semrush_database"] = database

    
    for key, value in api_keys.items():
        st.session_state[key] = value

    
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
            st.session_state.df_results = st.session_state.df_serp.copy().iloc[:2]
            
            with st.spinner("Fetching SEMRush Data..."):
                time.sleep(1.5)
                st.session_state.targeting_keywords = process_semrush_data(
                    st.session_state.df_results, 
                    st.session_state.SEMRUSH_API_KEY
                )
            
            contents = []
            for idx, link in enumerate(st.session_state.df_results['Link']):
                with st.spinner(f"Fetching content from link {idx + 1}/2: {link}"):
                    contents.append(fetch_content(link, st.session_state.JINA_API_KEY))
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
                    st.write(content_analysis)
            
            with st.spinner("Creating content plan..."):
                content_plan = generate_content_plan(topic_query, st.session_state.targeting_keywords, content_analysis, client)
                with st.expander("🗂️ Content Plan"):
                    st.write(content_plan)
            
            with st.spinner("Writing draft..."):
                content_draft = generate_content_draft(content_plan, content_analysis, client)
                with st.expander("✍️ Content Draft"):
                    st.write(content_draft)
            
            with st.spinner("Editorial review..."):
                proofread_draft = proofread_content(content_draft, content_plan, content_analysis, client)
                with st.expander("📝 Refined Article"):
                    st.write(proofread_draft)
            
            with st.spinner("Generating SEO recommendations..."):
                seo_recommendations = generate_seo_recommendations(proofread_draft, st.session_state.targeting_keywords, client)
                with st.expander("🤖 SEO Recommendations"):
                    st.write(seo_recommendations)
            
            with st.spinner("Preparing final deliverable..."):
                final_deliverable = generate_final_deliverable(
                    proofread_draft, seo_recommendations, st.session_state.targeting_keywords, 
                    st.session_state.df_serp, content_analysis, client
                )
                st.subheader("🎯 Final Deliverable")
                st.write(final_deliverable)

if __name__ == "__main__":
    main()