from flask import session
from website import db
from website.models import Url
# from website.api.user.controllers import token_required

def get_all_urls(user_id):
    urls = Url.query.filter_by(user_id=user_id).all()
    return urls

def get_all_xxcrf_urls():
    try:  urls = session['xxcrf_urls']
    except: return []
    return urls

def create_all_xxcrf_urls(user_id):
    urls = session['xxcrf_urls']
    for url in urls:
        new_url = Url(original_url=url['original_url'], new_url=url['new_url'], user_id=user_id)
        db.session.add(new_url)
        
    db.session.commit()
    session.pop('xxcrf_urls')
    return

def change_status(url_id, status):
    url = Url.query.filter_by(id=url_id).first()

    if status == 1:  url.status = 0
    else:  url.status = 1

    db.session.commit()
    return url.status