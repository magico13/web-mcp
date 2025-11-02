import requests
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter

from goggles import GogglesApi

class WebWrapper:
    def __init__(self, goggles: GogglesApi):
        self.goggles = goggles
        self._web_cache = {}

    def clear_cache(self):
        """Clear the cache of all previously fetched websites"""
        self._web_cache.clear()

    def get_markdown_for_url(self, url: str) -> tuple[int, str, str]:
        """Get the markdown for a website or file at a given URL"""
        try:
            if url in self._web_cache:
                code = self._web_cache[url].get('code', 200)
                markdown = self._web_cache[url].get('markdown', '')
                description = self._web_cache[url].get('description', '')
                return code, markdown, description
            
            code, text, _, _ = self.get_text_for_url(url)
            if code != 200:
                return code, text, ''
            # must be cached now
            code = self._web_cache[url].get('code', 200)
            markdown = self._web_cache[url].get('markdown', '')
            description = self._web_cache[url].get('description', '')
            return code, markdown, description
        except Exception as e:
            print("Exception in get_markdown_for_url: " + str(e))
            return 500, str(e), ''

    def get_text_for_url(self, url: str) -> tuple[int, str, str, list[str]]:
        """Get the code, text, description, and array of links for a website or file at a given URL"""
        try:
            text = ''
            description = ''
            links = []
            markdown = ''
            if url in self._web_cache:
                text = self._web_cache[url].get('text', '')
                description = self._web_cache[url].get('description', '')
                links = self._web_cache[url].get('links', [])
                return 200, text, description, links
            response = requests.get(url, timeout=5)
            content = response.content
            code = response.status_code
            if not response.ok: return code, response.text, description, links
            if response.headers['Content-Type'].startswith('text/html'):
                # website, use beautifulsoup to get the text
                soup = BeautifulSoup(content, 'html.parser')
                if soup.body is None: return code, '', []
                markdown = MarkdownConverter().convert_soup(soup)
                text = soup.body.text
                # split to newlines and remove leading and trailing spaces on each line
                # skip any empty lines
                text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])
                raw_links = soup.body.find_all('a')
                # only keep the link text and href as a string "link text - link href"
                links = [f'{link.text.strip()} - {link.get("href")}' for link in raw_links]
                # remove links that have no href (href is 'None')
                links = [link for link in links if link.split(' - ')[1] != 'None']
                description = '' # todo: find an appropriate description (site name?)
            else:
                # use goggles to get the text of whatever file this is
                filename = url.split('/')[-1].split('?')[0]
                code, goggles_response = self.goggles.extract_text(filename, content)
                if code < 400:
                    text = goggles_response['text'] # type: ignore
                    description = goggles_response['description'] # type: ignore
                    markdown = text
                else:
                    text = goggles_response
                    description = ''
                    markdown = text
            self._web_cache[url] = {'text': text, 'markdown': markdown, 'description': description, 'links': links}
            return code, text, description, links # type: ignore
        except Exception as e:
            print("Exception in get_text_for_url: " + str(e))
            return 500, str(e), '', []


