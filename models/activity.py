# models/activity.py
from . import db

class Activity(db.Model):
    __tablename__ = 'Activity'
    __table_args__ = {'schema': 'Referral'}

    ActivityID   = db.Column(db.Integer, primary_key=True)
    ActivityName = db.Column(db.String(20), nullable=False)

    # One-to-many against TrailActivity
    trail_activities = db.relationship(
        'TrailActivity',
        backref='activity',
        cascade="all, delete-orphan",
        lazy=True
    )
