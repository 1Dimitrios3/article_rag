import os
from typing import List, Tuple
import bm25s
from collections import defaultdict
from helpers import load_from_cache, normalize, rerank_documents_openai, rerank_documents_togetherai, save_to_cache, generate_embeddings

class Retriever:
    """
    Handles retrieval.
    Responsibilities:
      - Perform vector retrieval using the Chroma collection.
      - Create (and cache) a BM25 index and perform BM25 retrieval.
      - Fuse retrieval results and re-rank them.
    """
    def __init__(self, client, chroma_client, contextual_chunks: List[str], collection, integrator: str = "together", base_name: str = "document", cache_dir: str = "cache"):
        self.client = client
        self.chroma_client = chroma_client
        self.contextual_chunks = contextual_chunks
        self.collection = collection
        self.integrator = integrator
        self.base_name = base_name
        self.cache_dir = cache_dir

        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.bm25_cache = os.path.join(self.cache_dir, f"{self.base_name}_bm25.pkl")
        self.bm25_index = None

    def _chroma_vector_retrieval(self, query: str, k: int = 10) -> List[int]:
        """
        Given a query, generate its embedding and query the Chroma collection.
        Returns a list of indices corresponding to the retrieved chunks.
        """
        # Generate query embedding
        query_embedding = generate_embeddings(self.client, [query], integrator=self.integrator)[0]
        # Query the collection.
        results = self.collection.query(query_embeddings=[query_embedding], n_results=k)
        # Extract IDs assuming IDs are in the format "chunk_{index}".
        ids = results["ids"][0]
        indices = [int(id_.split("_")[1]) for id_ in ids]
        return indices

    def _create_bm25_index(self):
        """
        Create the BM25 model and index the corpus of contextual chunks.
        """
        if not self.contextual_chunks:
            raise ValueError("No contextual chunks available for BM25 indexing.")
        tokenized_corpus = bm25s.tokenize(self.contextual_chunks)
        bm25_index = bm25s.BM25(corpus=self.contextual_chunks)
        bm25_index.index(tokenized_corpus)
        return bm25_index

    def _bm25_retrieval(self, query: str, k: int, bm25_index) -> List[int]:
        """
        Retrieve indices using BM25.
        """
        results, _ = bm25_index.retrieve(bm25s.tokenize(query), k=k)
        # Build a mapping from normalized chunk to its index for efficient lookup.
        norm_chunks_map = {normalize(doc): idx for idx, doc in enumerate(self.contextual_chunks)}
        
        indices = []
        for doc in results[0]:
            norm_doc = normalize(doc)
            if norm_doc in norm_chunks_map:
                indices.append(norm_chunks_map[norm_doc])
        return indices

    def _fuse_ranks(self, *rank_lists, K: int = 60) -> Tuple[List[Tuple[int, float]], List[int]]:
        """
        Fuse ranking lists from multiple IR systems using Reciprocal Rank Fusion (RRF).
        
        Returns:
        - A list of tuples (document index, RRF score) sorted by score (highest first).
        - A list of document indices sorted by their RRF score.
        """
        rrf_scores = defaultdict(float)
        for rank_list in rank_lists:
            for rank, doc_index in enumerate(rank_list, 1):
                rrf_scores[doc_index] += 1 / (rank + K)
        sorted_scores = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores, [doc_index for doc_index, _ in sorted_scores]

    def _rerank_documents(self, documents: List[str], query: str, top_n: int = 5) -> str:
        """
        Rerank documents using the appropriate method based on the integrator property.
        If self.integrator is 'openai', call rerank_documents_openai;
        otherwise, call rerank_documents_togetherai.
        """
        if self.integrator.lower() == 'openai':
            return rerank_documents_openai(self.client, documents, query, top_n)
        else:
            return rerank_documents_togetherai(self.client, documents, query, top_n)

    # --- Public Methods for Granular Control ---

    def vector_retrieval(self, query: str, k: int = 8, 
                         embedding_model: str = "BAAI/bge-large-en-v1.5") -> List[int]:
        """Public method for vector retrieval using Chroma."""
        return self._chroma_vector_retrieval(query, k)

    def build_bm25_index(self):
        """Public method to build (or load) the BM25 index."""
        self.bm25_index = load_from_cache(self.bm25_cache) or self._create_bm25_index()
        if not load_from_cache(self.bm25_cache):
            save_to_cache(self.bm25_index, self.bm25_cache)
        return self.bm25_index

    def bm25_retrieval(self, query: str, k: int) -> List[int]:
        """Public method for BM25 retrieval."""
        if not self.bm25_index:
            self.build_bm25_index()
        # Clamp k to the size of the corpus
        k = min(k, len(self.contextual_chunks))
        return self._bm25_retrieval(query, k, self.bm25_index)

    def fuse_results(self, vector_results: List[int], bm25_results: List[int], K: int = 60) -> List[int]:
        """Public method to fuse vector and BM25 retrieval results."""
        _, fused_indices = self._fuse_ranks(vector_results, bm25_results, K=K)
        return fused_indices

    def rerank(self, indices: List[int], query: str, top_n: int = 5) -> str:
        """Public method to re-rank documents based on fused indices."""
        docs = [self.contextual_chunks[i] for i in indices]
        return self._rerank_documents(docs, query, top_n)

    def retrieve(self, query: str, k: int = 10) -> str:
        """
        High-level retrieval pipeline:
          1. Perform vector retrieval using Chroma.
          2. Build BM25 index (from cache or new) and perform BM25 retrieval.
          3. Fuse the vector and BM25 results.
          4. Re-rank the fused results.
        Returns the re-ranked documents.
        """
        vector_results = self.vector_retrieval(query, k)
        bm25_results = self.bm25_retrieval(query, k)

        if not bm25_results:
            print("[INFO] Falling back to vector results only.")
            return self.rerank(vector_results, query)

        fused_indices = self.fuse_results(vector_results, bm25_results)
        return self.rerank(fused_indices, query)