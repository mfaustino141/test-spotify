from os import access

import openai
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
import base64
import json
from requests import post, get
from django.utils import timezone
import urllib.parse
from django.urls import reverse
import re
from .models import WrappedData, SpotifyWrapped
from datetime import datetime

SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE_URL = 'https://api.spotify.com/v1'


# Register View
def register(request):
    if request.user.is_authenticated:
        # If user is already logged in, redirect to homepage
        return redirect('/')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('/register')

        # Create and save the new user
        user = User.objects.create_user(username=username, password=password)
        login(request, user)  # Log the user in after registration
        messages.success(request, 'Registration successful!')
        return redirect('/')  # Redirect to a 'home' page or any page you prefer

    return render(request, 'test_register.html')


# Login View
def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        # Get username and password from the form
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Log the user in
            login(request, user)
            # Redirect to the home page or any other page
            return redirect('/')  # Replace 'home' with your desired URL name
        else:
            # Invalid credentials, add an error message
            messages.error(request, 'Invalid username or password.')
            return redirect('/login')  # Redirect back to the login page

    return render(request, 'login.html')


# Logout View
def logout_view(request):
    if not request.user.is_authenticated:
        # If user is not logged in, redirect to login (can't logout if not logged in)
        return redirect('/login')

    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('/login')

@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        user.delete()
        request.session.flush()
        messages.success(request, "Your account has been deleted successfully.")
        return redirect('/login') 
    return redirect('/login')

# Takes user to Spotify's auth url
def spotify_authentication(request):
    if not request.user.is_authenticated:
        return redirect('login')

    scope = 'user-read-private user-read-email user-top-read user-read-recently-played user-library-read streaming user-read-playback-state user-modify-playback-state'
    redirect_uri = request.build_absolute_uri(reverse('spotify_back'))
    params = {
        'client_id': settings.SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': scope,
    }
    auth_url = f'{SPOTIFY_AUTH_URL}?{urllib.parse.urlencode(params)}'

    return redirect(auth_url)


