from flask import request, session
from flask_login import current_user, login_required
from website import db
from website.api import url
from website.api.user.controllers import token_required, make_error_response, try_refresh
from .controllers import get_all_urls, create_all_xxcrf_urls, change_status
from website.models import Url, User
import shortuuid, re
from datetime import datetime

@url.route('/create', methods=['POST'])
def create_url():
    user = current_user
    original_url = request.form.get('url')
    url_pattern = "^https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$"

    if re.match(url_pattern, original_url):
        url = None
        if user.is_authenticated:  url = Url.query.filter_by(original_url=original_url, user_id=user.id).first()
        else:
            try:
                for _url in session['xxcrf_urls']:
                    if original_url == _url['original_url']:
                        url = _url
                        break
            except:  pass
        if url:  return make_error_response("url already shortened"), 400

        new_url = shortuuid.ShortUUID().random(length=8)
        date = datetime.now()

        if user.is_authenticated:
            newUrl = Url(original_url=original_url, new_url=new_url, user_id=user.id)
            db.session.add(newUrl)
            db.session.commit()
        else:
            try:  all_urls = session['xxcrf_urls']
            except:  all_urls = None
            
            if not all_urls:
                urls = []
            else:  urls = all_urls

            url_count = len(urls)

            if url_count >= 5:
                return make_error_response("Limit reached"), 400
            else:
                urls.append({'original_url': original_url, 'new_url': new_url, 'date': date })

            session['xxcrf_urls'] = urls

        if len(original_url) > 60:  filler = '...'
        else:  filler = ''
        return f"""
            <tr class="t-row">
                <td><a href="{ new_url }" target="_blank" rel="noopener noreferrer">{ new_url }</a></td>
                <td><a href="{ original_url }" target="_blank" rel="noopener noreferrer">{ original_url[:60] }</a>{ filler }</td>
                <td>0</td>
                <td class="status !cursor-not-allowed mobile:hidden">Active
                    <svg width="26" height="25" viewBox="0 0 36 35" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="0.25" width="35" height="35" rx="17.5" fill="#1EB036" fill-opacity="0.14"/>
                    <path d="M25.6895 17.875L22.0273 21.5371C20.5625 23.002 18.1895 23.002 16.7539 21.5371C15.3477 20.1309 15.2598 17.9043 16.5488 16.4395L16.7246 16.2637C16.8711 16.0586 17.1934 16.0293 17.3691 16.2051C17.5742 16.3809 17.6035 16.6738 17.4277 16.8789L17.2812 17.0547C16.3145 18.168 16.373 19.8379 17.3984 20.8633C18.5117 21.9766 20.2695 21.9766 21.3828 20.8633L25.0156 17.2305C26.1289 16.1172 26.1289 14.3594 25.0156 13.2461C23.9316 12.1621 22.1445 12.1621 21.0605 13.2461L20.3867 13.9199C20.2109 14.0957 19.918 14.0957 19.7129 13.9199C19.5371 13.7148 19.5371 13.4219 19.7129 13.2461L20.3867 12.5723C21.8516 11.1074 24.2246 11.1074 25.6895 12.5723C27.1543 14.0371 27.1543 16.4102 25.6895 17.875ZM9.78125 17.875L13.4434 14.2422C14.9082 12.7773 17.252 12.7773 18.7461 14.2422C20.123 15.6191 20.2109 17.8457 18.9219 19.3398L18.7461 19.5156C18.5996 19.7207 18.3066 19.75 18.1016 19.5742C17.8965 19.3984 17.8672 19.1055 18.043 18.9004L18.2188 18.7246C19.1562 17.6113 19.0977 15.9414 18.0723 14.916C16.959 13.8027 15.2012 13.8027 14.0879 14.916L10.4551 18.5488C9.3418 19.6621 9.3418 21.4199 10.4551 22.5332C11.5391 23.6172 13.3262 23.6172 14.4102 22.5332L15.084 21.8594C15.2598 21.6836 15.5527 21.6836 15.7578 21.8594C15.9336 22.0352 15.9336 22.3574 15.7578 22.5332L15.084 23.1777C13.6191 24.6426 11.2461 24.6426 9.78125 23.1777C8.31641 21.7129 8.31641 19.3398 9.78125 17.875Z" fill="#C9CED6"/>
                    </svg>                             
                </td>
                <td>{ date.strftime('%m-%d-%Y') }</td>
            </tr>
            <tr id="extra"></tr>
        """
    else:
        return make_error_response("Please provide a valid url"), 400

@url.route('/all/<user_id>', methods=['GET'])
def get_all_urls(user_id):
    try:
        urls = get_all_urls(user_id)

        return urls
    except Exception as e:
        return f"<h3>An internal error occurred! : {str(e)}</h3>", 500
    
@url.route('/all/create', methods=['POST'])
@login_required
def create_all_xxcrf_urls():
    if session['xxcrf_urls']:
        try:
            user = current_user
            urls = session['xxcrf_urls']

            create_all_xxcrf_urls(user.id, urls)

            return "ok"
        except Exception as e:
            return f"<h3>An internal error occurred! : {str(e)}</h3>", 500
        
