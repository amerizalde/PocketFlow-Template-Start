import re
from pocketflow import Node
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from utils.call_llm import call_llm

# Simple in-memory cache for transcripts (can be replaced with diskcache)
_transcript_cache = {}

def get_video_id(url):
    match = re.search(r"(?:v=|youtu.be/)([\w-]+)", url)
    if not match:
        raise ValueError("Invalid YouTube URL")
    return match.group(1)

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
        video_id = get_video_id(url)
        # Check cache first
        if video_id in _transcript_cache:
            return _transcript_cache[video_id]
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([x["text"] for x in transcript])
            _transcript_cache[video_id] = transcript_text
            return transcript_text
        except (NoTranscriptFound, TranscriptsDisabled):
            # Fallback to Whisper ASR
            transcript_text = self.whisper_asr_fallback(video_id)
            _transcript_cache[video_id] = transcript_text
            return transcript_text
        except Exception as e:
            print(f"Transcript extraction failed: {e}")
            return ""

    def whisper_asr_fallback(self, video_id):
        # TODO: Implement Whisper ASR fallback here
        print("[ASR fallback not implemented: returning empty transcript]")
        return ""

    def post(self, shared, prep_res, exec_res):
        shared["transcript"] = exec_res
        if not exec_res.strip():
            return "empty_transcript"
        return "default"

class TopicExtractionNode(Node):
    def prep(self, shared):
        return shared["transcript"]
    def exec(self, transcript):
        if not transcript.strip():
            return []
        # Batch topic extraction in one LLM call
        prompt = f"""
Extract the most interesting topics from the following transcript. List each topic as a short phrase, one per line:\n\n{transcript}\n\nTopics:\n"""
        response = call_llm(prompt)
        # Parse topics as lines
        topics = [line.strip("- ") for line in response.strip().splitlines() if line.strip()]
        return topics
    def post(self, shared, prep_res, exec_res):
        shared["topics"] = exec_res
        return "default"

class QAGenerationNode(Node):
    def prep(self, shared):
        # Prepare all Q&A prompts as a batch
        topics = shared.get("topics", [])
        transcript = shared.get("transcript", "")
        return [(topic, transcript) for topic in topics]
    def exec(self, topic_transcript_pairs):
        # Batch Q&A generation (can be parallelized in future)
        qa_pairs = []
        for topic, transcript in topic_transcript_pairs:
            prompt = f"""
For the topic: '{topic}', generate a question and a detailed answer based on the transcript below.\n\nTranscript:\n{transcript}\n\nQ&A:\n"""
            response = call_llm(prompt)
            qa_pairs.append({"topic": topic, "qa": response})
        return qa_pairs
    def post(self, shared, prep_res, exec_res):
        shared["qa_pairs"] = exec_res
        return "default"

class SimplifyNode(Node):
    def prep(self, shared):
        # Prepare all Q&A for simplification
        return shared.get("qa_pairs", [])
    def exec(self, qa_pairs):
        # Batch simplification (can be parallelized in future)
        simplified = []
        for qa in qa_pairs:
            prompt = f"""
Simplify the following Q&A for a general audience.\n\n{qa['qa']}\n\nSimplified version:\n"""
            response = call_llm(prompt)
            simplified.append({"topic": qa["topic"], "simplified": response})
        return simplified
    def post(self, shared, prep_res, exec_res):
        shared["simplified_qa"] = exec_res
        return "default"

class HTMLGenerationNode(Node):
    def prep(self, shared):
        return shared.get("simplified_qa", [])
    def exec(self, simplified_qa):
        # Generate HTML summary
        html = ["<html>\n<head><title>YouTube Video Summary</title></head>\n<body>"]
        html.append("<h1>Video Summary</h1>")
        for i, qa in enumerate(simplified_qa, 1):
            html.append(f"<h2>{i}. {qa['topic']}</h2>")
            html.append(f"<p>{qa['simplified']}</p>")
        html.append("</body>\n</html>")
        # Write to file
        filename = "summary.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(html))
        print(f"Summary HTML generated: {filename}")
        return filename
    def post(self, shared, prep_res, exec_res):
        shared["html_file"] = exec_res
        return "default"
