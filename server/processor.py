import math
import os
from typing import List
import nltk
nltk.download('punkt_tab', quiet=True)
from context import CONTEXTUAL_RAG_PROMPT
from helpers import generate_context, load_from_cache, save_to_cache, generate_embeddings

class TextProcessor:
    """
    Processes raw document text and stores its embeddings.
    Responsibilities:
      - Load or cache the raw text.
      - Create overlapping text chunks.
      - Generate prompts and contextual chunks.
      - Generate embeddings and store them in a Chroma collection.
    """
    def __init__(
            self, 
            document: str, 
            client, 
            chroma_client,  
            integrator: str = "together", 
            base_name: str = "document", 
            cache_dir: str = "cache",
            chunk_size: str = "100"
            ):
        self.client = client
        self.chroma_client = chroma_client
        self.integrator = integrator
        self.base_name = base_name
        self.cache_dir = cache_dir
        try:
            self.chunk_size = int(chunk_size)
        except (ValueError, TypeError):
            self.chunk_size = 100

        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Define cache file paths.
        self.text_cache = os.path.join(self.cache_dir, f"{self.base_name}_text.pkl")
        self.chunks_cache = os.path.join(self.cache_dir, f"{self.base_name}_chunks.pkl")
        self.contextual_chunks_cache = os.path.join(self.cache_dir, f"{self.base_name}_contextual_chunks.pkl")
        
        # If a cached version of the document exists, load it.
        cached_doc = load_from_cache(self.text_cache)
        if cached_doc:
            self.document = cached_doc
        else:
            self.document = document
            save_to_cache(self.document, self.text_cache)
        
        # Output variables that will be set during processing.
        self.chunks = None
        self.contextual_chunks = None
        self.collection = None

    def _create_chunks(self, chunk_size: int, overlap: int = 10) -> List[str]:
        """
        Create overlapping text chunks from the document using sentence boundaries.
        The document is split into sentences and sentences are grouped until roughly 
        'chunk_size' tokens (words) are reached. The last 'overlap' tokens of each 
        chunk are then prepended to the next chunk.
        """
        if not isinstance(self.document, str):
            raise ValueError("Document must be a string.")
        if chunk_size <= overlap:
            raise ValueError("chunk_size must be greater than overlap.")
        
        # Split the document into sentences.
        sentences = nltk.sent_tokenize(self.document)
        token_count = lambda text: len(text.split())
        
        chunks = []
        current_tokens = []  # This will store tokens (words) for the current chunk.
        
        for sentence in sentences:
            # Prepare a potential chunk by joining current tokens with the new sentence.
            potential_chunk = " ".join(current_tokens + [sentence])
            if token_count(potential_chunk) > chunk_size and current_tokens:
                # Commit the current chunk.
                chunk_text = " ".join(current_tokens)
                chunks.append(chunk_text)
                # Retain the last 'overlap' tokens for context.
                current_tokens = chunk_text.split()[-overlap:] if overlap > 0 else []
            # Add the current sentence (as tokens) to the current chunk.
            current_tokens.extend(sentence.split())
        
        # Append any remaining tokens as the final chunk.
        if current_tokens:
            chunks.append(" ".join(current_tokens))
        
        return chunks

    def _generate_prompts(self, chunks: List[str]) -> List[str]:
        """Generate prompts for each chunk using a global prompt template."""
        return [
            CONTEXTUAL_RAG_PROMPT.format(WHOLE_DOCUMENT=self.document, CHUNK_CONTENT=chunk)
            for chunk in chunks
        ]

    def _generate_contextual_chunks(self, prompts: List[str], chunks: List[str]) -> List[str]:
        """Generate contextual chunks by fetching context from the client."""
        contextual_chunks = []
        for i, (prompt, chunk) in enumerate(zip(prompts, chunks)):
            try:
                context = generate_context(self.client, prompt, integrator=self.integrator)
                print(f"Context for chunk {i}: {context}")  # Consider logging instead
                contextual_chunks.append(f"{context} {chunk}")
            except Exception as e:
                print(f"Error generating context for chunk {i}: {e}")
                # Optionally append just the chunk without context or skip
                contextual_chunks.append(chunk)
        return contextual_chunks

    def _store_embeddings_in_chroma(self, collection_name: str, contextual_chunks: List[str], contextual_embeddings: List[List[float]]):
        """
        Upsert embeddings into a Chroma collection.
        """
        # Validate inputs.
        if len(contextual_chunks) != len(contextual_embeddings):
            raise ValueError("The number of chunks and embeddings must be the same.")

        collection = self.chroma_client.get_or_create_collection(name=collection_name)
        ids = [f"chunk_{i}" for i in range(len(contextual_chunks))]
        metadatas = [{"text": chunk} for chunk in contextual_chunks]

        collection.upsert(
            ids=ids,
            embeddings=contextual_embeddings,
            documents=contextual_chunks,
            metadatas=metadatas,
        )
        
        print(f"Upserted {len(contextual_chunks)} embeddings into Chroma collection '{collection_name}'")
        return collection
    
        # === Public Wrapper Methods for Granular Control ===

    def create_chunks(self) -> List[str]:
        """Public method to create (or load) overlapping text chunks."""
        self.chunks = load_from_cache(self.chunks_cache)
        if not self.chunks:
            print("No cached chunks found. Generating new chunks.")
            self.chunks = self._create_chunks(self.chunk_size, overlap=math.ceil(self.chunk_size / 20))
            if not self.chunks:
                raise ValueError("Failed to generate chunks from the document.")
            save_to_cache(self.chunks, self.chunks_cache)
        else:
            print("Loaded cached chunks.")
        return self.chunks

    def generate_contextual_chunks(self) -> List[str]:
        """Public method to generate (or load) contextual chunks based on prompts."""
        if not self.chunks:
            raise ValueError("Chunks not available; please generate chunks first.")
        prompts = self._generate_prompts(self.chunks)
        self.contextual_chunks = load_from_cache(self.contextual_chunks_cache)
        if not self.contextual_chunks:
            self.contextual_chunks = self._generate_contextual_chunks(prompts, self.chunks)
            save_to_cache(self.contextual_chunks, self.contextual_chunks_cache)
        return self.contextual_chunks

    def store_embeddings(self):
        """Public method to generate embeddings and store them in the Chroma collection."""
        if not self.contextual_chunks:
            raise ValueError("Contextual chunks not available; please generate them first.")
        collection_name = f"{self.base_name}_{self.integrator}_embeddings"
        self.collection = self.chroma_client.get_or_create_collection(name=collection_name)
        if self.collection.count() == 0:
            try:
                contextual_embeddings = generate_embeddings(self.client, self.contextual_chunks, integrator=self.integrator)
            except Exception as e:
                print(f"Error in generating embeddings: {e}")
                raise
            self.collection = self._store_embeddings_in_chroma(collection_name, self.contextual_chunks, contextual_embeddings)
        else:
            print(f"Using existing embeddings in Chroma collection '{collection_name}'")
        return self.collection

    def process(self):
        """High-level pipeline that runs all steps in order."""
        self.create_chunks()
        self.generate_contextual_chunks()
        self.store_embeddings()
        return {
            "chunks": self.chunks,
            "contextual_chunks": self.contextual_chunks,
            "collection": self.collection,
        }
    
    def cleanup(self):
        """Remove cached files for this article."""
        for cache_file in [self.text_cache, self.chunks_cache, self.contextual_chunks_cache]:
            if os.path.exists(cache_file):
                os.remove(cache_file)