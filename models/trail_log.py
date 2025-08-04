from . import db

class TrailLog(db.Model):
    __tablename__ = 'TrailLog'
    __table_args__ = {'schema': 'Referral'}

    LogID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    TrailID = db.Column(db.Integer, db.ForeignKey('Referral.Trail.TrailID'), nullable=True)
    AddedBy = db.Column(db.String(100), nullable=True)
    AddedOn = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    trail = db.relationship('Trail', backref='logs')
