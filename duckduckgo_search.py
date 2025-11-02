import requests
from bs4 import BeautifulSoup

class DuckDuckGoSearcher:
    def __init__(self):
        self.base_url = 'https://html.duckduckgo.com/html/'
        self.headers = {'User-Agent': 'Mozilla/5.0'}

    def search(self, query) -> list[dict[str, str]]:
        params = {'q': query}
        response = requests.post(self.base_url, data=params, headers=self.headers)
        response.raise_for_status()
        html = response.text
        return self._parse_results(html)

    def _parse_results(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        results: list[dict[str, str]] = []
        # Find all result entries
        # Adjust the selectors based on the actual HTML structure of DuckDuckGo's results page
        for result in soup.find_all('div', class_='result'):
            link_tag = result.find('a', class_='result__a')
            snippet_tag = result.find('a', class_='result__snippet') or result.find('div', class_='result__snippet')
            if link_tag:
                title = link_tag.get_text(' ', strip=True)
                href = link_tag.get('href', '')
                snippet = ''
                if snippet_tag:
                    snippet = snippet_tag.get_text(' ', strip=True)
                results.append({
                    "title": title,
                    "href": href,
                    "snippet": snippet
                })
        return results

