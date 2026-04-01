import uuid
import json
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from db import db


def _car_display_name(key):
    from data.cars import car_display_name
    return car_display_name(key)


def _track_display_name(key):
    from data.tracks import track_display_name
    return track_display_name(key)


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id           = db.Column(db.Integer, primary_key=True)
    email        = db.Column(db.String(255), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    setups = db.relationship('Setup', backref='user', lazy='dynamic',
                             cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Setup(db.Model):
    __tablename__ = 'setups'

    id            = db.Column(db.String(36), primary_key=True,
                              default=lambda: str(uuid.uuid4()))
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'),
                              nullable=False, index=True)
    filename      = db.Column(db.String(255), nullable=False)
    car_name      = db.Column(db.String(100), nullable=False)
    car_key       = db.Column(db.String(100), nullable=False, index=True)
    car_class     = db.Column(db.String(50),  nullable=False, default='Other')
    track_name    = db.Column(db.String(100), nullable=False)
    track_key     = db.Column(db.String(100), nullable=False, index=True)
    setup_type    = db.Column(db.String(50),  nullable=False, default='race')
    notes_text    = db.Column(db.Text)
    decoded_params = db.Column(db.Text, nullable=False, default='[]')  # JSON
    storage_path  = db.Column(db.String(500))
    rating        = db.Column(db.Integer)                              # 1–5 stars
    tags          = db.Column(db.String(500))                          # comma-separated
    uploaded_at   = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at  = db.Column(db.DateTime)

    params = db.relationship('SetupParam', backref='setup', lazy='dynamic',
                             cascade='all, delete-orphan')

    @property
    def car_display(self):
        return self.car_name or _car_display_name(self.car_key)

    @property
    def track_display(self):
        return self.track_name or _track_display_name(self.track_key)

    def get_decoded_params(self):
        try:
            return json.loads(self.decoded_params)
        except Exception:
            return []


class SetupHistory(db.Model):
    """Snapshot of decoded_params saved before a setup is overwritten on re-upload."""
    __tablename__ = 'setup_history'

    id            = db.Column(db.Integer, primary_key=True)
    setup_id      = db.Column(db.String(36), db.ForeignKey('setups.id'),
                              nullable=False, index=True)
    user_id       = db.Column(db.Integer, nullable=False, index=True)
    decoded_params = db.Column(db.Text, nullable=False, default='[]')
    saved_at      = db.Column(db.DateTime, default=datetime.utcnow)


class SetupParam(db.Model):
    __tablename__ = 'setup_params'

    id       = db.Column(db.Integer, primary_key=True)
    setup_id = db.Column(db.String(36), db.ForeignKey('setups.id'),
                         nullable=False, index=True)
    user_id  = db.Column(db.Integer, nullable=False, index=True)
    tab      = db.Column(db.String(100))
    section  = db.Column(db.String(100))
    label    = db.Column(db.String(200), nullable=False)
    value    = db.Column(db.String(200))
