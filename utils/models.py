def get_ollama_models():
    try:
        import requests
        resp = requests.get('http://192.168.0.250:11434/api/tags', timeout=3)
        resp.raise_for_status()
        return [m["name"] for m in resp.json()['models']]
    except Exception:
        return []

ollama_models = get_ollama_models()

if __name__ == "__main__":
    print("Available models:", ollama_models or "None")