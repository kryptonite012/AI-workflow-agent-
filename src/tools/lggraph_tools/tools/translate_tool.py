def translate_text(message: str, target_language: str) -> str | None:
    import requests
    from src.config import settings

    """
    Translates the given message to the target language using an external translation service.
    """
    try:
        url = settings.TRANSLATION_API_URL
        data = {
            "q": message,
            "source": "auto",
            "target": target_language,
            "format": "text",
        }
        response = requests.post(url, json=data)

        return response.json().get("translatedText", None)
    except requests.RequestException as e:
        print(f"An error occurred while making the request: {e}")
        return None
