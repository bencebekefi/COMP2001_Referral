from flask_sqlalchemy import SQLAlchemy

# Create the SQLAlchemy instance
db = SQLAlchemy()


from .trail import Trail
from .location import Location
from .user import User
from .comment import Comment


__all__ = ['db', 'Trail', 'Location', 'User']
