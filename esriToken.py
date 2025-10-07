import requests

def init_token(username, password, host):
    # Token generation URL and parameters
    token_url = "https://utsa.maps.arcgis.com/sharing/rest/generateToken"
    token_params = {
        'username': username,
        'password': password,
        'referer': host,
        'expiration': 60,
        'f': 'json'
    }
    try:
        # Make POST request to generate token
        response = requests.post(token_url, data=token_params)
        response.raise_for_status()  # Raise exception for bad status codes

        # Extract token from response
        token = response.json()['token']
        return token, username
    except Exception as e:
        print(f"Error generating token: {e}")
        return None