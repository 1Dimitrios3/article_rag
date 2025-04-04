import hashlib
import os
import pickle
import shutil
from typing import List
from filecache import FileCache
from flask import Response
import chromadb

def initialize_chroma_client(storage_path, reset=False):
    """
    Initialize a new ChromaDB PersistentClient with the given storage path.
    If reset is True, remove existing storage before initializing.
    """
    if reset:
        if os.path.exists(storage_path):
            print(f"Removing existing storage at: {storage_path}")
            shutil.rmtree(storage_path)
        else:
            print(f"No existing storage found at: {storage_path}")
    else:
        if os.path.exists(storage_path):
            print(f"Using existing storage at: {storage_path}")
        else:
            print(f"No existing storage found at: {storage_path}")
    
    client = chromadb.PersistentClient(path=storage_path)
    print(f"Initialized ChromaDB client with storage path: {storage_path}")
    return client

def get_chroma_client(integrator: str):
    if integrator.lower() == "openai":
        # Use the environment variable if defined, or default to a specific path.
        storage_path = os.getenv("CHROMA_STORAGE_PATH", "./openai_embeddings")
    elif integrator.lower() == "together":
        storage_path = "./together_embeddings"
    else:
        raise ValueError(f"Unknown integrator: {integrator}")
    
    return initialize_chroma_client(storage_path)

def clear_all_cache_and_embeddings(cache_dir: str, storage_path: str, integrator: str = 'random',  base_name: str = "document", chroma_client=None):
    """
    Clears the local file cache, the Chroma vector database storage, and all file cache title entries.
    
    Args:
        cache_dir (str): The path to the file-based cache directory.
        storage_path (str): The path to the Chroma vector database storage.
    """
    # Close the existing client connection if it exists.
    if chroma_client is not None:
        try:
            chroma_client.close()  # Make sure your client has a close() method.
            print("Existing Chroma client connection closed.")
        except Exception as e:
            print("Error closing existing Chroma client:", e)
    # Clear file cache.
    if os.path.exists(cache_dir):
        # Optionally, call the cleanup method of FileCache to remove JSON files.
        file_cache = FileCache(cache_dir)
        file_cache.cleanup()
        
        shutil.rmtree(cache_dir)
        print(f"Cleared file cache at {cache_dir}")
    else:
        print(f"No cache directory found at {cache_dir}")

    # Recreate the cache directory after clearing
    os.makedirs(cache_dir, exist_ok=True)

    # Clear Chroma storage.
    if os.path.exists(storage_path):
        shutil.rmtree(storage_path)
        print(f"Cleared Chroma embeddings at {storage_path}")
    else:
        print(f"No Chroma storage found at {storage_path}")

    # Recreate the storage directory after clearing
    os.makedirs(storage_path, exist_ok=True)

def get_base_name(url: str) -> str:
    return hashlib.md5(url.encode('utf-8')).hexdigest()

def save_to_cache(data, cache_path: str):
    with open(cache_path, "wb") as f:
        pickle.dump(data, f)
    print(f"Saved cache to {cache_path}")

def load_from_cache(cache_path: str):
    if os.path.exists(cache_path):
        print(f"Loading cache from {cache_path}")
        with open(cache_path, "rb") as f:
            return pickle.load(f)
    print(f"No cache found at {cache_path}")
    return None

def normalize(text):
    return text.strip().lower()

