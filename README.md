# RAG Chatbot for Articles

This repository contains the code for a Retrieval-Augmented Generation (RAG) Chatbot designed specifically for analyzing and interacting with articles. Drawing inspiration from [Anthropic’s article on contextual retrieval](https://www.anthropic.com/news/contextual-retrieval) — which introduces a new hybrid and more efficient approach — the system processes article URLs by scraping, processing, and embedding the content to generate insightful conversations and summaries.

## Key Features:
- **Article-Based Queries:** Provide a URL to an article and let the system read, embed, and analyze its content.
- **Choose Your Integrator:** Leverage the power of either OpenAI or TogetherAI. Set the respective API keys to select your preferred service.
- **Dynamic Model Selection:** Based on the chosen integrator, a tailored list of available models is provided to query and test, ensuring you have the right tool for your specific needs.
- **Optional Chunk Size Setting:** Configure an optional chunk size during the processing phase to control how the article content is segmented for embedding.
- **Retrieval-Augmented Generation (RAG):** Enhances response accuracy by retrieving relevant context from the article before generating answers.
- **Streaming Responses:** Experience real-time, incremental responses for a faster and more interactive chat experience.
- **Relevant Article Suggestions:** When using OpenAI as the integrator, receive suggestions for related articles that may enhance your research or discussion.

The project is split into two parts:
- A **Flask-based backend** that handles article processing, embedding generation, and chat interactions.
- A **TanStack Router frontend** that provides the user interface for interacting with the article content.

---

## Environment Configuration

Create a .env file in the backend root directory with the following variables:

1. Create a `.env` file in the backend root directory with the following content:
   ```env
   CHROMA_STORAGE_PATH=./chroma_storage
   OPENAI_API_KEY=your_openai_key_here
   TOGETHER_API_KEY=your_together_key_here


- **CHROMA_STORAGE_PATH**: Specifies where article embeddings are stored.
- **OPENAI_API_KEY**: Your API key for using OpenAI. [OpenAI Documentation](https://platform.openai.com/docs/overview)
- **TOGETHER_API_KEY**: Your API key for using TogetherAI. [TogetherAI Documentation](https://www.together.ai)

Note: Set the key for the integrator you plan to use. You can configure both if you wish to switch between services.

## Backend Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd <repository-directory>

2. All required Python dependencies are listed in dependencies.txt. Install them using:
   ```bash
   pip/python install -r dependencies.txt

3. Start the Backend Server locally
     ```bash
     uvicorn main:asgi_app --reload

## Frontend Setup

1. cd tanstack_fe
   ```bash
      pnpm i 
      pnpm dev
