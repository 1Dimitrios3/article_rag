import os
from filecache import FileCache
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from asgiref.wsgi import WsgiToAsgi
from helpers import clear_all_cache_and_embeddings, create_chat, get_base_name, get_chroma_client, initialize_chroma_client, suggest_similar_articles
from processor import TextProcessor
from retriever import Retriever
from scraper import Scraper
from together import Together
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Check that at least one API key is provided.
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
openai_api_key = os.environ.get("OPENAI_API_KEY")

if not (TOGETHER_API_KEY or openai_api_key):
    raise Exception("Error: At least one of TOGETHER_API_KEY or OPENAI_API_KEY must be set in the .env file.")


# Instantiate Together client only if the key is present;
# Otherwise, raise an error when someone attempts to use it.
if TOGETHER_API_KEY and TOGETHER_API_KEY.strip():
    together_client = Together(api_key=TOGETHER_API_KEY)
else:
    together_client = None  # Later, endpoints can return an error if a Together integrator is requested

# Instantiate OpenAI responses client only if the key is present.
if openai_api_key and openai_api_key.strip():
    openai_responses_client = OpenAI(api_key=openai_api_key)
else:
    openai_responses_client = None  # Later, endpoints can return an error if an OpenAI integrator is requested

# Instantiate chroma storage path
STORAGE_PATH = os.getenv("CHROMA_STORAGE_PATH", "./together_embeddings")
chroma_client = None

# Create a Flask app.
app = Flask(f"article_scraper")
CORS(
    app,
    resources={r"/*": {"origins": ["http://localhost:3000"]}},
    supports_credentials=True,
    methods=["GET", "POST", "DELETE"],
    allow_headers=["*"]
)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "you-will-never-guess")
asgi_app = WsgiToAsgi(app)

file_cache = FileCache()

IMAGES_DIR = os.path.join(os.getcwd(), "images")

@app.route("/api/article-image", methods=["GET"])
def get_article_image():
    image_filename = "articleImage.png"
    image_path = os.path.join(IMAGES_DIR, image_filename)
    
    if not os.path.exists(image_path):
        return jsonify({"error": "Image not found"}), 404
    
    # Serve the image file.
    return send_from_directory(IMAGES_DIR, image_filename)

@app.route("/api/process-article", methods=["POST"])
def process_article_endpoint():
    global chroma_client
    data = request.json
    url = data.get("url")
    chunk_size = data.get("chunk_size")
    integrator = data.get("integrator", "together").lower()
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    # Validate integrator.
    if integrator not in ["together", "openai"]:
        return jsonify({"error": "Invalid integrator specified."}), 400

    try:
        # Initialize the global chroma_client if it hasn't been already.
        if chroma_client is None:
            chroma_client = get_chroma_client(integrator)
        # Decide which client to use.
        used_client = together_client if integrator.lower() == "together" else openai_responses_client

        # Scrape the article.
        scraper = Scraper()
        document = scraper.scrape_article(url)
        article_title = document["title"]
        article_text = document["article_text"]

        if not article_text:
            return jsonify({"error": "Failed to retrieve article text."}), 500


        # Compute a unique base name for this URL.
        base_name = get_base_name(url)

        # Cache the article title and text.
        file_cache.set(url, "title", article_title)
        file_cache.set(url, "text", article_text)

        # Process the article.
        # The TextProcessor will load cached text, chunks, and contextual_chunks if available.
        processor = TextProcessor(article_text, used_client, chroma_client, integrator, base_name, chunk_size=chunk_size)
        processor.process() 

        return jsonify({"message": "Article has been processed successfully.", "articleTitle": article_title }), 200
    
    except Exception as e:
        error_message = f"Server error during article processing. Details: {str(e)}"
        print(f"Error processing article: {error_message}")
        return jsonify({"error": error_message}), 500   

# Global chat history dictionary.
chat_histories = {}

@app.route("/api/retrieve-chat", methods=["POST"])
def retrieve_chat_endpoint():
    global chroma_client
    data = request.json
    url = data.get("url")
    query = data.get("query")
    model = data.get("model")
    integrator = data.get("integrator", "together").lower()
    
    if not url or not query:
        return jsonify({"error": "URL and query are required"}), 400

    if integrator not in ["together", "openai"]:
        return jsonify({"error": "Invalid integrator specified."}), 400
    
    try:
        # Initialize the global chroma_client if it hasn't been already.
        if chroma_client is None:
            chroma_client = get_chroma_client(integrator)

        used_client = together_client if integrator.lower() == "together" else openai_responses_client

        # Compute the same unique base name for this URL.
        base_name = get_base_name(url)

        article_text = file_cache.get(url, "text")
        if not article_text:
            return jsonify({"error": "Article text not found in cache. Please process the article first."}), 404

        processor = TextProcessor(article_text, used_client, chroma_client, integrator, base_name)
        processed_data = processor.process()

        retriever = Retriever(
            used_client,
            chroma_client,
            processed_data["contextual_chunks"],
            processed_data["collection"],
            integrator,
            base_name
        )

        retrieved_chunks = retriever.retrieve(query)

        # Return the streaming chat response.
        return create_chat(
            used_client, 
            query, 
            retrieved_chunks, 
            integrator,
            model, 
            url=url, 
            chat_histories=chat_histories
            )
    
    except Exception as e:
        print(f"Error during retrieval: {e}")
        return jsonify({"error": "Internal server error during chat retrieval."}), 500