def generate_embeddings(client, input_texts: List[str], integrator: str, model_api_string: str = None) -> List[List[float]]:
    """
    Generate embeddings using the specified client and integrator.
    
    Args:
        input_texts (List[str]): A list of input texts.
        model_api_string (str): The model identifier for the embedding model.
        client: The client instance (either Together or OpenAI).
        integrator (str): The API provider to use. Accepts 'together' or 'openai'. Default is 'together'.
        
    Returns:
        List[List[float]]: A list of embeddings corresponding to the input texts.
    """
    embeddings = []
    
    if integrator.lower() == 'together':
        outputs = client.embeddings.create(
            input=input_texts,
            model=model_api_string or "BAAI/bge-large-en-v1.5",
        )
        for i, data in enumerate(outputs.data):
            embedding = data.embedding
            snippet = input_texts[i][:50] + "..." if len(input_texts[i]) > 50 else input_texts[i]
            print(f"[DEBUG][Together] Embedding {i + 1}/{len(outputs.data)} created for input: '{snippet}' (length: {len(embedding)})")
            embeddings.append(embedding)
            
    elif integrator.lower() == 'openai':
        # For OpenAI, assume the client follows the OpenAI API structure.
        outputs = client.embeddings.create(
            input=input_texts,
            model=model_api_string or "text-embedding-ada-002",
        )
        for i, data in enumerate(outputs.data):
            embedding = data.embedding
            snippet = input_texts[i][:50] + "..." if len(input_texts[i]) > 50 else input_texts[i]
            print(f"[DEBUG][OpenAI] Embedding {i + 1}/{len(outputs.data)} created for input: '{snippet}' (length: {len(embedding)})")
            embeddings.append(embedding)
            
    else:
        raise ValueError("Unsupported provider. Choose 'together' or 'openai'.")
    
    return embeddings


def generate_context(client, prompt: str, integrator: str = 'together', model: str = None, temperature: float = 1) -> str:
    """
    Generate context from a prompt using the specified client, integrator, and model.
    
    Args:
        client: The client instance (either Together or OpenAI).
        prompt (str): The prompt to generate context from.
        integrator (str): The API provider to use ('together' or 'openai'). Default is 'together'.
        model (str): The model identifier. If None, a default is used based on the integrator.
        temperature (float): Temperature for generation.
        
    Returns:
        str: The generated context.
    """
    if integrator.lower() == 'together':
        default_model = "meta-llama/Llama-3.2-3B-Instruct-Turbo"
    elif integrator.lower() == 'openai':
        default_model = "gpt-3.5-turbo"
    else:
        raise ValueError("Unsupported integrator. Please choose 'together' or 'openai'.")

    model = model or default_model

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    return response.choices[0].message.content

def rerank_documents_togetherai(client, documents: List[str], query: str, top_n: int = 5) -> str:
    """
    Rerank documents using the Salesforce/Llama-Rank-V1 model and return the top results.
    """
    response = client.rerank.create(
        model="Salesforce/Llama-Rank-V1",
        query=query,
        documents=documents,
        top_n=top_n
    )
    retrieved_chunks = ""
    for result in response.results:
        retrieved_chunks += documents[result.index] + '\n\n'
    return retrieved_chunks

def rerank_documents_openai(client, documents: List[str], query: str, top_n: int = 5) -> str:
    """
    Rerank documents using the OpenAI chat completion API.
    This function constructs a prompt that instructs the model to rank the candidate documents 
    based on their relevance to the query and return the top documents.
    """
    # Build a prompt that presents the query and candidate documents.
    prompt = (
        "You are a helpful assistant that ranks documents by their relevance to a given query.\n\n"
        f"Query: {query}\n\n"
        "Here are the candidate documents:\n"
    )
    for i, doc in enumerate(documents, start=1):
        prompt += f"{i}. {doc}\n\n"
    
    prompt += (
        f"Please rank the documents by relevance to the query and return the top {top_n} document texts, "
        "each separated by a newline. Do not include numbers or extra commentary."
    )
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        stream=False
    )
    
    # The output should be a plain text list of documents. 
    return response.choices[0].message.content
  
def stream_generator(response_iterator, url='', chat_histories=None):
    """Stream OpenAI response while storing it in chat history."""
    full_response = ""
    
    for chunk in response_iterator:
        delta = chunk.choices[0].delta
        if delta.content is not None:
            full_response += delta.content
            print(delta.content, end="", flush=True)
            yield delta.content

    # # Ensure there is a history for this session.
    # if url not in chat_histories:
    #     chat_histories[url] = []
        
    # # Store final response in chat history.
    # chat_histories[url].append({"role": "assistant", "content": full_response})
    # # Keep only the last 5 entries.
    # chat_histories[url] = chat_histories[url][-5:]

