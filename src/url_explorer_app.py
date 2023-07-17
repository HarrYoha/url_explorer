from flask import Flask
import logging
from controller.url_controller import scrape_bp


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.register_blueprint(scrape_bp)

if __name__ == '__main__':
    app.run()


