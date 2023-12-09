from flask import request, jsonify, redirect, render_template, url_for, make_response, current_app
from flask_login import login_required, logout_user, login_user, current_user
import bcrypt, uuid, re
from datetime import datetime, timedelta
from website import db
from website.models import User, RefreshToken
from website.api.user.controllers import token_required, create_access_token, generate_refresh_token, try_refresh, make_error_response

from website.api import auth, BASE_URL

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')

        user = User.query.filter_by(email=email).first()

        try:
            if user:
                return make_error_response("User already exists"), 400
            if password != confirm_password:
                return make_error_response("Passwords don't match"), 400
            
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

            user_id = uuid.uuid4().hex
            data = {
                "id": user_id,
                "exp": datetime.now() + timedelta(minutes=3)
            }
            new_user = User(id=user_id, name=name, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            access_token = create_access_token(data)
            refresh_token = generate_refresh_token(user_id)
            user = User.query.filter_by(id=user_id).first()
            user.refresh_token = refresh_token
            db.session.commit()

            login_user(new_user, remember=True)
            response = make_response(f"<script>window.location.href='{BASE_URL}'</script>")
            response.set_cookie('X-access-token', value=access_token, expires=datetime.now() + timedelta(minutes=3), secure=True, httponly=True, samesite='Strict')
            response.set_cookie('X-refresh-token', value=str(refresh_token.token), expires=datetime.now() + timedelta(days=3), secure=True, httponly=True, samesite='Strict')

            return response
        except Exception as e:
            print(e)
            return make_error_response("An internal error occurred!"), 500

    return render_template('signup.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user:
            try:
                if bcrypt.checkpw(password.encode('utf-8'), user.password):
                    data = {
                        "id": user.id,
                        "exp": datetime.now() + timedelta(minutes=3)
                    }
                    access_token = create_access_token(data)
                    refresh_token = generate_refresh_token(user.id)

                    user.token = refresh_token
                    db.session.commit()
                    login_user(user)

                    response = make_response(f"<script>window.location.href='{BASE_URL}'</script>")
                    response.set_cookie('X-access-token', value=access_token, expires=datetime.now() + timedelta(minutes=3), secure=True, httponly=True, samesite='Strict')
                    response.set_cookie('X-refresh-token', value=str(refresh_token.token), expires=datetime.now() + timedelta(days=3), secure=True, httponly=True, samesite='Strict')

                    return response
                else:
                    return make_error_response("Invalid password"), 400
            except Exception as e:
                return make_error_response("An internal error occurred!"), 500
        else:
            return make_error_response("User does not exist"), 400
    
    return render_template('login.html')

@auth.route('/logout', methods=['POST'])
@login_required
@token_required
def logout(currentUser, access_token):
    if not currentUser:
        try_refresh()
    
    user = current_user
    refresh_token = RefreshToken.query.filter_by(token=user.token.token).first()
    db.session.delete(refresh_token)
    db.session.commit()

    logout_user()

    response = make_response(f"<script>window.location.href='{BASE_URL}/auth/login'</script>")
    response.delete_cookie('X-access-token')
    response.delete_cookie('X-refresh-token')

    return response

@login_required
def get_current_user():
    return current_user

@auth.route('/refresh', methods=['POST'])
@login_required
def refresh():
    user = current_user
    token = None

    try:
        if 'X-refresh-token' in request.cookies:
            token = request.cookies['X-refresh-token']
        refresh_token = user.token

        if not token:
            return jsonify({"message":"Token is missing"}), 400
        if token != refresh_token.token:
            return jsonify({"message":"Invalid refresh token"}), 400
        if refresh_token.expiration < datetime.now():
            db.session.delete(refresh_token)
            return redirect(url_for('auth.login')), 400
        
        db.session.delete(refresh_token)
        db.session.commit()
        data = {
            "id": user.id,
            "exp": datetime.now() + timedelta(minutes=3)
        }
        access_token = create_access_token(data)
        new_refresh_token = generate_refresh_token(user.id)
        user.token = new_refresh_token
        db.session.commit()

        response = make_response(jsonify({
            "message": "Refreshed successfully",
            "access_token": access_token,
            "refresh_token": new_refresh_token.token
        }))
        response.set_cookie('X-access-token', value=access_token, expires=datetime.now() + timedelta(minutes=3), secure=True, httponly=True, samesite='Strict')
        response.set_cookie('X-refresh-token', value=str(refresh_token.token), expires=datetime.now() + timedelta(days=3), secure=True, httponly=True, samesite='Strict')

        return response
    except Exception as e:
        print(e)
        return f"<h3>An internal error occurred! : {str(e)}. User may already be logged out</h3>", 500

@auth.route('/validate-email', methods=['POST'])
def validate_email():
    email = request.form.get('email')
    email_validate_pattern = r"^\S+@\S+\.\S+$"

    user = User.query.filter_by(email=email).first()

    if user:
        return f"""
        <input type="text" class="w-full h-12 rounded-full bg-bg border-4 border-red-500 text-text text-xs px-14 sm:px-16 py-1 outline-none" placeholder="Enter email here" id="email" name="email"
            hx-post="/auth/validate-email"
            hx-trigger="keyup changed delay:250ms"
            hx-target="#grp"
            hx-swap="innerHTML" value="{email}" required>
            <span class="text-red-500 text-sm font-light mt-3 ml-4">*User aleady exists</span>
        """
    elif not re.match(email_validate_pattern, email):
        return f"""
        <input type="text" class="w-full h-12 rounded-full bg-bg border-4 border-red-500 text-text text-xs px-14 sm:px-16 py-1 outline-none" placeholder="Enter email here" id="email" name="email"
            hx-post="/auth/validate-email"
            hx-trigger="keyup changed delay:250ms"
            hx-target="#grp"
            hx-swap="innerHTML" value="{email}" required>
            <span class="text-red-500 text-sm font-light mt-3 ml-4">*Invalid email</span>
        """
    else:
        return f"""
        <input type="text" class="w-full h-12 rounded-full bg-bg border-4 border-border text-text text-xs px-14 sm:px-16 py-1 outline-none" placeholder="Enter email here" id="email" name="email"
            hx-post="/auth/validate-email"
            hx-trigger="keyup changed delay:250ms"
            hx-target="#grp"
            hx-swap="innerHTML" value="{email}" required>
        """
    

@auth.route('/validate-password', methods=['POST'])
def validate_password():
    password = request.form.get('password')
    password_pattern = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9]).{8,}$"

    if not re.match(password_pattern, password):
        return f"""
        <input type="text" class="w-full h-12 rounded-full bg-bg border-4 border-red-500 text-text text-xs px-14 sm:px-16 py-1 outline-none" placeholder="Enter password here" id="password" name="password"
            hx-post="/auth/validate-password"
            hx-trigger="keyup changed delay:250ms"
            hx-target="#pass-grp"
            hx-swap="innerHTML" value="{password}" required>
            <span class="text-red-500 text-sm font-light mt-3 ml-4">*Password must contain at least 8 characters, one uppercase letter, one lowercase letter and one number</span>
        """
    else:
        return f"""
        <input type="text" class="w-full h-12 rounded-full bg-bg border-4 border-border text-text text-xs px-14 sm:px-16 py-1 outline-none" placeholder="Enter password here" id="password" name="password"
            hx-post="/auth/validate-password"
            hx-trigger="keyup changed delay:250ms"
            hx-target="#pass-grp"
            hx-swap="innerHTML" value="{password}" required>
        """