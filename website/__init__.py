from flask import Flask, render_template, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') if os.environ.get('DATABASE_URL') else 'sqlite:///database.db'
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config.from_pyfile('config.py')

    db.init_app(app)

    migrate = Migrate(app, db)


    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html', current_user=current_user, base=BASE_URL)

    from .api import views, url, auth, BASE_URL
    from .api.user import signup, login, logout
    from .api.Url import get_all_urls, get_all_xxcrf_urls, create_all_xxcrf_urls
    from .models import User, Url

    from datetime import datetime
    @views.route('/')
    def home():
        if current_user.is_authenticated:
            try:
                if session['xxcrf_urls']:  create_all_xxcrf_urls(current_user.id)
            except:  pass
            return render_template('base.html', user=current_user, urls=get_all_urls(current_user.id), base=BASE_URL)
        else:
            try:
                if not session['xxcrf_urls']:  session['xxcrf_urls'] = []
            except:  pass
            limit = 5-(len(session['xxcrf_urls']) if 'xxcrf_urls' in session else 0)
            return render_template('base.html', user=current_user, limit=limit, urls=get_all_xxcrf_urls(), base=BASE_URL)
        
    @views.route('/<url>')
    def visit(url):
        link = Url.query.filter_by(new_url=url).first()
        if link and link.status != 0:
            link.clicks += 1
            db.session.commit()
            return redirect(link.original_url)
        else:  return render_template('404.html', base=BASE_URL)
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(url, url_prefix='/url')
    app.register_blueprint(auth, url_prefix='/auth')

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(id)

    return app