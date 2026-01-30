from datetime import datetime
from app import db


class User(db.Model):
    """User model for authentication and ownership."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for OAuth users
    is_active = db.Column(db.Boolean, default=True)
    # OAuth fields
    oauth_provider = db.Column(db.String(50))  # 'microsoft', 'google', etc.
    oauth_id = db.Column(db.String(255), index=True)  # Provider's user ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    songs = db.relationship('Song', backref='creator', lazy='dynamic', cascade='all, delete-orphan')
    styles = db.relationship('Style', backref='creator', lazy='dynamic')

    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Style(db.Model):
    """Style model for music style definitions."""

    __tablename__ = 'styles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    style_prompt = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    songs = db.relationship('Song', backref='style', lazy='dynamic')

    def to_dict(self, include_details=True):
        """Convert style to dictionary."""
        data = {
            'id': self.id,
            'name': self.name,
            'style_prompt': self.style_prompt,
            'created_by': self.creator.username if self.creator else None,
            'created_by_id': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        return data


class Song(db.Model):
    """Song model for music creation tracking."""

    __tablename__ = 'songs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.Enum('create', 'submitted', 'completed', 'failed', 'unspecified', name='song_status'), default='create', index=True)
    specific_title = db.Column(db.String(500))
    version = db.Column(db.String(10), default='v1')
    star_rating = db.Column(db.Integer, default=0, index=True)
    specific_lyrics = db.Column(db.Text)
    prompt_to_generate = db.Column(db.Text)
    style_id = db.Column(db.Integer, db.ForeignKey('styles.id', ondelete='SET NULL'))
    vocal_gender = db.Column(db.Enum('male', 'female', 'other', name='vocal_gender'))
    voice_name = db.Column(db.String(255))  # Azure Speech voice name
    download_url_1 = db.Column(db.String(1000))
    downloaded_url_1 = db.Column(db.Boolean, default=False)
    download_url_2 = db.Column(db.String(1000))
    downloaded_url_2 = db.Column(db.Boolean, default=False)
    speech_task_id = db.Column(db.String(255), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_user=False, include_style=True):
        """Convert song to dictionary."""
        data = {
            'id': self.id,
            'status': self.status,
            'specific_title': self.specific_title,
            'version': self.version or 'v1',
            'star_rating': self.star_rating or 0,
            'specific_lyrics': self.specific_lyrics,
            'prompt_to_generate': self.prompt_to_generate,
            'vocal_gender': self.vocal_gender,
            'voice_name': self.voice_name,
            'download_url_1': self.download_url_1,
            'downloaded_url_1': self.downloaded_url_1 or False,
            'download_url_2': self.download_url_2,
            'downloaded_url_2': self.downloaded_url_2 or False,
            'speech_task_id': self.speech_task_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_user:
            data['creator'] = self.creator.username if self.creator else None
            data['user_id'] = self.user_id

        if include_style and self.style:
            data['style'] = self.style.to_dict(include_details=False)
            data['style_name'] = self.style.name
        else:
            data['style_id'] = self.style_id

        return data
