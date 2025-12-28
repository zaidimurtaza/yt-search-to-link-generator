from dotenv import load_dotenv
import os
from googleapiclient.discovery import build
from pytubefix import YouTube
import datetime
import time
from pathlib import Path
import requests
load_dotenv()
API_KEY = os.getenv("key")
YOUTUBE = build("youtube", "v3", developerKey=API_KEY)

UPLOAD_DIR = Path("songs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR = UPLOAD_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAIL_DIR = UPLOAD_DIR / "thumbnails"
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

def unique_file_name(song_name):
    song_name = song_name.replace(" ", "_")
    song_name = song_name.replace(":", "_")
    song_name = song_name.replace(".", "_")
    song_name = song_name.replace("-", "_")
    song_name = song_name.replace("(", "_")
    song_name = song_name.replace(")", "_")
    song_name = song_name.replace("'", "_")
    song_name = song_name.replace("\"", "_")
    song_name = song_name.replace("/", "_")
    song_name = song_name.replace("\\", "_")
    song_name = song_name.replace("|", "_")
    song_name = song_name.replace("?", "_")
    song_name = song_name.replace("!", "_")
    song_name = song_name.replace("@", "_")
    song_name = song_name.replace("#", "_")
    song_name = song_name.replace("$", "_")
    song_name = song_name.replace("%", "_")
    song_name = song_name.replace("^", "_")
    song_name = song_name.replace("&", "_")
    song_name = song_name.replace("*", "_")
    song_name = song_name.replace("+", "_")
    song_name = song_name.replace("=", "_")
    filename = f"{song_name[:10]}_{time.time()}"
    return filename

def download_thumbnail(url, filename):
    thumbnail_path = THUMBNAIL_DIR / filename
    response = requests.get(url)
    with open(thumbnail_path, 'wb') as f:
        f.write(response.content)
    return thumbnail_path

def get_top_songs(song_name, max_results=2):
    request = YOUTUBE.search().list(
        q=song_name,
        part="snippet",
        type="video",
        maxResults=max_results
    )
    response = request.execute()
    results = []
    for item in response['items']:
        video = {
            "title": item['snippet']['title'],
            "channel": item['snippet']['channelTitle'],
            "video_url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
            "video_id": item['id']['videoId'],
            "thumbnail_url": item['snippet']['thumbnails']['high']['url']
        }
        results.append(video)
    return results

def download_song(song_url, title="abc", base_url=""):
    yt = YouTube(song_url)
    filename = unique_file_name(title)

    thumbnail_path = download_thumbnail(yt.thumbnail_url, filename+".jpg")
    # filter only audio
    audio_stream = yt.streams.filter(only_audio=True).first()

    output_file = audio_stream.download(filename=filename+".mp4",
    output_path=str(AUDIO_DIR))
    
    # Convert Path objects to strings and generate URLs
    audio_filename = Path(output_file).name
    thumbnail_filename = Path(thumbnail_path).name
    
    audio_url = f"{base_url}/audio/{audio_filename}" if base_url else f"/audio/{audio_filename}"
    thumbnail_url = f"{base_url}/thumbnails/{thumbnail_filename}" if base_url else f"/thumbnails/{thumbnail_filename}"
    
    return {
        "filename": filename,
        "audio_url": audio_url,
        "thumbnail_url": thumbnail_url,
    }

def delete_song(filename):
    audio_path = AUDIO_DIR / f"{filename}.mp4"
    thumbnail_path = THUMBNAIL_DIR / f"{filename}.jpg"
    audio_path.unlink()
    thumbnail_path.unlink()
    return {"message": "Song deleted", "status": "success"}

if __name__ == "__main__":
    # songs = get_top_songs("Shape of You", max_results=1)
    # print(json.dumps(songs, indent=4))
    file_path = download_song("https://www.youtube.com/watch?v=JGwWNGJdvx8", "Shape of You")
    print(file_path)
    print(datetime.datetime.now())
    print(time.time())
    delete_song("shape_1766918972.228894")