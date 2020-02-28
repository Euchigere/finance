from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class Users(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), index=True, unique=True, nullable=False)
    phash = db.Column(db.String(128))
    cash = db.Column(db.Float, default=10000.00)
    record = db.relationship('Records', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.phash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.phash, password)

    def __repr__(self):
        return f"<User {self.username}>"

class Records(db.Model):
    __tablename__ = 'records'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(25), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    transact_type = db.Column(db.String(10), nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"<Id {self.id}>"