import enum

from app import db, login
from datetime import date, datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    trackers = db.relationship('Tracker', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Anime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), index=True, unique=True)
    image_url = db.Column(db.String(200), default='')
    total_episodes = db.Column(db.Integer)
    trackers = db.relationship('Tracker', backref='anime', lazy='dynamic')

    def __repr__(self):
        return f'<Anime {self.title}>'


class Tracker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    watched_episodes = db.Column(db.Integer, default=0)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='Watching')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    anime_id = db.Column(db.Integer, db.ForeignKey('anime.id'))

    def __repr__(self):
        user = User.query.get(self.user_id)
        anime = Anime.query.get(self.anime_id)
        if user is None or anime is None:
            return 'None'
        return f'<Tracker (User={user}, Anime={anime})>'


@login.user_loader
def load_user(id):
    return User.query.get(int(id))