# SpotifyDownloader

## Introduction
This script can be used to download songs or playlists from Spotify. Simply paste the link to a song or playlist from Spotify, and the tracks will be downloaded as MP3s.

For a song, the script uses Spotify's API to gather information about the track. Then, the script uses YouTube's API and various libraries to search for and download the track from YouTube. For a playlist, the script loops through every song and uses the same methodology as just described. 

## Setup
1. Clone the repository by pasting `https://github.com/bjiruff/SpotifyDownloader.git` into your terminal or by downloading this repository's ZIP file.
2. Install ffmpeg, which is used by the script to get MP3s. For MacOS users, if you haven't installed Homebrew, do so by pasting the following command in your terminal:
  `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`. Upon installation, run `brew install ffmpeg`. For Windows users, consult the tutorial [here](https://phoenixnap.com/kb/ffmpeg-windows).
3. Make a [Spotify for Developers](https://developer.spotify.com/) account, create an app, and fetch the *client_id* and *client_secret* associated with your app. Next, make a project on the [Google Cloud Platform](https://console.cloud.google.com/) and create an *API key*. These credentials will be used to access the Spotify and YouTube APIs, respectively.
4. In the project's directory, rename the file *secret_template.py* into *secret.py* and paste in your credentials.
5. Navigate to the terminal in your project's directory and run `pip install -r requirements.txt` to download the libraries needed for the script to function.
6. Again in the terminal, run `python SpotifyDownloader.py` or `python3 SpotifyDownloader.py` to begin downloading songs or playlists.


