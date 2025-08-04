from . import db

class TrailActivity(db.Model):
    __tablename__  = 'TrailActivity'
    __table_args__ = {'schema': 'Referral'}

    TrailID    = db.Column(
        db.Integer,
        db.ForeignKey('Referral.Trail.TrailID'),
        primary_key=True
    )
    ActivityID = db.Column(
        db.Integer,
        db.ForeignKey('Referral.Activity.ActivityID'),
        primary_key=True
    )

    # Relationships
    trail    = db.relationship(
        'Trail',
        backref=db.backref('activities', lazy=True)
    )
    activity = db.relationship(
        'Activity',
        backref=db.backref('trail_activities', lazy=True)
    )
