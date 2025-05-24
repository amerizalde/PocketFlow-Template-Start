from pocketflow import Flow
from nodes_youtube import (
    YouTubeInputNode,
    TranscriptNode,
    TopicExtractionNode,
    QAGenerationNode,
    SimplifyNode,
    HTMLGenerationNode
)

def create_youtube_summary_flow():
    """Create and return a YouTube video summarization flow."""
    input_node = YouTubeInputNode()
    transcript_node = TranscriptNode()
    topic_node = TopicExtractionNode()
    qa_node = QAGenerationNode()
    simplify_node = SimplifyNode()
    html_node = HTMLGenerationNode()

    input_node >> transcript_node >> topic_node >> qa_node >> simplify_node >> html_node
    return Flow(start=input_node)
