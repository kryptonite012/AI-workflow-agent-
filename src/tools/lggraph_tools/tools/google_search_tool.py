from typing import Any


# this is tools for making searches on Google using google search api
def search_google_tool(query: str) -> Any | None:
    # make simple request to google search api
    import requests
    from dotenv import load_dotenv
    import os

    load_dotenv()

    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cx = os.getenv("CX")

    url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={query}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()
        return data
        # print(data, f"\n\n\n\n ")
        # Process the search results
        # if 'items' in data:
        #     for item in data['items']:
        #         print(f"Title: {item['title']}")
        #         print(f"Link: {item['link']}")
        #         print(f"Snippet: {item['snippet']}\n")
        # else:
        #     print("No results found.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while making the request: {e}")
        return None


if __name__ == "__main__":
    # Example usage of the search_tool function
    query = "narendra modi"
    print(f"Search initiated for query: {query} : result: {search_google_tool(query)}")
