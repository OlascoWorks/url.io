from flask import jsonify, request, redirect, url_for
from datetime import datetime, timedelta
from website.models import User, RefreshToken
from website.api import BASE_URL
from website import db
from functools import wraps
import os, jwt, uuid, requests, random, string, json

# decorator for verifying the JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'X-access-token' in request.cookies:
            token = request.cookies['X-access-token']

        # set to arbitrary value if token is not passed
        if not token:
            token = 'No-ToKeN1234'
  
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, os.environ.get('JWT_SECRET'), algorithms=["HS256"])
            expiration = data['exp']
            # covert expiration to datetime
            expiration = datetime.fromtimestamp(expiration)
            if expiration < datetime.now():
                currentUser = User.query\
                    .filter_by(id = data['id'])\
                    .first()
                #check if token expiration is less than 30 seconds
                if expiration < (datetime.now() + timedelta(seconds=30)):
                    access_token = create_access_token(data={
                        "id": currentUser.id,
                        "exp": datetime.now() + timedelta(minutes=3)
                    })
                else:  access_token = request.cookies['X-access-token']
            else:
                currentUser = None
                access_token = request.cookies['X-access-token']
        except Exception as e:
            if token != 'No-ToKeN1234':
                return jsonify({
                    'message' : 'Token is invalid !!',
                    'error' : str(e)
                }), 401
            else:
                currentUser = None
                access_token = 'No-ToKeN1234'
        
        # returns the current logged in users context to the routes
        return  f(currentUser, access_token, *args, **kwargs)
  
    return decorated

# write a function that generates a new access token
def create_access_token(data):
    access_token = jwt.encode(data, os.environ.get('JWT_SECRET'))
    return access_token

#write a function that generates a new refresh token
def generate_refresh_token(user_id):
    refresh_token = RefreshToken(token=uuid.uuid4().hex, user_id=user_id)
    db.session.add(refresh_token)
    db.session.commit()

    return refresh_token

def try_refresh():
    refresh_url = BASE_URL + '/auth/refresh'
    res = requests.post(refresh_url, cookies={
        'session': request.cookies['session'],
        'X-refresh-token': request.cookies['X-refresh-token']
    })

    data = json.loads(res.text)
    if data['message'] != "Refreshed successfully":
        return redirect(url_for('auth.login')), 400
    
    return
    
def make_error_response(error_text):
    class_name = ''.join(random.choice(string.ascii_letters) for i in range(8))
    dismiss_name = ''.join(random.choice(string.ascii_letters) for i in range(8))
    respone = f"""
<div
        role="alert"
        class="relative left-1/2 -translate-x-1/2 mt-5 flex items-center max-w-max px-4 py-2 text-xs text-white bg-red-500 rounded-lg font-light {class_name}"
        id="alert"
        data-dismissible="alert"
        >
            <div class="mr-12" id="text">{error_text}</div>
            <button
                role="button"
                data-dismissible-target="alert"
                class="!absolute right-3 h-6 max-h-[32px] w-6 max-w-[32px] select-none rounded-lg text-center align-middle font-sans text-xs font-medium uppercase text-white transition-all hover:bg-white/10 active:bg-white/30 disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none {dismiss_name}"
                id="dismiss-btn"
            >
                <span class="absolute transform -translate-x-1/2 -translate-y-1/2 top-1/2 left-1/2">
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    class="w-4 h-"
                    stroke-width="2"
                >
                    <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                    ></path>
                </svg>
                </span>
            </button>

            <script>
                dismissBtn = document.querySelector('.{dismiss_name}');
                let alertDiv = document.querySelector('.{class_name}');

                dismissBtn.addEventListener('click', () => {{
                    alertDiv.classList.add('!hidden');
                }});

                setTimeout(() => {{
                    alertDiv.classList.add('!hidden');
                }}, 5000);
            </script>
        </div>
            """
    
    return respone