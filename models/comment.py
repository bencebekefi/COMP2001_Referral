from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class Comment(db.Model):
    __tablename__ = 'Comment'
    __table_args__ = {'schema': 'Referral'}

    CommentID = db.Column(db.Integer, primary_key=True)
    TrailID = db.Column(db.Integer, db.ForeignKey('Referral.Trail.TrailID'))
    UserID = db.Column(db.Integer, db.ForeignKey('Referral.User.UserID'))
    CommentText = db.Column(db.String, nullable=False)
    CommentDate = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    IsArchived = db.Column(db.Boolean, default=False)
