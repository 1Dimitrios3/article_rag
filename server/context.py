# We want to generate a snippet explaining the relevance/importance of the chunk with
# full document in mind.

CONTEXTUAL_RAG_PROMPT = """
Given the document below, we want to explain what the chunk captures in the document.

{WHOLE_DOCUMENT}

Here is the chunk we want to explain:

{CHUNK_CONTENT}

Answer ONLY with a succinct explaination of the meaning of the chunk in the context of the whole document above.
"""