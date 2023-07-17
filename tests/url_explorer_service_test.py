import pytest
import requests
import redis
from unittest.mock import MagicMock
from queue import Queue

from requests import RequestException

from exceptions.url_not_found_exception import UrlNotFoundException
from repositories.url_repository import UrlRepository
from service.url_explorer_service import UrlExplorerService


@pytest.fixture
def url_explorer():
    url_explorer = UrlExplorerService()
    url_explorer.redis_client = MagicMock(redis.Redis)
    url_explorer.url_repository = MagicMock(UrlRepository)
    url_explorer.session = MagicMock(requests.Session)
    return url_explorer


def test_fetch_url_valid_url(url_explorer):
    response = requests.Response()
    response._content = "<html><body></body></html>".encode("utf-8")
    response.status_code = 200
    url_explorer.session.get.return_value = response

    url, html = url_explorer.fetch_url("https://test.com")

    assert html.encode("utf-8") == response._content


def test_fetch_url_403_received(url_explorer):
    url_explorer.session.get.return_value = MagicMock()
    response = requests.Response()
    response.status_code = 403
    url_explorer.session.get.return_value.raise_for_status.side_effect = RequestException(response=response)

    url_explorer.fetch_url("https://test.com")

    assert url_explorer.session.get.call_count > 1


def test_fetch_url_502_received(url_explorer):
    url_explorer.session.get.return_value = MagicMock()
    response = requests.Response()
    response.status_code = 502
    url_explorer.session.get.return_value.raise_for_status.side_effect = RequestException(response=response)

    url_explorer.fetch_url("https://test.com")

    assert url_explorer.session.get.call_count > 1



def test_parse_urls_from_html(url_explorer):
    html = "<html><body><a href='https://invalidLink987.com'>Link</a></body></html>"
    urls = url_explorer.parse_urls_from_html(html)
    assert len(urls) == 1

def test_parse_urls_from_html_no_valid_urls(url_explorer):
    html = "<html><body><a href='invalidLink.com'>Link</a></body></html>"
    urls = url_explorer.parse_urls_from_html(html)
    assert len(urls) == 0

def test_crawl_saving_to_db(url_explorer):
    url_explorer.url_queue = Queue()
    url_explorer.redis_client.exists.return_value = False
    response = requests.Response()
    response._content = "<html><body></body></html>".encode("utf-8")
    response.status_code = 200
    url_explorer.session.get.return_value = response
    url_explorer.parse_urls_from_html = MagicMock()

    url_explorer.crawl("https://test.com")

    assert url_explorer.parse_urls_from_html.called
    assert url_explorer.url_repository.upsert_url.called


def test_crawl_fail_saving_to_db(url_explorer):
    url_explorer.url_queue = Queue()
    url_explorer.redis_client.exists.return_value = False
    response = requests.Response()
    response.status_code = 404
    url_explorer.session.get.return_value = response
    url_explorer.parse_urls_from_html = MagicMock()

    url_explorer.crawl("https://test.com")

    assert url_explorer.parse_urls_from_html.not_called
    assert url_explorer.url_repository.upsert_url.not_called


def test_get_html(url_explorer):
    url_explorer.url_repository.find_url.return_value = {"url": "https://test.com",
                                                         "content": "<html><body></body></html>"}
    result = url_explorer.get_html("https://test.com")
    assert result == "<html><body></body></html>"

    url_explorer.url_repository.find_url.return_value = None
    with pytest.raises(UrlNotFoundException):
        url_explorer.get_html("https://test.com")
