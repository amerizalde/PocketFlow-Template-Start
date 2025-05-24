from pocketflow import Node
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from utils.call_llm import call_llm
import jinja2
import re

class YouTubeInputNode(Node):
    def exec(self, _):
        url = input("Enter YouTube video URL: ")
        return url
    def post(self, shared, prep_res, exec_res):
        shared["youtube_url"] = exec_res
        return "default"

class TranscriptNode(Node):
    def prep(self, shared):
        return shared["youtube_url"]
    def exec(self, url):
        # Extract video ID from URL
        match = re.search(r"(?:v=|youtu.be/)([\w-]+)", url)
        if not match:
            raise ValueError("Invalid YouTube URL")
        video_id = match.group(1)
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            if not transcript or not isinstance(transcript, list):
                print("Transcript is empty or invalid.")
                return ""
            text = " ".join([seg["text"] for seg in transcript])
            return text
        except (NoTranscriptFound, TranscriptsDisabled):
            print("No transcript available for this video or transcripts are disabled.")
            return ""
        except Exception as e:
            print(f"Could not fetch transcript: {e}\nThis video may not have a transcript or is restricted.")
            return ""
    def post(self, shared, prep_res, exec_res):
        shared["transcript"] = exec_res
        return "default"

class TopicExtractionNode(Node):
    def prep(self, shared):
        return shared["transcript"]
    def exec(self, transcript):
        prompt = f"""
Extract the most interesting topics from the following transcript. List each topic as a short phrase:

{transcript}

Topics:
"""
        response = call_llm(prompt)
        topics = [t.strip("- ") for t in response.split("\n") if t.strip()]
        return topics
    def post(self, shared, prep_res, exec_res):
        shared["topics"] = exec_res
        return "default"

class QAGenerationNode(Node):
    def prep(self, shared):
        return {"topics": shared["topics"], "transcript": shared["transcript"]}
    def exec(self, data):
        topics = data["topics"]
        transcript = data["transcript"]
        qa_pairs = []
        for topic in topics:
            prompt = f"""
Based on the transcript below, generate a simple question and a clear, concise answer about the topic: '{topic}'.

Transcript:
{transcript}

Q&A:
"""
            response = call_llm(prompt)
            qa_pairs.append({"topic": topic, "qa": response.strip()})
        return qa_pairs
    def post(self, shared, prep_res, exec_res):
        shared["qa_pairs"] = exec_res
        return "default"

class SimplifyNode(Node):
    def prep(self, shared):
        return shared["qa_pairs"]
    def exec(self, qa_pairs):
        simplified = []
        for item in qa_pairs:
            prompt = f"""
Explain the following Q&A in the simplest, most beginner-friendly way possible:

{item['qa']}
"""
            simple = call_llm(prompt)
            simplified.append({"topic": item["topic"], "qa": simple.strip()})
        return simplified
    def post(self, shared, prep_res, exec_res):
        shared["simplified_qa"] = exec_res
        return "default"

class HTMLGenerationNode(Node):
    def prep(self, shared):
        return shared["simplified_qa"]
    def exec(self, simplified_qa):
        template = """
        <html>
        <head><title>YouTube Video Summary</title></head>
        <body>
        <h1>Video Summary</h1>
        {% for item in qa_list %}
          <h2>{{ item.topic }}</h2>
          <p>{{ item.qa }}</p>
        {% endfor %}
        </body>
        </html>
        """
        html = jinja2.Template(template).render(qa_list=simplified_qa)
        with open("summary.html", "w", encoding="utf-8") as f:
            f.write(html)
        return "summary.html"
    def post(self, shared, prep_res, exec_res):
        shared["html_file"] = exec_res
        print(f"Summary HTML generated: {exec_res}")
