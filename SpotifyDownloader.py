import os
import re
import requests
import spotipy
import subprocess
import secret
from pytube import YouTube
from moviepy.editor import *
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, error
from spotipy.oauth2 import SpotifyClientCredentials
from googleapiclient.discovery import build


SPOTIFY_CLIENT_ID = secret.SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET = secret.SPOTIFY_CLIENT_SECRET

YOUTUBE_API_KEY = secret.YOUTUBE_API_KEY

client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)


def main():

    spotify_link = getSpotifyLink()

    if 'track' in spotify_link:
        output_folder = 'music'
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

        downloadTrack(spotify_link, output_folder)

        print("\nFinished!", end='\n\n')

    elif 'playlist' in spotify_link:
        playlist = sp.playlist(spotify_link)
        output_folder = playlist['name'].replace(' ', '-')

        if not os.path.exists(output_folder):
            os.mkdir(output_folder)
        
        # Loop through tracks in playlist and download them individually
        tracks = playlist['tracks']['items']
        for track in tracks:
            track_link = track['track']['external_urls']['spotify']
            downloadTrack(track_link, output_folder)
        
        print("\nFinished!", end='\n\n')

    else:
        print("Unsupported Spotify link", end='\n\n')


def getSpotifyLink():

    while True:
        spotify_link = input("Please enter the link to a song or playlist: ").strip()
        print('')
        match = re.search(r"(https://)?open\.spotify\.com/(track|playlist)/.+$", spotify_link)
        if match:
            try:
                # Query Spotify API for track information using the track ID from the link
                track = sp.track(spotify_link)
                break
            except spotipy.SpotifyException:
                try:
                    # Query Spotify API for playlist information using the playlist ID from the link
                    playlist = sp.playlist(spotify_link)
                    if playlist['public'] == False:
                        print(
                            "Playlist is private. Please make your playlist public and try again."
                        , end='\n\n')
                        continue
                    break
                except spotipy.SpotifyException:
                    print("Spotify link does not exist or invalid.", end='\n\n')
        else:
            print("Invalid link.", end='\n\n')
    
    return spotify_link


def downloadTrack(spotify_link, output_folder):

    # Get data about track with Spotify API
    result = getTrackData(spotify_link, output_folder)

    if result is not None:
        track_name, artist_name, album_name, album_art_name = result
    else:
        return
    
    # With information about track name and artist, search
    # for corresponding YouTube video with YouTube API
    video = getYouTubeVideo(track_name, artist_name)

    # Download mp3 (and mp4) from the YouTube video
    mp3_file_name, mp4_file_name = downloadmp3(track_name, artist_name, video, output_folder)

    # Add metadata to mp3 file
    addMetadata(
        mp3_file_name, 
        track_name, 
        artist_name, 
        album_name, 
        album_art_name, 
        output_folder
        )

    # Remove leftover mp4 and album art jpg
    os.remove(os.path.join(output_folder, mp4_file_name))
    os.remove(os.path.join(output_folder, album_art_name))


def getTrackData(spotify_link, output_folder):

    # Extract information about the track
    track = sp.track(spotify_link)
    track_name = track['name']
    artist_name = track['artists'][0]['name']
    album_name = track['album']['name']
    album_art_url = track['album']['images'][0]['url']

    print(f"\nDownloading '{track_name}' by '{artist_name}'...", end='\n\n')

    mp3_file_name = f"{track_name}_by_{artist_name}.mp3".replace(' ', '-')
    file_path = os.path.join(output_folder, mp3_file_name)
    if os.path.exists(file_path):
        while True:
            yes_or_no = input(
                f"'{track_name}' by '{artist_name}' already exists in '{output_folder}'. Overwrite [Y/N]? "
                )
            print('')

            if yes_or_no.upper() == 'Y':
                os.remove(file_path)
                break
            elif yes_or_no.upper() == 'N':
                return None
            else:
                print("Please enter 'Y' or 'N' only.", end='\n\n')
                

    # Retrieve the track's album art
    response = requests.get(album_art_url)
    album_art_name = f"{track_name.replace(' ', '-')}_album_art.jpg"
    if response.status_code == 200:
        with open(os.path.join(output_folder, album_art_name), 'wb') as f:
            f.write(response.content)

    return track_name, artist_name, album_name, album_art_name


def downloadmp3(track_name, artist_name, video, output_folder):

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    # Download mp4
    video.download(output_path=output_folder) 
    mp4_file_name = video.default_filename 
    mp3_file_name = (f"{track_name}_by_{artist_name}.mp3").replace(' ', '-')

    # Use ffmpeg tool to extract mp3 from mp4
    run_ffmpeg(['ffmpeg', 
                    '-i', 
                    os.path.join(output_folder, mp4_file_name), 
                    os.path.join(output_folder, mp3_file_name)
                    ])

    return mp3_file_name, mp4_file_name


def addMetadata(mp3_file_name, track_name, artist_name, album_name, album_art_name, output_folder):

    audio = MP3(os.path.join(output_folder, mp3_file_name), ID3=ID3)

    with open(os.path.join(output_folder, album_art_name), 'rb') as img:
        album_art = img.read()

    # Assign album art to mp3
    picture = APIC(  
        encoding=3,  
        mime='image/jpeg',  
        type=3,  
        desc=u'Cover',  
        data=album_art 
    )
    try:
        audio.tags.add(picture)
    except error:
        audio.tags.update(picture)

    # Adding metadata to mp3
    audio.tags.add(TIT2(encoding=3, text=track_name))  
    audio.tags.add(TPE1(encoding=3, text=artist_name)) 
    audio.tags.add(TALB(encoding=3, text=album_name))  
    audio.save()


def getYouTubeVideo(track_name, artist_name):

    search_query = f"{track_name} by {artist_name} official audio"

    # Search for YouTube video based on query
    search_response = youtube.search().list(
        q=search_query,
        part='id',
        type='video',
        maxResults=1 
    ).execute()

    # Create YouTube object based on search
    video_id = search_response['items'][0]['id']['videoId']
    video_link = f"https://www.youtube.com/watch?v={video_id}"
    video = YouTube(video_link)
    video = video.streams.first()

    return video


def run_ffmpeg(command):
    with open(os.devnull, 'w') as null_device:
        subprocess.run(command, stdout=null_device, stderr=null_device)


if __name__ == "__main__":
    main()



