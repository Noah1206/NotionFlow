from authlib.integrations.flask_client import OAuth

def register_oauth_service(app, name, client_id, client_secret, authorize_url, access_token_url, api_base_url, scope):
    oauth = OAuth(app)
    return oauth.register(
        name=name,
        client_id=client_id,
        client_secret=client_secret,
        access_token_url=access_token_url,
        authorize_url=authorize_url,
        api_base_url=api_base_url,
        client_kwargs={'scope': scope}
    )
