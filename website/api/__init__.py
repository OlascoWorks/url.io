from flask import Blueprint
import os

views = Blueprint('views', __name__)
url = Blueprint('url', __name__)
auth = Blueprint('auth', __name__)

BASE_URL = os.environ.get('BASE_URL')
BASE_URL = 'http://127.0.0.1:5000' if BASE_URL == None else BASE_URL