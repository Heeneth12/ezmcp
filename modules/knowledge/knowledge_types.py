from dataclasses import dataclass


@dataclass
class KnowledgeChunk:
    id: str
    heading: str
    content: str
    source: str
    category: str
