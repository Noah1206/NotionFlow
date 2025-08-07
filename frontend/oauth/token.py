from flask import Blueprint, jsonify, session, current_app
import jwt
import datetime

token_bp = Blueprint('token_bp', __name__)

def create_jwt(user_info):
    payload = {
        "email": user_info["email"],
        "name": user_info["name"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    secret = current_app.config["SECRET_KEY"]
    return jwt.encode(payload, secret, algorithm="HS256")

@token_bp.route("/auth/token")
def issue_token():
    user_info = session.get("user_info")
    if not user_info:
        return jsonify({"error": "No user info in session"}), 401
    token = create_jwt(user_info)
    return jsonify({"token": token}) 