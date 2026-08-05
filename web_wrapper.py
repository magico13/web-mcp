import requests
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter
import time
import os

from goggles import GogglesApi

class WebWrapper:
    def __init__(self, goggles: GogglesApi):
        self.goggles = goggles
        # Read cache TTL from environment variable (default 300 seconds / 5 minutes)
        self.cache_ttl = int(os.environ.get("WEB_CACHE_TTL", 300))
        self._web_cache = {}

    def clear_cache(self):
        """Clear the cache of all previously fetched websites"""
        self._web_cache.clear()

    def get_markdown_for_url(self, url: str) -> tuple[int, str, str]:
        """Get the markdown for a website or file at a given URL"""
        try:
            if url in self._web_cache:
                cached_data = self._web_cache[url]
                # Check if cache is still valid based on TTL
                if time.time() - cached_data.get('timestamp', 0) < self.cache_ttl:
                    code = cached_data.get('code', 200)
                    markdown = cached_data.get('markdown', '')
                    description = cached_data.get('description', '')
                    return code, markdown, description
                else:
                    # Cache expired, remove it
                    del self._web_cache[url]
            
            code, text, _, _ = self.get_text_for_url(url)
            if code != 200:
                return code, text, ''
            
            # The result is now cached inside get_text_for_url
            cached_data = self._web_cache[url]
            code = cached_data.get('code', 200)
            markdown = cached_data.get('markdown', '')
            description = cached_data.get('description', '')
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
                cached_data = self._web_cache[url]
                # Check if cache is still valid based on TTL
                if time.time() - cached_data.get('timestamp', 0) < self.cache_ttl:
                    code = cached_data.get('code', 200)
                    text = cached_data.get('text', '')
                    description = cached_data.get('description', '')
                    links = cached_data.get('links', [])
                    return code, text, description, links
                else:
                    # Cache expired, remove it
                    del self._web_cache[url]

            response = requests.get(url, timeout=5)
            content = response.content
            code = response.status_code
            if not response.ok: return code, response.text, description, links
            if response.headers['Content-Type'].startswith('text/html'):
                # website, use beautifulsoup to get the text
                
                #turn content into a string from bytes
                content = content.decode('utf-8', errors='ignore')
                soup = BeautifulSoup(content, 'html.parser')
                if soup.body is None: return code, '', '', []
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
            
            # Cache the result with a timestamp
            self._web_cache[url] = {
                'code': code,
                'text': text, 
                'markdown': markdown, 
                'description': description, 
                'links': links,
                'timestamp': time.time()
            }
            return code, text, description, links # type: ignore
        except Exception as e:
            print("Exception in get_text_for_url: " + str(e))
            return 500, str(e), '', []


