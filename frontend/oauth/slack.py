from flask import Blueprint, redirect, url_for, session, request
import os
from .base_oauth import register_oauth

# Slack OAuth configuration - using environment variables
urls = {
    'authorize_url': 'https://slack.com/oauth/authorize',
    'access_token_url': 'https://slack.com/api/oauth.access',
    'base_url': 'https://slack.com/api/'
}
scope = 'identity.basic'
client_id = os.getenv('SLACK_CLIENT_ID')
client_secret = os.getenv('SLACK_CLIENT_SECRET')

slack_bp = Blueprint('slack_bp', __name__)
slack_oauth = None

def init_slack_oauth(app):
    if not client_id or not client_secret:
        raise ValueError("Slack OAuth credentials not found in environment variables")
    
    global slack_oauth
    slack_oauth = register_oauth(app, 'slack', urls, scope, client_id, client_secret)

    @slack_bp.route('/login/slack')
    def login_slack():
        return slack_oauth.authorize(callback=url_for('slack_bp.slack_authorized', _external=True))

    @slack_bp.route('/auth/slack/callback')
    def slack_authorized():
        resp = slack_oauth.authorized_response()
        if resp is None or resp.get('access_token') is None:
            return 'Access denied'
        session['slack_token'] = (resp['access_token'], '')
        user_info = slack_oauth.get('users.identity')
        return f"Logged in as: {user_info.data}"

    @slack_oauth.tokengetter
    def get_slack_oauth_token():
        return session.get('slack_token')
