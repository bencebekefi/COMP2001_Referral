from flask import Flask, jsonify, request, abort, session, send_from_directory
from flask_migrate import Migrate
from flask_swagger_ui import get_swaggerui_blueprint
from models import db, Trail, User, Comment
from config import DevelopmentConfig, TestingConfig, ProductionConfig
from sqlalchemy import text
import requests
import logging
import os
import datetime

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "defaultsecret")

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Starting the application...")

    env = os.environ.get('FLASK_ENV', 'development')
    logging.info(f"Loading configuration for {env} environment...")
    app.config.from_object(ProductionConfig)

    db.init_app(app)
    Migrate(app, db)
    logging.info("Database initialized successfully.")

    SWAGGER_URL = '/api/docs'
    API_URL = '/swagger.json'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "Trails API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    @app.route('/swagger.json')
    def swagger_json():
        try:
            return send_from_directory('static', 'swagger.yml')
        except Exception as e:
            logging.error(f"Error serving swagger.yml: {e}")
            abort(500, description="Swagger specification file not found.")

    AUTH_API_URL = "https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users"

    def role_required(required_role):
        def decorator(func):
            def wrapper(*args, **kwargs):
                if 'username' not in session or 'role' not in session:
                    abort(401, description="Unauthorized: Please log in.")
                if session['role'] != required_role:
                    abort(403, description="Forbidden: You do not have permission.")
                return func(*args, **kwargs)
            wrapper.__name__ = func.__name__
            return wrapper
        return decorator

    @app.route('/test-db')
    def test_db():
        try:
            db.session.execute(text('SELECT 1'))
            return jsonify({"message": "Database connection successful!"}), 200
        except Exception as e:
            return jsonify({"error": "Database connection failed", "details": str(e)}), 500

    @app.route('/login', methods=['POST'])
    def login():
        try:
            if not request.is_json:
                logging.warning("Request does not contain valid JSON.")
                return jsonify({"error": "Request must be in JSON format."}), 400

            credentials = request.get_json()
            email = credentials.get('email')
            password = credentials.get('password')
            if not email or not password:
                return jsonify({"error": "Email and password are required."}), 400

            auth_payload = {'email': email, 'password': password}
            response = requests.post(AUTH_API_URL, json=auth_payload)

            if response.status_code == 200:
                api_response = response.json()
                print("DEBUG API RESPONSE:", api_response)

                if isinstance(api_response, list) and "Verified" in api_response and "True" in api_response:
                    # ✅ Ensure user exists in local DB
                    user = User.query.filter_by(EmailAddress=email).first()
                    if not user:
                        logging.info(f"User {email} not found in local DB. Creating new entry.")
                        user = User(EmailAddress=email, Role="User")  # Or assign 'Admin' based on email if needed
                        db.session.add(user)
                        db.session.commit()

                    # ✅ Set session
                    session['username'] = email
                    session['role'] = user.Role
                    session['logged_in_at'] = datetime.datetime.utcnow().isoformat()

                    logging.info(f"User {email} authenticated successfully as {user.Role}.")
                    return jsonify({
                        "message": "Login successful",
                        "username": email,
                        "role": user.Role
                    }), 200
                else:
                    logging.error("Invalid API response format")
                    return jsonify({"error": "Invalid response from authentication service."}), 500

            elif response.status_code == 401:
                logging.warning(f"Authentication failed for email: {email}")
                return jsonify({"error": "Invalid email or password."}), 401

            else:
                logging.error(f"External API error: {response.status_code} - {response.text}")
                return jsonify({"error": "External API error", "details": response.text}), 500

        except requests.exceptions.RequestException as e:
            logging.error(f"Error connecting to external API: {e}")
            return jsonify({"error": "Unable to connect to the authentication service."}), 500

        except Exception as e:
            logging.error(f"Unexpected error during login: {e}")
            return jsonify({"error": "Internal Server Error."}), 500

    @app.route('/logout', methods=['POST'])
    def logout():
        session.clear()
        return jsonify({"message": "Logged out successfully."}), 200

    @app.route('/trails', methods=['GET'])
    def get_all_trails():
        try:
            trails = Trail.query.all()
            return jsonify({"trails": [{
                "TrailID": t.TrailID,
                "TrailName": t.TrailName,
                "TrailRating": float(t.TrailRating) if t.TrailRating else None,
                "TrailDifficulty": t.TrailDifficulty,
                "TrailDistance": float(t.TrailDistance),
                "TrailEstTime": t.TrailEstTime,
                "TrailRouteType": t.TrailRouteType,
                "TrailDescription": t.TrailDescription,
                "LocationID": t.LocationID
            } for t in trails]}), 200
        except Exception as e:
            return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

    @app.route('/trails/<int:trail_id>', methods=['GET'])
    def get_trail(trail_id):
        trail = Trail.query.get(trail_id)
        if not trail:
            return jsonify({"error": "Trail not found"}), 404
        return jsonify({
            "TrailID": trail.TrailID,
            "TrailName": trail.TrailName,
            "TrailRating": float(trail.TrailRating) if trail.TrailRating else None,
            "TrailDifficulty": trail.TrailDifficulty,
            "TrailDistance": float(trail.TrailDistance),
            "TrailEstTime": trail.TrailEstTime,
            "TrailRouteType": trail.TrailRouteType,
            "TrailDescription": trail.TrailDescription,
            "LocationID": trail.LocationID
        }), 200

    @app.route('/trails', methods=['POST'])
    @role_required('Admin')
    def create_trail():
        try:
            data = request.get_json()
            required_fields = ["TrailName", "TrailDifficulty", "TrailDistance", "TrailEstTime", "TrailRouteType", "TrailDescription", "LocationID"]
            for field in required_fields:
                if field not in data:
                    abort(400, description=f"Missing field: {field}")
            new_trail = Trail(
                TrailName=data["TrailName"],
                TrailDifficulty=data["TrailDifficulty"],
                TrailDistance=data["TrailDistance"],
                TrailEstTime=data["TrailEstTime"],
                TrailRouteType=data["TrailRouteType"],
                TrailDescription=data["TrailDescription"],
                LocationID=data["LocationID"],
                TrailRating=data.get("TrailRating", None)
            )
            db.session.add(new_trail)
            db.session.commit()
            return jsonify({"message": "Trail created successfully", "TrailID": new_trail.TrailID}), 201
        except Exception as e:
            return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

    @app.route('/trails/<int:trail_id>', methods=['PUT'])
    @role_required('Admin')
    def update_trail(trail_id):
        try:
            trail = Trail.query.get(trail_id)
            if not trail:
                return jsonify({"error": "Trail not found"}), 404
            data = request.get_json()
            for field in ["TrailName", "TrailRating", "TrailDifficulty", "TrailDistance", "TrailEstTime", "TrailRouteType", "TrailDescription", "LocationID"]:
                if field in data:
                    setattr(trail, field, data[field])
            db.session.commit()
            return jsonify({"message": "Trail updated successfully"}), 200
        except Exception as e:
            return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

    @app.route('/trails/<int:trail_id>', methods=['DELETE'])
    @role_required('Admin')
    def delete_trail(trail_id):
        try:
            trail = Trail.query.get(trail_id)
            if not trail:
                return jsonify({"error": "Trail not found"}), 404
            db.session.delete(trail)
            db.session.commit()
            return jsonify({"message": "Trail deleted"}), 200
        except Exception as e:
            return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

    @app.route('/comments', methods=['GET'])
    def get_all_comments():
        try:
            comments = Comment.query.filter_by(IsArchived=False).all()
            result = [{
                "CommentID": c.CommentID,
                "TrailID": c.TrailID,
                "UserID": c.UserID,
                "CommentText": c.CommentText,
                "CommentDate": c.CommentDate.isoformat()
            } for c in comments]
            return jsonify({"comments": result}), 200
        except Exception as e:
            return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

    @app.route('/trails/<int:trail_id>/comments', methods=['GET'])
    def get_comments_for_trail(trail_id):
        try:
            comments = Comment.query.filter_by(TrailID=trail_id, IsArchived=False).all()
            result = [{
                "CommentID": c.CommentID,
                "TrailID": c.TrailID,
                "UserID": c.UserID,
                "CommentText": c.CommentText,
                "CommentDate": c.CommentDate.isoformat()
            } for c in comments]
            return jsonify({"comments": result}), 200
        except Exception as e:
            return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

    @app.route("/trails/<int:trail_id>/comments", methods=["POST"])
    def add_comment(trail_id):
        if "username" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        try:
            data = request.get_json()
            comment_text = data.get("CommentText")
            if not comment_text:
                return jsonify({"error": "CommentText is required."}), 400
            user = User.query.filter_by(EmailAddress=session["username"]).first()
            comment = Comment(
                TrailID=trail_id,
                UserID=user.UserID,
                CommentText=comment_text,
                CommentDate=datetime.datetime.utcnow(),
                IsArchived=False
            )
            logging.info(f"debug; {comment.UserID}")
            db.session.add(comment)
            db.session.commit()
            return jsonify({"message": "Comment added"}), 201
        except Exception as e:
            return jsonify({"error": "Server error", "details": str(e)}), 500

    @app.route('/comments/<int:comment_id>', methods=['PUT'])
    def edit_comment(comment_id):
        comment = Comment.query.get(comment_id)
        if not comment:
            return jsonify({"error": "Comment not found"}), 404
        user = User.query.filter_by(EmailAddress=session.get('username')).first()
        if not user or (user.UserID != comment.UserID and session.get('role') != 'Admin'):
            return jsonify({"error": "Forbidden"}), 403
        data = request.get_json()
        content = data.get("CommentText")
        if not content:
            return jsonify({"error": "Missing CommentText"}), 400
        comment.CommentText = content
        db.session.commit()
        return jsonify({"message": "Comment updated"}), 200

    @app.route('/comments/<int:comment_id>', methods=['DELETE'])
    def archive_comment(comment_id):
        comment = Comment.query.get(comment_id)
        if not comment:
            return jsonify({"error": "Comment not found"}), 404
        if session.get('role') != 'Admin':
            return jsonify({"error": "Forbidden: Admins only"}), 403
        comment.IsArchived = True
        db.session.commit()
        return jsonify({"message": "Comment archived"}), 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
