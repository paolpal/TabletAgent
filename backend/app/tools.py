import ipaddress
import json
import os
import socket
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import httpx
from ddgs import DDGS
from langchain_core.tools import tool


@tool
def current_date() -> str:
    """Return the current date and time in the configured local timezone."""
    zone = os.environ.get('TZ', 'Europe/Rome')
    return datetime.now(ZoneInfo(zone)).isoformat(timespec='seconds') + ' (' + zone + ')'


@tool
def search_web(query: str) -> str:
    """Search the web for current information and return titles, links, and excerpts."""
    try:
        results = DDGS(timeout=10).text(query[:300], region='it-it', max_results=5)
        return json.dumps(results, ensure_ascii=False)
    except Exception:
        return 'Ricerca web non disponibile. Riprova più tardi.'


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ignored = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript', 'svg'):
            self.ignored += 1
        elif tag in ('p', 'div', 'br', 'li', 'h1', 'h2', 'h3'):
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript', 'svg') and self.ignored:
            self.ignored -= 1

    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)


@tool
def read_web_page(url: str) -> str:
    """Read the text of a public HTTP or HTTPS page. Provide the complete URL."""
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
            return 'Indirizzo non valido.'
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80), type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(entry[4][0]).is_global for entry in addresses):
            return 'Sono accessibili solo indirizzi Internet pubblici.'
        with httpx.Client(timeout=12, follow_redirects=False, trust_env=False) as client:
            with client.stream('GET', url, headers={'User-Agent': 'TabletAgent/1.0'}) as response:
                response.raise_for_status()
                if response.is_redirect:
                    return 'La pagina reindirizza a ' + response.headers.get('location', '') + '. Apri il nuovo indirizzo se pubblico.'
                content_type = response.headers.get('content-type', '')
                if 'text/html' not in content_type and 'text/plain' not in content_type:
                    return 'Formato della pagina non supportato.'
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > 1000000:
                        break
                    chunks.append(chunk)
        text = b''.join(chunks).decode('utf-8', errors='replace')
        if 'text/html' in content_type:
            parser = TextExtractor()
            parser.feed(text)
            text = ' '.join(''.join(parser.parts).split())
        return text[:16000] or 'Pagina vuota.'
    except Exception:
        return 'Impossibile leggere la pagina.'
