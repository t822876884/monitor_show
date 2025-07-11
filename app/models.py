from datetime import datetime
from app import db

class Platform(db.Model):
    __tablename__ = 'platforms'
    
    id = db.Column(db.Integer, primary_key=True)
    platform_id = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    img = db.Column(db.String(255))
    number = db.Column(db.Integer)
    is_favorite = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    livestreams = db.relationship('Livestream', backref='platform', lazy='dynamic')
    
    def __repr__(self):
        return f'<Platform {self.title}>'

class Livestream(db.Model):
    __tablename__ = 'livestreams'
    
    id = db.Column(db.Integer, primary_key=True)
    stream_id = db.Column(db.String(100), unique=True, nullable=False)
    platform_id = db.Column(db.String(50), db.ForeignKey('platforms.platform_id'))
    title = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    img = db.Column(db.String(255))
    is_online = db.Column(db.Boolean, default=True)
    is_favorite = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    last_check = db.Column(db.DateTime, default=datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    downloads = db.relationship('Download', backref='livestream', lazy='dynamic')
    
    def __repr__(self):
        return f'<Livestream {self.title}>'

class Download(db.Model):
    __tablename__ = 'downloads'
    
    id = db.Column(db.Integer, primary_key=True)
    stream_id = db.Column(db.String(100), db.ForeignKey('livestreams.stream_id'))
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    filesize = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    start_time = db.Column(db.DateTime, default=datetime.now)
    end_time = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Download {self.filename}>'

class Setting(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255))
    description = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<Setting {self.key}={self.value}>'