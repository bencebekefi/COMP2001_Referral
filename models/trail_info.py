from . import db

class TrailInfo(db.Model):
    __tablename__ = 'TrailInfo'
    __table_args__ = {'schema': 'Referral'}

    TrailID = db.Column(db.Integer, db.ForeignKey('Referral.Trail.TrailID'), primary_key=True)
    InfoID = db.Column(db.Integer, db.ForeignKey('Referral.Info.InfoID'), primary_key=True)
    AdditionalInfo = db.Column(db.String(255), nullable=True)

    # Relationships
    trail = db.relationship('Trail', backref='trail_info_associations')
    info = db.relationship('Info', backref='trail_info_associations')
