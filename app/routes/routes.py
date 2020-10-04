import ast
import json
import requests
from app.api.handler import SpotifyHandler
from secrets import CLIENT_ID, CLIENT_SECRET
from app.api.spotify_client import SpotifyClient
from flask import render_template, Blueprint, request, redirect, url_for, session

blueprint = Blueprint('app', __name__)

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')


spotify_client = SpotifyClient(client_id, client_secret, client_side_url='CLIENT_URL', port=8002)
handler = SpotifyHandler()


@blueprint.route("/login", methods=['POST', 'GET'])
def login():
    auth_url = spotify_client.get_auth_url()
    return redirect(auth_url)


@blueprint.route("/callback/q")
def callback():
    auth_token = request.args['code']
    spotify_client.get_authorization(auth_token)
    authorization_header = spotify_client._authorization_header
    session['authorization_header'] = authorization_header
    return redirect(url_for("app.select_tracks"))


@blueprint.route("/select-tracks", methods=['GET', 'POST'])
def select_tracks():
    if request.method == 'GET':
        return render_template('loading.html')


@blueprint.route("/load", methods=['GET', 'POST'])
def load():
    authorization_header = session['authorization_header']
    get_letters = lambda x: ''.join([i for i in x if not i.isdigit()])

    if request.method == 'GET':
        # -------- Get user's name, id, and set session --------
        profile_data = handler.get_user_profile_data(authorization_header)
        user_display_name, user_id = profile_data['display_name'], profile_data['id']
        session['user_id'], session['user_display_name'] = user_id, user_display_name

        # -------- Get user playlist data --------
        playlist_data = handler.get_user_playlist_data(authorization_header, user_id)

        return render_template('select.html',
                               user_display_name=user_display_name,
                               playlists_data=playlist_data,
                               func=get_letters)

    return render_template('404.html')


@blueprint.route("/finetune", methods=['GET', 'POST'])
def finetune():
    selected_tracks = request.form.get('selected_tracks').split(',')
    session['selected_tracks'] = selected_tracks
    return render_template('finetune.html')


@blueprint.route("/your-playlist", methods=['GET', 'POST'])
def your_playlist():
    authorization_header = session['authorization_header']
    fine_tune_vals = ast.literal_eval(request.form.get('fine-tune-values'))
    fine_tune_vals = [{val['key']: val['val'] for val in fine_tune_vals}][0]

    if request.method == 'POST':
        params = {
            'seed_tracks': session['selected_tracks'],
            'danceability': float(fine_tune_vals['danceability']) / 10,
            'energy': float(fine_tune_vals['energy']) / 10,
            'loudness': (float(fine_tune_vals['loudness']) * -60 / 10)
        }

        get_reccomended_url = f"https://api.spotify.com/v1/recommendations?limit={25}"
        response = requests.get(get_reccomended_url, headers=authorization_header, params=params).text
        response = list(json.loads(response)['tracks'])
        track_uris = [track['uri'] for track in response]
        session['traks_uri'] = track_uris

        return render_template('result.html', data=response)

    return redirect(url_for('not_found'))


@blueprint.route("/save-playlist", methods=['GET', 'POST'])
def save_playlist():
    authorization_header = session['authorization_header']
    user_id = session['user_id']

    playlist_name = request.form.get('playlist_name')
    playlist_data = json.dumps({
        "name": playlist_name,
        "description": "Recommended songs",
        "public": True
    })
    create_playlist_url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    response = requests.post(create_playlist_url, headers=authorization_header, data=playlist_data).text
    playlist_id = json.loads(response)['id']

    track_uris = session['traks_uri']
    tracks_data = json.dumps({
        "uris": track_uris,
    })
    add_items_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    response = requests.post(add_items_url, headers=authorization_header, data=tracks_data).text

    return render_template('listen.html', playlist_id=playlist_id)


@blueprint.route("/")
def main():
    return render_template('main.html')


@blueprint.route("/not-found")
def not_found():
    return render_template('404.html')


@blueprint.route("/listen")
def listen():
    return render_template('listen.html')


@blueprint.route("/refresh", methods=['GET', 'POST'])
def refresh_result():
    return redirect(url_for("app.your_playlist"))
