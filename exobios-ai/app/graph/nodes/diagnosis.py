"""
cleans input vitals, embeds user input query, retrieves against input embed query in QDrant by: hybrid search, calls llm with the retrieved and reranked chunks, writes to the state object the differential diagnosis object
"""