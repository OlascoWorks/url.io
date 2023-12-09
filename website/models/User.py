from website import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.String(80), primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    token = db.relationship('RefreshToken', uselist=False, backref='user')
    urls = db.relationship('Url')

    def __repr__(self) -> str:
        return f'User --name "{self.name}"'
    

class Url(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    custom_name = db.Column(db.String(60), default='')
    original_url = db.Column(db.String(200), nullable=False)
    new_url = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Integer, default=1)
    clicks = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.String(80), db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        return f'Url --id "{self.id}"'