from youtube_flow import create_youtube_summary_flow

def main():
    '''Run the YouTube video summarization flow.'''
    shared = {}
    flow = create_youtube_summary_flow()
    flow.run(shared)
    print(f"HTML summary generated: {shared.get('html_file')}")

if __name__ == "__main__":
    main()
