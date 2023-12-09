from website import db
from datetime import timedelta, datetime
from sqlalchemy.sql import func

class RefreshToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(80))
    expiration = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now() + timedelta(days=3))
    user_id = db.Column(db.String(80), db.ForeignKey('user.id'))