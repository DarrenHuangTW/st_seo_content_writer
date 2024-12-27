# SEO Content Writer

An AI-powered content research and generation tool that helps create SEO-optimized articles based on competitor analysis and keyword research.

![Demo Video](static/seo_content_writer.mp4)

## Features

- SERP Analysis
- Keyword Research
- Competitor Content Analysis
- AI-Powered Content Generation
- SEO Optimization
- Automated Content Refinement

## Required API Keys

To use this application, you'll need the following API keys:

1. **SerpAPI Key** - For retrieving search engine results
   - Get it from: [SerpAPI](https://serpapi.com/)
   - Used in: Search results retrieval

2. **SEMrush API Key** - For keyword research and competitor analysis
   - Get it from: [SEMrush](https://www.semrush.com/api-documentation/)
   - Used in: Keyword data extraction

3. **OpenAI API Key** - For AI-powered content generation
   - Get it from: [OpenAI](https://platform.openai.com/)
   - Used in: Content analysis and generation

4. **Jina AI API Key** - For web content extraction
   - Get it from: [Jina AI](https://jina.ai/)
   - Used in: Competitor content extraction

## Workflow

1. **Topic Research** (Input: User's topic query)
   - Retrieves top-ranking pages from Google

2. **Keyword Analysis** (Input: Top-ranking URLs)
   - Extracts keyword data using SEMrush API
   - Analyzes keyword frequency and search volume

3. **Content Extraction** (Input: Competitor URLs)
   - Fetches content from competitor pages using Jina AI

4. **Content Generation**
   - **Input:** Analyzed data
   - **Process:**
     - **Content Analysis:**
       - Common topics across competitors
       - Contradicting viewpoints
       - Information gaps
     - **Content Planning:**
       - Structured outline
       - SEO keyword integration strategy
       - Content differentiation strategy
     - **Draft Generation:**
       - AI-generated initial content
       - Following the content plan
       - Keyword-optimized
     - **Proofreading:**
       - Proofread content
       - Enhanced readability
       - SEO-optimized structure
     - **SEO Optimization:**
       - URL slug suggestions
       - Title tag variations
       - Meta description options
     - **Final Deliverable:**
       - Complete article
       - SEO elements
       - Keyword analysis
       - Competitor insights
       - Content strategy notes

