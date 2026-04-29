from .knowledge_service import KnowledgeService

knowledge_service = KnowledgeService()

search_documentation_tool = {
    "name": "search_documentation",
    "description": "Search the internal EZ Inventory knowledge base for navigation help, feature explanations, and directions on where to go in the system.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search term or question about how the system works"}
        },
        "required": ["query"]
    },
    "execute": lambda args, token, logger: knowledge_service.query_docs(args["query"])
}