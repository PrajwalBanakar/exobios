"""
input is: differrential diagnosis from node 1
reads the diseases, does retrieval and rerank by hybrid search in QDrant against the diagnosed diseases
gets back citations/chunks from qdrant, llm call with the chunks payload
generated the recommended investigation object
write to the state object the recommended investigation object

"""