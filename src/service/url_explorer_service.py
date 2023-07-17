import concurrent
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import time
from bs4 import BeautifulSoup
import requests
import redis
import logging
from exceptions.url_not_found_exception import UrlNotFoundException
from repositories.url_repository import UrlRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_EXPIRATION_SECONDS = 3600





class UrlExplorerService:
    def __init__(self):
        self.url_queue = Queue()
        self.url_repository = UrlRepository()
        self.session = requests.Session()
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)

    def parse_urls_from_html(self, html_content):
        urls_found = []
        soup = BeautifulSoup(html_content, 'html.parser')
        links = soup.find_all('a')
        for link in links:
            href = link.get('href')
            if href and href.startswith('http'):
                urls_found.append(href)
        return urls_found

    def fetch_url(self, url, max_retries=3):
        retries = 0
        delay_seconds = 1
        headers = {}
        while retries < max_retries:
            try:
                response = self.session.get(url, headers=headers)
                response.raise_for_status()
                return url, response.text
            except requests.exceptions.RequestException as e:
                error_code = getattr(e.response, 'status_code', None)
                if error_code == 403:
                    logger.error(f"Got a 403 Forbidden, retrying with browser headers for url: {url}")
                    retries += 1
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'
                    }
                    logger.info(f"Retrying in {delay_seconds} seconds...")
                    time.sleep(delay_seconds)
                    delay_seconds *= 2
                    continue
                if error_code in [500, 502, 503, 504]:
                    logger.error(f"Got a server error worth retrying for url: {url}")
                    retries += 1
                    logger.info(f"Retrying in {delay_seconds} seconds...")
                    time.sleep(delay_seconds)
                    delay_seconds *= 2
                else:
                    logger.error(f"Got a fatal error for url: {url}, error: {e}")
                    return None

    def mark_url_as_visited(self, url, expiration_seconds):
        self.redis_client.setex(url, expiration_seconds, "visited")

    def is_url_visited(self, url):
        return self.redis_client.exists(url)

    def crawl(self, seed_url):
        logger.info(f"Crawling seed url: {seed_url}")

        self.url_queue.put(seed_url)

        with ThreadPoolExecutor() as executor:
            futures = []
            while not self.url_queue.empty():
                url = self.url_queue.get()
                logger.info(f"will start exploring url {url}")

                if self.is_url_visited(url):
                    logger.info(f"url was found in the cache, no processing will be done: {url}")
                    continue

                self.mark_url_as_visited(url, CACHE_EXPIRATION_SECONDS)

                future = executor.submit(self.fetch_url, url)
                futures.append(future)

                for completed_future in concurrent.futures.as_completed(futures):
                    url_result = completed_future.result()
                    if url_result:
                        url, html_content = url_result
                        logger.info(f"html found for url {url}, will start parsing its links")
                        urls_found = self.parse_urls_from_html(html_content)
                        for url_found in urls_found:
                            self.url_queue.put(url_found)
                        self.url_repository.upsert_url(url=url, content=html_content)
                        logger.info(f"saved html for url {url} to db")
                    else:
                        logger.error(f"no html content could have been fetched for url: {url}")

    def get_html(self, url):
        url = self.url_repository.find_url(url)
        if url:
            return url.get('content')
        else:
            raise UrlNotFoundException()