@url.route('/<url_id>/status/change', methods=['POST'])
@login_required
def change(url_id):
    size = request.args.get('size')
    status = Url.query.filter_by(id=url_id).first().status

    new_status = change_status(url_id, status)

    if size == 'mobile':  w_h = (15, 16)
    else:  w_h = (25, 26)

    if new_status == 1:
        current_status = 'Active'
        svg = f"""
            <svg width="{ w_h[0] }" height="{ w_h[1] }" viewBox="0 0 36 35" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="0.25" width="35" height="35" rx="17.5" fill="#1EB036" fill-opacity="0.14"/>
                <path d="M25.6895 17.875L22.0273 21.5371C20.5625 23.002 18.1895 23.002 16.7539 21.5371C15.3477 20.1309 15.2598 17.9043 16.5488 16.4395L16.7246 16.2637C16.8711 16.0586 17.1934 16.0293 17.3691 16.2051C17.5742 16.3809 17.6035 16.6738 17.4277 16.8789L17.2812 17.0547C16.3145 18.168 16.373 19.8379 17.3984 20.8633C18.5117 21.9766 20.2695 21.9766 21.3828 20.8633L25.0156 17.2305C26.1289 16.1172 26.1289 14.3594 25.0156 13.2461C23.9316 12.1621 22.1445 12.1621 21.0605 13.2461L20.3867 13.9199C20.2109 14.0957 19.918 14.0957 19.7129 13.9199C19.5371 13.7148 19.5371 13.4219 19.7129 13.2461L20.3867 12.5723C21.8516 11.1074 24.2246 11.1074 25.6895 12.5723C27.1543 14.0371 27.1543 16.4102 25.6895 17.875ZM9.78125 17.875L13.4434 14.2422C14.9082 12.7773 17.252 12.7773 18.7461 14.2422C20.123 15.6191 20.2109 17.8457 18.9219 19.3398L18.7461 19.5156C18.5996 19.7207 18.3066 19.75 18.1016 19.5742C17.8965 19.3984 17.8672 19.1055 18.043 18.9004L18.2188 18.7246C19.1562 17.6113 19.0977 15.9414 18.0723 14.916C16.959 13.8027 15.2012 13.8027 14.0879 14.916L10.4551 18.5488C9.3418 19.6621 9.3418 21.4199 10.4551 22.5332C11.5391 23.6172 13.3262 23.6172 14.4102 22.5332L15.084 21.8594C15.2598 21.6836 15.5527 21.6836 15.7578 21.8594C15.9336 22.0352 15.9336 22.3574 15.7578 22.5332L15.084 23.1777C13.6191 24.6426 11.2461 24.6426 9.78125 23.1777C8.31641 21.7129 8.31641 19.3398 9.78125 17.875Z" fill="#C9CED6"/>
            </svg>
        """
    else:
        current_status = 'Inactive'
        svg = f"""<svg width="{ w_h[0] }" height="{ w_h[1] }" viewBox="0 0 36 35" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="0.25" width="35" height="35" rx="17.5" fill="#B0901E" fill-opacity="0.19"/>
                    <path d="M9.10742 10.4922L26.9492 24.5547C27.125 24.7012 27.1836 25.0234 27.0078 25.1992C26.8613 25.4043 26.5684 25.4629 26.3633 25.2871L8.55078 11.2246C8.3457 11.0781 8.28711 10.7559 8.46289 10.5801C8.60938 10.375 8.93164 10.3164 9.10742 10.4922ZM25.6895 17.875L23.5215 20.0723L22.7891 19.4863L25.0156 17.2305C26.1289 16.1172 26.1289 14.3594 25.0156 13.2461C23.9316 12.1621 22.1445 12.1621 21.0605 13.2461L20.3867 13.9199C20.2109 14.0957 19.918 14.0957 19.7129 13.9199C19.5371 13.7148 19.5371 13.4219 19.7129 13.2461L20.3867 12.5723C21.8516 11.1074 24.2246 11.1074 25.6895 12.5723C27.1543 14.0371 27.1543 16.4102 25.6895 17.875ZM20.5039 22.4746C19.2148 22.8555 17.7793 22.5625 16.7539 21.5371C15.9629 20.7461 15.582 19.6914 15.6699 18.6367L16.6367 19.3984C16.7246 19.9551 16.9883 20.4531 17.3984 20.8633C17.9844 21.4492 18.7754 21.7422 19.5371 21.6836L20.5039 22.4746ZM18.0723 14.916V14.8867C17.4863 14.3301 16.6953 14.0371 15.9336 14.0664L14.9668 13.3047C16.2559 12.9238 17.7207 13.2168 18.7168 14.2422C19.5078 15.0332 19.8887 16.0879 19.8301 17.1426L18.834 16.3809C18.7461 15.8242 18.4824 15.3262 18.0723 14.916ZM12.7109 16.293L10.4551 18.5488C9.3418 19.6621 9.3418 21.4199 10.4551 22.5332C11.5391 23.6172 13.3262 23.6172 14.4102 22.5332L15.084 21.8594C15.2598 21.6836 15.5527 21.6836 15.7578 21.8594C15.9336 22.0352 15.9336 22.3574 15.7578 22.5332L15.084 23.1777C13.6191 24.6426 11.2461 24.6426 9.78125 23.1777C8.31641 21.7129 8.31641 19.3398 9.78125 17.875L11.9492 15.707L12.7109 16.293Z" fill="#B0901E"/>
                </svg>"""
        

    return f"""
        <td class="status !cursor-pointer" hx-post="/url/{ url_id }/status/change?size={ size }" hx-trigger="click" hx-swap="outerHTML">{ current_status }
            { svg }                                
        </td>
    """