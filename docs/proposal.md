# Proposal: Optimizing YouTube Video Summarizer

## 1. Problem Statement

The current system is slow due to:
- Sequential LLM calls for each topic and Q&A.
- No fallback for videos without transcripts.
- No batching, parallelization, or caching.

## 2. Goals

- **Reduce total runtime** for summarizing a video.
- **Increase robustness** (handle videos without transcripts).
- **Maintain or improve output quality**.

## 3. Proposed Changes

### A. Dependencies

- **Add**:  
  - `openai-whisper` or `faster-whisper` (for ASR fallback).
  - `concurrent.futures` (standard lib, for parallelization).
  - `diskcache` or similar (optional, for caching).

### B. Transcript Extraction

- Try `youtube-transcript-api` first.
- If not available, **download audio and transcribe with Whisper** (local or API).
- Cache transcripts by video ID.

### C. LLM Calls

- **Batch LLM calls** where possible (e.g., extract all topics in one call, generate all Q&A in one call).
- **Parallelize** independent LLM calls using `ThreadPoolExecutor` or `ProcessPoolExecutor`.
- Optionally, cache LLM responses for repeated runs.

### D. Flow Improvements

- **Short-circuit** the flow if transcript is empty.
- Optionally, allow user to select which steps to run (for debugging or partial runs).

### E. Example Optimized Flow

```mermaid
flowchart LR
    input[YouTube URL] --> transcript[Get Transcript or ASR]
    transcript --> topics[Extract Topics (LLM)]
    topics --> qa[Batch Q&A Generation (LLM, Parallel)]
    qa --> simplify[Batch Simplification (LLM, Parallel)]
    simplify --> html[Generate HTML]