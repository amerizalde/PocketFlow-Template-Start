import sys
import os
# Ensure parent directory is in sys.path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
import builtins
import contextlib

# Redirect all stdout/stderr to test_log.txt for debugging
test_log_path = os.path.join(os.path.dirname(__file__), '..', 'test_log.txt')
log_file = open(test_log_path, 'a', encoding='utf-8')
@contextlib.contextmanager
def log_output():
    import sys
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = log_file
    try:
        yield
    finally:
        sys.stdout, sys.stderr = old_out, old_err

with log_output():
    print('Starting test_youtube_flow.py')
    try:
        # Test suite for YouTube summarization flow optimizations
        from youtube_flow import create_youtube_summary_flow

        class DummyInput:
            """Monkeypatch input() for testing."""
            def __init__(self, responses):
                self.responses = responses
                self.idx = 0
            def __call__(self, prompt=None):
                resp = self.responses[self.idx]
                self.idx += 1
                return resp

        def test_youtube_summary_flow(monkeypatch=None):
            """Test the YouTube summarization flow for runtime and output quality."""
            # Use a known YouTube video with transcript
            test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            shared = {}
            # Monkeypatch input()
            if monkeypatch:
                monkeypatch.setattr("builtins.input", DummyInput([test_url]))
            else:
                builtins.input = DummyInput([test_url])
            flow = create_youtube_summary_flow()
            start = time.time()
            flow.run(shared)
            elapsed = time.time() - start
            html = shared.get("html_file") or shared.get("html")
            # If html is a filename, read its contents
            if isinstance(html, str) and html.endswith('.html'):
                with open(html, "r", encoding="utf-8") as f:
                    html_content = f.read()
            else:
                html_content = html
            if html_content is None:
                raise AssertionError("Flow did not produce any HTML output. Possible early exit or error in flow.")
            if "Video Summary" not in html_content:
                print("\n--- HTML OUTPUT START ---\n" + str(html_content) + "\n--- HTML OUTPUT END ---\n")
            assert "Video Summary" in html_content, "HTML output missing expected content."
            print(f"Test passed in {elapsed:.2f} seconds. Output size: {len(html_content)} bytes.")

        def test_transcript_fallback(monkeypatch=None):
            """Test that ASR fallback is triggered for videos with no transcript."""
            # Use a fake video ID to force fallback
            test_url = "https://www.youtube.com/watch?v=FAKEID12345"
            shared = {}
            if monkeypatch:
                monkeypatch.setattr("builtins.input", DummyInput([test_url]))
            else:
                builtins.input = DummyInput([test_url])
            flow = create_youtube_summary_flow()
            flow.run(shared)
            html = shared.get("html_file") or shared.get("html")
            if isinstance(html, str) and html.endswith('.html'):
                with open(html, "r", encoding="utf-8") as f:
                    html_content = f.read()
            else:
                html_content = html
            assert "Video Summary" in html_content, "HTML output missing expected content (fallback)."
            print("ASR fallback test passed.")

        def test_transcript_caching(monkeypatch=None):
            """Test that transcript caching speeds up repeated runs."""
            test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            shared = {}
            if monkeypatch:
                monkeypatch.setattr("builtins.input", DummyInput([test_url]))
            else:
                builtins.input = DummyInput([test_url])
            flow = create_youtube_summary_flow()
            import time
            start = time.time()
            flow.run(shared)
            elapsed1 = time.time() - start
            # Run again, should be faster due to cache
            shared2 = {}
            if monkeypatch:
                monkeypatch.setattr("builtins.input", DummyInput([test_url]))
            else:
                builtins.input = DummyInput([test_url])
            start = time.time()
            flow.run(shared2)
            elapsed2 = time.time() - start
            print(f"First run: {elapsed1:.2f}s, Second run (cached): {elapsed2:.2f}s")
            assert elapsed2 < elapsed1, "Transcript caching did not speed up repeated run."
            print("Transcript caching test passed.")

        if __name__ == "__main__":
            test_youtube_summary_flow()
            test_transcript_fallback()
            test_transcript_caching()
    except Exception as e:
        import traceback
        print("Exception occurred:", e)
        traceback.print_exc()
    finally:
        log_file.flush()
        log_file.close()

# Write a marker to the log file to verify file write outside context manager
with open(test_log_path, 'a', encoding='utf-8') as f:
    f.write("\n[LOG END MARKER]\n")