@app.route("/api/suggest-articles", methods=["POST"])
def suggest_articles_endpoint():
    """
    Suggest similar articles based on the cached article title.
    
    Expects JSON with:
      - "url": The URL of the article whose title was cached.
      - "integrator": (Optional) "together" or "openai" (defaults to "together").
    """
    data = request.json
    url = data.get("url")
    integrator = data.get("integrator", "together")
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    # Validate integrator.
    if integrator not in ["together", "openai"]:
        return jsonify({"error": "Invalid integrator specified."}), 400
        
    try:
        used_client = together_client if integrator.lower() == "together" else openai_responses_client
        
        cached_title = file_cache.get(url, "title")
        print('cached_title ---->', cached_title)
        if cached_title is None:
            return jsonify({"error": "Article title not found in cache."}), 404
        
        article_title = cached_title.decode("utf-8") if isinstance(cached_title, bytes) else cached_title

        # Return the streaming response from suggest_similar_articles.
        return suggest_similar_articles(used_client, article_title)
    
    except Exception as e:
        print(f"Error in suggest_articles_endpoint: {e}")
        return jsonify({"error": "Internal server error during article suggestion."}), 500
    
@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    global chroma_client
    data = request.get_json()
    integrator = data.get("integrator", "together").lower()

    if integrator == "openai":
        storage_path_to_use = STORAGE_PATH
    elif integrator == "together":
        storage_path_to_use = "./together_embeddings"
    else:
        return jsonify({"error": f"Unknown integrator: {integrator}"}), 400
    
    try:
        # Clear caches and reinitialize a new client.
        chroma_client = clear_all_cache_and_embeddings("cache", storage_path_to_use, integrator, chroma_client=chroma_client)
        # Optionally, log or return information about the new client.
        return jsonify({"message": "Cache and embeddings cleared."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/check-integrators", methods=["GET"])
def check_integrators():
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    together_api_key = os.environ.get("TOGETHER_API_KEY")
    
    result = {
        "openai": bool(openai_api_key and openai_api_key.strip()),
        "together": bool(together_api_key and together_api_key.strip())
    }
    return jsonify(result), 200
# if __name__ == "__main__":
#     # For development, you can use uvicorn:
#     # uvicorn main:asgi_app --workers 4 --reload
#     app.run(debug=True)

if __name__ == "__main__":
#     integrator='openai'
#     # query = "What happens to the treasure?"
#     # query = "Who saved Sally?"
#     # query = "What happened to Sally?"
#     # query = "Who is Mark?"
#     # query = "Will AI Revolutionize Drug Development?"
#     # query="what is the challenge posed in the article?"
#     # query="Based on the article when does an infant starts forming memories?"
#     query="what are some key findings of the article?"
#     url="https://singularityhub.com/2025/03/20/new-baby-brain-scans-reveal-the-moment-we-start-making-memories/"
#     # url="https://singularityhub.com/2025/02/04/will-ai-revolutionize-drug-development-these-are-the-root-causes-of-drug-failure-it-must-address/"
#     # url="https://www.theatlantic.com/technology/archive/2025/01/generative-ai-virtual-cell/681246/"
#     # url="https://newlinesinstitute.org/state-resilience-fragility/as-discontent-grows-in-syria-assad-struggles-to-retain-support-of-alawites/" # forbidden
#     # url="https://www.theatlantic.com/international/archive/2024/12/assad-alawites-syria-hts/681038/"
#     # url="https://www.huffingtonpost.es/global/siria-guerra-venganza-matanza-evidencia-complicaciones-transicion-post-assad.html"
    
#     used_client = together_client if integrator.lower() == "together" else openai_responses_client

#     # Retrieve and process the webpage document.
#     scraper = Scraper()
#     document = scraper.scrape_article(url)   
#     article_title = document["title"]
#     article_text = document["article_text"] 

#     response = suggest_similar_articles(used_client, article_title)
#     # --- Processing Phase ---
#     processor = TextProcessor(article_text, used_client, chroma_client, integrator)
#     processed_data = processor.process()

#     # # --- Retrieval Phase ---
#     retriever = Retriever(used_client, chroma_client, processed_data["contextual_chunks"], processed_data["collection"], integrator)
#     retrieved_chunks = retriever.retrieve(query)

#     # # --- Final Chat Response ---
#     response = create_chat(used_client, query, retrieved_chunks, integrator)
    
#     print("Final Chat Response:")
#     print(response)
    
    clear_all_cache_and_embeddings("cache", STORAGE_PATH)