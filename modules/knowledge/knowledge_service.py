import chromadb
from ollama import Client

class KnowledgeService:
    def __init__(self):
        self.client = Client(host='http://localhost:11434')
        # Stores data in a local folder called 'vector_db'
        self.db = chromadb.PersistentClient(path="./vector_db")
        self.collection = self.db.get_or_create_collection("ez_docs")

    async def query_docs(self, user_query: str):
        # 1. Generate embedding for the query using Ollama
        response = self.client.embed(model="nomic-embed-text", input=user_query)
        query_vector = response['embeddings'][0]

        # 2. Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_vector], 
            n_results=3
        )
    
        # 3. Format for the LLM
        if not results["documents"][0]:
            return "No specific documentation found for this query."
    
        return "\n---\n".join(results["documents"][0])