def create_chat(client, query, retrieved_chunks, integrator: str, model: str = None, temperature: float = 0.3, url: str = '', chat_histories: dict = None):
    """
    Create a chat completion request using the specified client, integrator, and model,
    while integrating chat history (keeping the last 5 responses per URL).
    
    Args:
        client: The API client instance (e.g., OpenAI or Together).
        query (str): The user query.
        retrieved_chunks (str): Relevant information to be provided to the chat model.
        integrator (str): Which API provider to use ('openai' or 'together').
        model (str): Optional. A model identifier. If not provided, a default model is chosen based on the integrator.
        temperature (float): The generation temperature.
        url (str): A key for storing/retrieving chat history.
        chat_histories (dict): A dictionary mapping URL keys to a list of previous chat responses.
    
    Returns:
        StreamingResponse: A streaming response wrapping the chat completion.
    """
    if chat_histories is None:
        chat_histories = {}

    # Set default models based on integrator.
    if integrator.lower() == 'openai':
        default_model = "gpt-4o-mini"
    elif integrator.lower() == 'together':
        default_model = "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo"
    else:
        raise ValueError("Unsupported integrator. Choose 'openai' or 'together'.")
    
    chosen_model = model or default_model
    
    # Build the conversation messages.
    messages = [
        {"role": "system", "content": "You are an AI assistant that provides answers based solely on the provided content."}
    ]
    
    # Append any existing chat history for the URL.
    # if url in chat_histories:
    #     messages.extend(chat_histories[url])
    
    # Append the new user message.
    messages.append({
        "role": "user",
        "content": f"Answer the question: {query}. Here is relevant information: {retrieved_chunks}"
    })
    
    response = client.chat.completions.create(
        model=chosen_model,
        messages=messages,
        temperature=temperature,
        stream=True
    )
    
    return Response(stream_generator(response, url, chat_histories), mimetype="text/plain")

def stream_generator_responses_api(response):
    """Generator that yields streaming text from the response."""
    full_text = ""
    for event in response:
        # Check if the event is a delta event with text.
        if event.type == "response.output_text.delta":
            delta = event.delta  # the incremental text content
            full_text += delta
            yield delta  # yield incremental updates (or you can yield full_text if desired)
        # You can handle annotation events if needed.
        elif event.type == "response.completed":
            break


def suggest_similar_articles(client, title_text: str, search_context_size: str = "medium", user_location: dict = None) -> str:
    """
    Uses the web_search_preview tool to search the web for similar articles.
    The prompt instructs the LLM to read the provided article title carefully
    and then suggest 4-5 interesting articles on similar topics.

    Args:
        client: The OpenAI client instance.
        title_text (str): The scraped article title.
        search_context_size (str): The context size for the search tool ('high', 'medium', or 'low'). Default is 'medium'.
        user_location (dict, optional): Optional dictionary to refine search results based on user location.

    Returns:
        str: The output text from the web search, including inline citations.
    """

    # Build the prompt with additional instructions.
    prompt = (
        "Read the following article title carefully and suggest 4-5 interesting articles "
        "that cover similar topics and breakthroughs. Provide only the article titles, a short description, and a link for each. "
        "Ensure that all suggested articles were published within the last 2 years and no older, and exclude any articles that require paid reading or subscriptions.\n\n"
        f"Article Title: {title_text}"
    )
    
    # Build the tool configuration.
    tool_config = {
        "type": "web_search_preview",
        "search_context_size": search_context_size
    }
    
    # Optionally add user location details.
    if user_location:
        tool_config["user_location"] = user_location
    
    # Create the response using the web search tool.
    stream = client.responses.create(
        model="gpt-4o-mini",
        tools=[tool_config],
        input=prompt,
        stream=True
    )

    def generate():
        for delta in stream_generator_responses_api(stream):
            print(delta, end="", flush=True)
            yield delta
    
    return Response(generate(), mimetype="text/plain")

