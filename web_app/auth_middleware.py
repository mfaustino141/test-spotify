from django.shortcuts import redirect
from datetime import timedelta
from django.conf import settings
from requests import post, exceptions
from django.urls import reverse
import logging
from datetime import datetime, timedelta, timezone
from django.utils import timezone as dj_timezone


logger = logging.getLogger(__name__)

SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'

class SpotifyAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.debug("Auth Middleware")

        # Skip authentication for certain paths
        exempt_paths = [
            reverse('spotify_login'),
            reverse('spotify_back'),
            reverse('login'),
            reverse('register'),
            reverse('welcome'),
            # reverse('profile'),  # Add profile to exempt paths
            # reverse('top_artists'),
            # reverse('guess_song'),
            # reverse('top_songs'),
            # reverse('time'),
            # reverse('aura'),
            # reverse('friends')
        ]
        normalized_request_path = request.path.rstrip('/')
        normalized_exempt_paths = [path.rstrip('/') for path in exempt_paths]

        if normalized_request_path in normalized_exempt_paths:
            return self.get_response(request)
        
        print("NOT EXEMPT", request.path)
        # Check if the user is logged in
        if not request.user.is_authenticated:
            logger.debug("User not logged in or registered")
            request.session['next'] = request.path
            return redirect(reverse('login'))

        printSession(request)
        # Check if the user has a valid Spotify access token
        access_token = request.session.get('access_token')
        refresh_token = request.session.get('refresh_token')
        expires_in = request.session.get('expires_in')
        time_obtained_timestamp = request.session.get('time_obtained')

        if time_obtained_timestamp:
            # Convert timestamp to datetime object
            time_obtained = datetime.fromtimestamp(time_obtained_timestamp, tz=timezone.utc)
        else:
            # Handle the case where time_obtained is not in the session
            time_obtained = None

        if access_token and time_obtained and expires_in:
            # Check if the token is still valid
            current_time = dj_timezone.now()
            token_expiration_time = time_obtained + timedelta(seconds=expires_in - 60)  # 60-second buffer

            if current_time >= token_expiration_time:
                logger.debug("Access token expired, attempting to refresh")
                if refresh_token:
                    new_tokens = refresh_spotify_token(refresh_token)
                    if new_tokens:
                        logger.debug("New tokens obtained after refreshing")
                        request.session['access_token'] = new_tokens['access_token']
                        request.session['expires_in'] = new_tokens['expires_in']
                        request.session['time_obtained'] = dj_timezone.now().timestamp()
                    else:
                        logger.error("Failed to refresh access token")
                        return redirect(reverse('spotify_login'))
        else:
            logger.debug("No access token, redirecting to Spotify login")
            request.session['next'] = request.path
            return redirect(reverse('spotify_login'))

        # Proceed with the request
        return self.get_response(request)

def refresh_spotify_token(refresh_token):
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': settings.SPOTIFY_CLIENT_ID,
        'client_secret': settings.SPOTIFY_CLIENT_SECRET,
    }
    try:
        response = post(SPOTIFY_TOKEN_URL, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to refresh token: {response.status_code} - {response.text}")
    except exceptions.RequestException as e:
        logger.exception("Exception occurred while refreshing token")
    return None


def printSession(request):
    print("Session:")
    for key, value in request.session.items():
        print(f"{key}: {value}")