# Handle Spotify authentication callback
def spotify_back(request):
    if not request.user.is_authenticated:
        return redirect('login')

    error = request.GET.get('error')
    if error:
        return HttpResponse(f"Error occurred during Spotify authentication: {error}")

    code = request.GET.get('code')
    redirect_uri = request.build_absolute_uri('/back/')
    auth_token = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    auth_base64str = str(base64.b64encode(auth_token.encode('utf-8')), 'utf-8')

    headers = {'Authorization': f'Basic {auth_base64str}', 'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'grant_type': 'authorization_code', 'code': code, 'redirect_uri': redirect_uri}
    response = post(SPOTIFY_TOKEN_URL, data=data, headers=headers)
    tokens = json.loads(response.text)

    # Store tokens in the user's session
    request.session['access_token'] = tokens['access_token']
    request.session['refresh_token'] = tokens['refresh_token']
    request.session['time_obtained'] = timezone.now().timestamp()  # Store time the token was obtained
    request.session['expires_in'] = tokens['expires_in']

    # Redirect to the original page the user was trying to access
    next_url = request.session.pop('next', '/')  # Default to home page if 'next' is not set
    return redirect(next_url)


def get_user_profile(request):
    print("Getting profile")
    try:
        access_token = request.session.get('access_token')
        headers = {'Authorization': f'Bearer {access_token}'} # bearer is authorized to make api requests
        response = get(f'{SPOTIFY_API_BASE_URL}/me', headers=headers) # gets user's profile information

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")

        return JsonResponse(response.json())
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_top_tracks(request):
    try:
        access_token = request.session.get('access_token')
        time_range = request.GET.get('time_range', 'medium_term')
        lim = request.GET.get('limit', '5')
        headers = {'Authorization': f'Bearer {access_token}'}
        response = get(
            f'{SPOTIFY_API_BASE_URL}/me/top/tracks',
            headers=headers,
            params={'time_range': time_range, 'limit': lim}
        )
        return JsonResponse(response.json())
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_top_artists(request):
    try:
        access_token = request.session.get('access_token')
        time_range = request.GET.get('time_range', 'medium_term')
        lim = request.GET.get('limit', '50')
        headers = {'Authorization': f'Bearer {access_token}'}
        response = get(
            f'{SPOTIFY_API_BASE_URL}/me/top/artists',
            headers=headers,
            params={'time_range': time_range, 'limit': lim}
        )
        return JsonResponse(response.json())
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_recently_played(request):
    try:
        access_token = request.session.get('access_token')
        lim = request.GET.get('limit', '20')
        headers = {'Authorization': f'Bearer {access_token}'}
        response = get(
            f'{SPOTIFY_API_BASE_URL}/me/player/recently-played',
            headers=headers,
            params={'limit': lim}
        )
        return JsonResponse(response.json())
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_saved_tracks(request):
    try:
        access_token = request.session.get('access_token')
        lim = request.GET.get('limit', '20')
        offset = request.GET.get('offset', '0')
        headers = {'Authorization': f'Bearer {access_token}'}
        response = get(
            f'{SPOTIFY_API_BASE_URL}/me/tracks',
            headers=headers,
            params={'limit': lim, 'offset': offset}
        )
        return JsonResponse(response.json())
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_track_features(request, track_id):
    try:
        access_token = request.session.get('access_token')
        headers = {'Authorization': f'Bearer {access_token}'}
        response = get(
            f'{SPOTIFY_API_BASE_URL}/audio-features/{track_id}',
            headers=headers
        )
        return JsonResponse(response.json())
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def validate_spotify_id(request, id, type):
    # Ensure type is valid
    if type not in ['artist', 'album', 'playlist', 'track']:
        return JsonResponse({'error': 'Invalid type specified'}, status=400)

    # Get access token from session
    access_token = request.session.get('access_token')

    if not access_token:
        return JsonResponse({'error': 'Access token not found'}, status=400)

    # Set up the endpoint based on the type
    endpoint = f"{SPOTIFY_API_BASE_URL}/{type}s/{id}"

    # Set up headers with Authorization
    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        # Make the GET request to Spotify API
        response = get(endpoint, headers=headers)

        # Check if the response is valid
        if response.status_code == 200:
            return JsonResponse({'valid': True})
        elif response.status_code == 404:
            return JsonResponse({'valid': False})
        else:
            return JsonResponse({'error': 'Spotify API request failed'}, status=response.status_code)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_tracks(request, content_type, query):
    access_token = request.session.get('access_token')

    limit = 50
    headers = {'Authorization': f'Bearer {access_token}'}

    if content_type == 'artist':
        endpoint = f"https://api.spotify.com/v1/search?q=artist:{query}&type=track&limit={limit}"
    elif content_type == 'artistID':
        endpoint = f"https://api.spotify.com/v1/artists/{query}/albums?market=US&limit={limit}"
    elif content_type == 'playlist':
        endpoint = f"https://api.spotify.com/v1/search?q=playlist:{query}&type=track&limit={limit}"
    elif content_type == 'playlistID':
        endpoint = f"https://api.spotify.com/v1/playlists/{query}/tracks?limit={limit}"
    elif content_type == 'album':
        endpoint = f"https://api.spotify.com/v1/search?q=album:{query}&type=track&limit={limit}"
    elif content_type == 'albumID':
        endpoint = f"https://api.spotify.com/v1/albums/{query}/tracks?limit={limit}"
    elif content_type == 'top50':
        endpoint = f"https://api.spotify.com/v1/me/top/tracks?limit={limit}"
    elif content_type == 'liked':
        endpoint = f"https://api.spotify.com/v1/me/tracks?limit={limit}"
    else:
        return JsonResponse({"error": "Invalid content type specified"}, status=400)

    response = get(endpoint, headers=headers)

    if response.status_code == 200:
        data = response.json()

        track_data = []

        if content_type in ['artist', 'playlist', 'album']:
            tracks = data.get('tracks', {}).get('items', [])
            for track in tracks:
                cleanTitle = track.get("name", "").replace(" ", "")
                cleanTitle = re.sub(r"[^\w&]", "", cleanTitle)
                if track.get("uri").split(':')[1] != 'track' or not cleanTitle:
                    continue
                track_item = {
                    "title": track.get("name"),
                    "artist": track["artists"][0]["name"] if track.get("artists") else "Unknown",
                    "uri": track.get("uri"),
                    "duration": track.get("duration_ms")
                }
                if not any(existing["title"] == track_item["title"] for existing in track_data):
                    track_data.append(track_item)

        elif content_type == 'artistID':
            albums = data.get('items', [])

            for album in albums:
                if album.get('album_group') != 'appears_on':
                    album_id = album.get('id')
                    tracks_endpoint = f'https://api.spotify.com/v1/albums/{album_id}/tracks'
                    tracks_response = get(tracks_endpoint, headers=headers)

                    if tracks_response.status_code == 200:
                        tracks = tracks_response.json().get('items', [])
                        for track in tracks:
                            if len(track_data) >= 50:
                                break
                            cleanTitle = track.get("name", "").replace(" ", "")
                            cleanTitle = re.sub(r"[^\w&]", "", cleanTitle)
                            if track.get("uri").split(':')[1] != 'track' or not cleanTitle:
                                continue
                            track_item = {
                                'title': track.get('name'),
                                'artist': track['artists'][0].get('name', 'Unknown') if track.get('artists') else 'Unknown',
                                'uri': track.get('uri'),
                                'duration': track.get('duration_ms')
                            }

                            # Avoid adding duplicates
                            if not any(existing['title'] == track_item['title'] for existing in track_data):
                                track_data.append(track_item)

                        if len(track_data) >= 50:
                            break
        elif content_type in ['top50', 'albumID']:
            tracks = data.get('items', [])
            for track in tracks:
                cleanTitle = track.get("name", "").replace(" ", "")
                cleanTitle = re.sub(r"[^\w&]", "", cleanTitle)
                if track.get("uri").split(':')[1] != 'track' or not cleanTitle:
                    continue

                album_images = track.get("album", {}).get("images", [])
                albumArt = album_images[0]["url"] if album_images else ""

                track_item = {
                    "title": track.get("name"),
                    "artist": track["artists"][0]["name"] if track.get("artists") else "Unknown",
                    "uri": track.get("uri"),
                    "duration": track.get("duration_ms"),
                    "albumArt": albumArt
                }
                if not any(existing["title"] == track_item["title"] for existing in track_data):
                    track_data.append(track_item)



        elif content_type in ['liked', 'playlistID']:
            tracks = data.get('items', [])
            for track in tracks:
                cleanTitle = track['track'].get("name", "").replace(" ", "")
                cleanTitle = re.sub(r"[^\w&]", "", cleanTitle)
                if track['track'].get("uri").split(':')[1] != 'track' or not cleanTitle:
                    continue

                track_item = {
                    "title": track['track'].get("name"),
                    "artist": track['track']["artists"][0]["name"] if track['track'].get("artists") else "Unknown",
                    "uri": track['track'].get("uri"),
                    "duration": track['track'].get("duration_ms")
                }

                if not any(existing["title"] == track_item["title"] for existing in track_data):
                    track_data.append(track_item)

        return JsonResponse({"tracks": track_data}, safe=False)
    else:
        # Handle error
        return JsonResponse({"error": "Failed to retrieve data from Spotify"}, status=response.status_code)


def get_spotify_track(request, track_id):
    endpoint = f"https://api.spotify.com/v1/tracks/{track_id}"
    access_token = request.session.get('access_token')

    headers = {'Authorization': f'Bearer {access_token}'}
    response = get(endpoint, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        song_data = {
            "song": f"{response_data['name']} - {response_data['artists'][0]['name']}",
            "uri": f"spotify:track:{track_id}",
            "duration": response_data['duration_ms']
        }
        return JsonResponse(song_data)
    else:
        return JsonResponse({"error": "Failed to fetch song data"}, status=500)

def get_access_token(request):
    access_token = request.session.get('access_token')

    if access_token:
        return JsonResponse({'access_token': access_token})
    else:
        return JsonResponse({'error': 'Access token not found'}, status=400)

def game(request):
    access_token = request.session.get('access_token')
    print('Access Token: ', access_token)

    if not access_token:
        return redirect('spotify_login')
    return render(request, 'game.html')

def game_intro(request):
    return render(request, 'gameintro.html')

@login_required
def get_music_personality(request):
    """Dynamically describe how someone who listens to my music acts/thinks/dresses."""
    try:
        wrapped_user = WrappedData.objects.filter(user=request.user).latest('created_at')

        top_artists = [artist['name'] for artist in wrapped_user.top_artists if isinstance(artist, dict) and 'name' in artist]
        top_genres = wrapped_user.top_genres

        prompt = f"""
        Based on the following Spotify Wrapped data:
        - Top Artists: {', '.join(top_artists)}
        - Top Genres: {', '.join(top_genres)}

        Describe how this person tends to act, think, and dress in 75 words or less.
        """

        openai.api_key = settings.OPENAI_API_KEY
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing personality based on music tastes."},
                {"role": "user", "content": prompt}
            ]
        )

        desc = response['choices'][0]['message']['content'].strip()

        return JsonResponse({
            'description': desc,
        })
    except WrappedData.DoesNotExist:
        return JsonResponse({'error': 'Cannot find any Spotify data for the specified user.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def generate_wrapped(request):
    if request.method == 'POST':
        # Create a new SpotifyWrapped instance
        now = datetime.now()
        date = now.date()
        time = now.time()

        wrapped = SpotifyWrapped.objects.create(
            user=request.user,
            date=date,
            time=time,
            user_data="Sample Data"
        )
        return JsonResponse({'status': 'success', 'id': wrapped.id, 'created_at': wrapped.created_at})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

def get_wraps(request):
    wraps = SpotifyWrapped.objects.filter(user=request.user).order_by('-created_at')
    wraps_data = []
    for wrap in wraps:
        wraps_data.append({
            'date': wrap.date.strftime('%A, %B %d, %Y'),
            'time': wrap.time.strftime('%I:%M:%S %p')
        })
    return JsonResponse({'status': 'success', 'wraps': wraps_data})


def delete_all_wraps(request):
    try:
        # Delete all SpotifyWrapped models for the current user
        SpotifyWrapped.objects.filter(user=request.user).delete()

        return JsonResponse({'status': 'success', 'message': 'All wraps deleted successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def index(request):
    context = {
        'greeting' : 'How are you, user?'
    }
    return render(request, 'index.html', context)

def welcome(request):
    is_logged_in = request.user.is_authenticated
    return render(request, 'welcome.html', {'is_logged_in': is_logged_in})

def pastwraps(request):
    return render(request, 'pastwraps.html')

def profile(request):
    return render(request, 'profile.html')

def guess_song(request):
    return render(request, 'guess_song.html')

def top_genres(request):
    return render(request, 'top_genres.html')

def in_year_you(request):
    return render(request, 'in_year_you.html')

def top_artists(request):
    return render(request, 'top_artists.html')

def top_songs(request):
    return render(request, 'top_songs.html')

def time(request):
    return render(request, 'time.html')

def aura(request):
    return render(request, 'aura.html')

def friends(request):
    return render(request, 'friends.html')

def game_transition(request):
    return render(request, 'game_transition.html')

def llm_transition(request):
    return render(request, 'llm_transition.html')