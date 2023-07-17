import threading
import logging
import validators
from flask import request, jsonify, abort, Blueprint

from exceptions.url_not_found_exception import UrlNotFoundException
from service.url_explorer_service import UrlExplorerService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scrape_bp = Blueprint('scrape', __name__)

url_explorer_service = UrlExplorerService()


# todo implement celery?

@scrape_bp.route('/scrape', methods=['POST'])
def scrape_page():
    url = request.get_json().get('url')
    if not validators.url(url):
        logger.error(f"Received an invalid url {url}")
        abort(400, "Received an invalid url")
    logger.info(f"Received request to scrap urls for: {url}")
    thread = threading.Thread(target=url_explorer_service.crawl, args=(url,))
    thread.start()
    response = {'message': 'Request accepted and processing started'}
    return jsonify(response), 202


@scrape_bp.route('/html', methods=['GET'])
def get_html_for_url():
    url = request.get_json().get('url')
    if not validators.url(url):
        logger.error(f"Received an invalid url {url}")
        abort(400, "Received an invalid url")
    logger.info(f"received request to get HTML for url: {url}")
    try:
        html = url_explorer_service.get_html(url)
        logger.info(f"html successfully found for url: {url}")
        return html, 200
    except UrlNotFoundException as e:
        logger.error(f"html was not found for url {url}")
        abort(400, description=e.message)
