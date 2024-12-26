# Prompts
from functions import interact_with_ai

# Analyze the content from top-ranking pages.
def generate_content_analysis(topic_query, df_results, client):
    messages_content_analysis = [
        {
            "role": "system", 
            "content": """You are a meticulous content researcher with expertise in analyzing web content, particularly articles and blogs. You have access to a list of webpage contents related to the topic a user is interested in."""
        },
        {
            "role": "user", 
            "content": f"""Analyze the provided content below. 

        First, determine if each piece of content is a blog or an article. Exclude any content that is primarily promotional, youtube page, a forum post, or social media content. Focus on articles and blogs that provide informative or opinionated content.

        For each identified blog or article, add it to a review list. Then, thoroughly review each item on this list and provide an analysis that includes:

        (1) Common Topics:
            * Identify 3-5 main topics discussed across the content.
            * For each main topic, list 2-3 key subtopics or related concepts.
            * Provide a brief summary (1-2 sentences) of how each subtopic is addressed.

        (2) Contradicting Viewpoints:
            * Highlight contradicting viewpoints among the top results if there are any. 
            * Briefly explain the opposing arguments and any evidence presented.

        (3) Information Gaps:
            * Considering the user's search query '{topic_query}', identify key questions that a user might have that are NOT answered by the provided content, if there are any.
            * Suggest specific areas or subtopics that are missing from the content but would be relevant to someone interested in '{topic_query}, if there are any'.

        --------------------
        """ + "\n".join([f"SOURCE {i + 1}:\n{content}" for i, content in enumerate(df_results['Content']) if content])
        }
    ]
    return interact_with_ai(messages_content_analysis, client)

# Create a detailed content plan based on analysis.
def generate_content_plan(topic_query, targeting_keywords, content_analysis, client):
    messages_content_plan = [
        {
            "role": "system", 
            "content": """You are an expert content strategist skilled in crafting detailed and actionable content plans. You are adept at creating outlines that are clear, comprehensive, and tailored to the specific needs of a given topic. You have access to a detailed analysis of competitor content related to the topic a user is interested in."""
        },
        {
            "role": "user", 
            "content": f"""Develop a comprehensive content plan considering the content analysis provided below.

        Topic: 
        {topic_query}
        
        Target Keywords:
        {targeting_keywords}
        
        Content Analysis:
        {content_analysis}
        
        The content plan should include:

        (1) Outline: 
            * Create an outline with a hierarchical structure of headings and subheadings that logically organize the content.
            * The outline should have at least 3 main headings, with subheadings under each.

        (2) SEO Keywords:
            * Incorporate these SEO keywords: {targeting_keywords}. Prioritize them with Frequency (how many top ranking pages rank on the keyword) and Search Volume 
            * Ensure these keywords are naturally integrated into the headings and subheadings where relevant.

        (3) Content Strategy:
            * Address the common topics and subtopics identified in the content analysis.
            * Highlight any areas with contradicting viewpoints, and suggest a balanced approach to these topics.
            * Fill the information gaps identified in the analysis.
            * Suggest a unique angle or perspective for the content.
            """}
    ]
    return interact_with_ai(messages_content_plan, client)

def generate_content_draft(content_plan, content_analysis, client):
    """Generate the first draft of the content."""
    messages_content_draft = [
        {"role": "system", "content": """You are a skilled content writer specializing in crafting engaging, informative, and SEO-friendly blog posts. You excel at following detailed content plans and adapting your writing style to meet specific guidelines and objectives. You have access to a content plan and an analysis of competitor content related to the topic a user is interested in."""},
        {"role": "user", "content": f"""Write a comprehensive article using the provided Content Plan and the insights from the Competitor Content Analysis:
        
        Content Plan:
        {content_plan}
        
        Content Analysis:
        {content_analysis}
        
        Requirements:
        1. Follow the provided structure exactly
        2. Maintain a natural, engaging writing style
        3. Include relevant examples and explanations
        4. Integrate target keywords naturally
        5. Focus on providing unique value"""}
    ]
    return interact_with_ai(messages_content_draft, client)

