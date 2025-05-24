from pocketflow import Flow
from nodes_youtube import (
    YouTubeInputNode,
    TranscriptNode,
    TopicExtractionNode,
    QAGenerationNode,
    SimplifyNode,
    HTMLGenerationNode
)

from pocketflow import Node  # Ensure Node is imported

def create_youtube_summary_flow():
    """Create and return a YouTube video summarization flow."""
    input_node = YouTubeInputNode()
    transcript_node = TranscriptNode()
    topic_node = TopicExtractionNode()
    qa_node = QAGenerationNode()
    simplify_node = SimplifyNode()
    html_node = HTMLGenerationNode()

    # EndNode now inherits from Node and implements required methods
    class EndNode(Node):
        def prep(self, shared):
            return None
        def exec(self, prep_res):
            return None
        def post(self, shared, prep_res, exec_res):
            print("Flow ended early: No transcript available.")
            html = """
            <html><head><title>Video Summary</title></head><body>
            <h1>Video Summary</h1>
            <p style='color:red;'>No transcript available for this video. Unable to generate summary.</p>
            </body></html>
            """
            # Write to file for consistency
            with open("summary.html", "w", encoding="utf-8") as f:
                f.write(html)
            shared["html_file"] = "summary.html"
            return None
    end_node = EndNode()

    # Wire up the short-circuit action
    transcript_node - "empty_transcript" >> end_node
    input_node >> transcript_node >> topic_node >> qa_node >> simplify_node >> html_node
    return Flow(start=input_node)
