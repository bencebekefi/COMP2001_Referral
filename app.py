from flask import Flask, jsonify, request, abort, session, send_from_directory
from flask_migrate import Migrate
from flask_swagger_ui import get_swaggerui_blueprint
from sqlalchemy import text
import requests
import logging
import os
import datetime

from config import DevelopmentConfig, TestingConfig, ProductionConfig  # :contentReference[oaicite:2]{index=2}
from models import db, Trail, User, Comment

def create_app():
    # -- Flask + Config --------------------------------------------------
    app = Flask(__name__)

    # Select config based on FLASK_ENV
    env = os.environ.get('FLASK_ENV', 'development').lower()
    if env == 'production':
        app.config.from_object(ProductionConfig)
    elif env == 'testing':
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # Secret key (falls back to Config.SECRET_KEY)
    app.secret_key = app.config.get('SECRET_KEY', 'change-me')

    # -- Logging ----------------------------------------------------------
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info(f"Starting app in {env!r} environment...")

    # -- Database & Migrations --------------------------------------------
    db.init_app(app)                          # single SQLAlchemy init!
    Migrate(app, db)                          # Flask-Migrate
    logging.info("Database initialized successfully.")

    # -- Swagger UI -------------------------------------------------------
    swaggerui_blueprint = get_swaggerui_blueprint(
        app.config['SWAGGER_URL'],
        app.config['API_URL'],
        config={'app_name': "Trails API"}
    )
    app.register_blueprint(swaggerui_blueprint,
                           url_prefix=app.config['SWAGGER_URL'])
    logging.info("Swagger UI registered successfully.")

    @app.route('/swagger.json')
    def swagger_json():
        try:
            return send_from_directory('static', 'swagger.yml')
        except Exception as e:
            logging.error(f"Error serving swagger.yml: {e}")
            abort(500, description="Swagger spec not found")

    # -- Authentication Middleware ---------------------------------------
    AUTH_API_URL = "https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users"
    def role_required(role):
        def decorator(f):
            def wrapped(*args, **kwargs):
                if 'username' not in session or 'role' not in session:
                    abort(401, description="Unauthorized")
                if session['role'] != role:
                    abort(403, description="Forbidden")
                return f(*args, **kwargs)
            wrapped.__name__ = f.__name__
            return wrapped
        return decorator

    # -- Healthcheck ------------------------------------------------------
    @app.route('/test-db')
    def test_db():
        try:
            db.session.execute(text('SELECT 1'))
            return jsonify(message="Database OK"), 200
        except Exception as e:
            logging.error(f"DB failed: {e}")
            return jsonify(error="DB connection failed"), 500

    # -- Login / Logout --------------------------------------------------
    @app.route('/login', methods=['POST'])
    def login():
        if not request.is_json:
            return jsonify(error="Must send JSON"), 400
        creds = request.get_json()
        email = creds.get('email')
        pwd   = creds.get('password')
        if not email or not pwd:
            return jsonify(error="Email+password required"), 400

        try:
            r = requests.post(AUTH_API_URL, json=dict(email=email, password=pwd))
            if r.status_code == 200:
                api_resp = r.json()
                # expecting ["Verified", "True"] somewhere in list
                if isinstance(api_resp, list) and "Verified" in api_resp:
                    user = User.query.filter_by(EmailAddress=email).first()
                    if not user:
                        return jsonify(error="User not in local DB"), 404

                    session['username']    = email
                    session['role']        = user.Role
                    session['logged_in_at']= datetime.datetime.utcnow().isoformat()
                    return jsonify(message="Login OK", role=user.Role), 200

                else:
                    return jsonify(error="Auth service rejected you"), 401

            return jsonify(error="Auth service error", details=r.text), r.status_code

        except requests.RequestException as e:
            logging.error(f"Auth API unreachable: {e}")
            return jsonify(error="Auth service unreachable"), 503

    @app.route('/logout', methods=['POST'])
    def logout():
        session.clear()
        return jsonify(message="Logged out"), 200

    # -- Trails CRUD ------------------------------------------------------
    @app.route('/trails', methods=['GET'])
    def get_all_trails():
        trails = Trail.query.all()
        data = [{
            "TrailID":       t.TrailID,
            "TrailName":     t.TrailName,
            "TrailRating":   float(t.TrailRating) if t.TrailRating is not None else None,
            "TrailDifficulty": t.TrailDifficulty,
            "TrailDistance": float(t.TrailDistance),
            "TrailEstTime":  t.TrailEstTime,
            "TrailRouteType": t.TrailRouteType,
            "TrailDescription": t.TrailDescription,
            "LocationID":    t.LocationID
        } for t in trails]
        return jsonify(trails=data), 200

    @app.route('/trails/<int:trail_id>', methods=['GET'])
    def get_trail(trail_id):
        t = Trail.query.get_or_404(trail_id,
                description=f"Trail {trail_id} not found")
        return jsonify({
            "TrailID":       t.TrailID,
            "TrailName":     t.TrailName,
            "TrailRating":   float(t.TrailRating) if t.TrailRating is not None else None,
            "TrailDifficulty": t.TrailDifficulty,
            "TrailDistance": float(t.TrailDistance),
            "TrailEstTime":  t.TrailEstTime,
            "TrailRouteType": t.TrailRouteType,
            "TrailDescription": t.TrailDescription,
            "LocationID":    t.LocationID
        }), 200

    @app.route('/trails', methods=['POST'])
    @role_required('Admin')
    def create_trail():
        data = request.get_json() or {}
        missing = [f for f in (
            "TrailName","TrailDifficulty","TrailDistance",
            "TrailEstTime","TrailRouteType","TrailDescription",
            "LocationID"
        ) if f not in data]
        if missing:
            return jsonify(error="Missing fields", fields=missing), 400

        t = Trail(**{k: data[k] for k in data if hasattr(Trail, k)})
        db.session.add(t)
        db.session.commit()
        return jsonify(message="Created", TrailID=t.TrailID), 201

    @app.route('/trails/<int:trail_id>', methods=['PUT'])
    @role_required('Admin')
    def update_trail(trail_id):
        t = Trail.query.get_or_404(trail_id,
                description=f"Trail {trail_id} not found")
        data = request.get_json() or {}
        for k, v in data.items():
            if hasattr(t, k):
                setattr(t, k, v)
        db.session.commit()
        return jsonify(message="Updated"), 200

    @app.route('/trails/<int:trail_id>', methods=['DELETE'])
    @role_required('Admin')
    def delete_trail(trail_id):
        t = Trail.query.get_or_404(trail_id,
                description=f"Trail {trail_id} not found")
        db.session.delete(t)
        db.session.commit()
        return jsonify(message="Deleted"), 200

    # -- Comments ---------------------------------------------------------
    @app.route('/comments', methods=['GET'])
    def get_all_comments():
        ms = Comment.query.filter_by(IsArchived=False).all()
        data = [{
            "CommentID":   c.CommentID,
            "TrailID":     c.TrailID,
            "UserID":      c.UserID,
            "CommentText": c.CommentText,
            "CommentDate": c.CommentDate.isoformat()
        } for c in ms]
        return jsonify(comments=data), 200

    @app.route('/trails/<int:trail_id>/comments', methods=['GET'])
    def get_comments_for_trail(trail_id):
        ms = Comment.query.filter_by(
                 TrailID=trail_id,
                 IsArchived=False).all()
        data = [{
            "CommentID":   c.CommentID,
            "TrailID":     c.TrailID,
            "UserID":      c.UserID,
            "CommentText": c.CommentText,
            "CommentDate": c.CommentDate.isoformat()
        } for c in ms]
        return jsonify(comments=data), 200

    @app.route('/trails/<int:trail_id>/comments', methods=['POST'])
    def add_comment(trail_id):
        if 'username' not in session:
            return jsonify(error="Unauthorized"), 401
        user = User.query.filter_by(
                   EmailAddress=session['username']).first_or_404(
                   description="User not found")
        data = request.get_json() or {}
        text = data.get('CommentText')
        if not text:
            return jsonify(error="CommentText required"), 400

        c = Comment(
            TrailID=trail_id,
            UserID=user.UserID,
            CommentText=text,
            CommentDate=datetime.datetime.utcnow(),
            IsArchived=False
        )
        db.session.add(c)
        db.session.commit()
        return jsonify(message="Comment added"), 201

    @app.route('/comments/<int:comment_id>', methods=['PUT'])
    def edit_comment(comment_id):
        c = Comment.query.get_or_404(comment_id,
                description="Comment not found")
        user = User.query.filter_by(
                   EmailAddress=session.get('username')).first()
        if not user or (user.UserID != c.UserID and session.get('role')!='Admin'):
            return jsonify(error="Forbidden"), 403

        data = request.get_json() or {}
        txt  = data.get('CommentText')
        if not txt:
            return jsonify(error="Missing CommentText"), 400

        c.CommentText = txt
        db.session.commit()
        return jsonify(message="Comment updated"), 200

    @app.route('/comments/<int:comment_id>', methods=['DELETE'])
    def archive_comment(comment_id):
        c = Comment.query.get_or_404(comment_id,
                description="Comment not found")
        if session.get('role') != 'Admin':
            return jsonify(error="Forbidden"), 403
        c.IsArchived = True
        db.session.commit()
        return jsonify(message="Archived"), 200

    return app

if __name__ == '__main__':
    create_app().run(debug=True, port=5000)
