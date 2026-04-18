from .knowledge_service import KnowledgeService

knowledge_service = KnowledgeService()

search_documentation_tool = {
    "name": "search_documentation",
    "description": "Search the internal EZ Inventory manual for help with features, settings, or business logic.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search term or question about how the system works"}
        },
        "required": ["query"]
    },
    "execute": lambda args, token: knowledge_service.query_docs(args["query"])
}