def proofread_content(content_draft, content_plan, content_analysis, client):
    """Proofread and improve the content draft."""
    messages_proofread = [
        {"role": "system", "content": """You are an expert content editor with a keen eye for detail, specializing in refining and polishing written content. You excel at ensuring content is engaging, error-free, and adheres to SEO best practices. You have access to a draft article, its corresponding content plan, and an analysis of competitor content related to the topic a user is interested in."""},
        {"role": "user", "content": f"""Review and refine the provided Content Draft to ensure it aligns with the Content Plan and surpasses the quality of competitor content.
        
        Draft:
        {content_draft}
        
        Content Plan:
        {content_plan}

        Competitor Content Analysis:
        {content_analysis}
        
        Focus on the following:
        * Accuracy: Verify the accuracy of facts and claims (if possible).
        * Clarity and Conciseness: Ensure the writing is clear, concise, and free of jargon.
        * Engagement: Suggest ways to make the content more engaging (e.g., examples, anecdotes, varied sentence structures).
        * Flow and Structure: Ensure smooth transitions between paragraphs and sections.
        * Grammar and Mechanics: Correct any grammatical errors, typos, and punctuation issues.
        * SEO:
            * Ensure headings are properly used and optimized.
            * Check for keyword density and placement (avoid keyword stuffing).

        Please provide the revised article only, without any additional commentary or explanations. """}
    ]
    return interact_with_ai(messages_proofread, client)

def generate_seo_recommendations(proofread_draft, targeting_keywords, client):
    """Generate SEO optimization recommendations."""
    messages_seo = [
        {"role": "system", "content": """You are a seasoned SEO expert specializing in optimizing blog articles for search engines. You are adept at crafting compelling title tags and meta descriptions that improve click-through rates and accurately reflect the content. You have access to the final version of a blog article and a list of its targeting keywords related to the topic a user is interested in."""},
        {"role": "user", "content": f"""Develop SEO recommendations for the provided content.
        
        Content:
        {proofread_draft}
        
        Target Keywords (Prioritized by Frequency then Search Volume):
        {targeting_keywords}
        
        URL Slug:
        * Create an optimized URL slug for the article.
        * Use hyphens to separate words.
        * Include relevant keywords.

        Title Tag:
        * Generate three variations of a Title Tag following SEO best practices.
        * Accurately reflect the content of the article.
        * Include relevant keywords (naturally and if possible).

        Meta Description:
        * Create three variations of a Meta Description.
        * Provide a concise and accurate summary of the article's content.
        * Include a call to action (if relevant).
        * Use relevant keywords (naturally).

        Please provide only the URL slug, Title Tags, and Meta Descriptions, without any additional commentary or explanations.
        """}
    ]
    return interact_with_ai(messages_seo, client)

def generate_final_deliverable(proofread_draft, seo_recommendations, targeting_keywords, df_serp, content_analysis, client):
    """Compile the final content package with all components."""
    messages_final = [
        {"role": "system", "content": """You are a meticulous Senior Project Manager with expertise in presenting comprehensive project deliverables. You excel at organizing and summarizing complex information into a clear, concise, and client-ready format. You have access to all the outputs generated during a content creation process related to the topic a user is interested in."""},
        {"role": "user", "content": f"""Compile the following information into a well-structured Markdown document for client presentation.
        
        Content:
        {proofread_draft}
        
        SEO Recommendations:
        {seo_recommendations}
        
        Target Keywords:
        {targeting_keywords}

        Competitors:
        {df_serp[['Position', 'Link', 'Title']]} 
        
        Competitor Analysis:
        {content_analysis}
        
        The Markdown document should include:

        # [Content Title]

        ## SEO Recommendations

        ### Title & Meta Description
        * Present the SEO-optimized title and meta description options.
        * Highlight the chosen or recommended ones.
        * Include alternative options for consideration.
            * Use Markdown formatting for lists and emphasis (e.g., bold, italics).

        ### URL
        * Provide the finalized URL slug for the article.

        ## Keywords Analysis
        * List the primary keywords targeted in the content.
            * Only show up to 15 keywords, prioritized by Frequency first then Search Volume.
            * Use a Markdown table to present the keywords, search volume, and frequency.

        ## Competitors
        * Summarize key information about the top competitors.
            * Use a Markdown table with columns for "Position", "Link", and "Title".

        ## Content Strategy Notes
        * Offer insights into the content strategy.
        * Explain what aspects are covered.
        * Highlight unique points not addressed by competitors.
        * Mention areas that may require human validation or review.

        ## ===Final Content===
        * Present the fully proofread and polished article in a markdown format

        Ensure the deliverable is client-friendly, easy to understand, and provides a comprehensive overview of the project. Please provide the final deliverable document only, without any additional commentary or explanations. 
        """}
    ]
    return interact_with_ai(messages_final, client)