from dotenv import load_dotenv
import os
from googleapiclient.discovery import build
from yt_dlp import YoutubeDL
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

def download_song(song_url, title="abc", base_url="", max_retries=3):
    filename = unique_file_name(title)
    # yt-dlp will determine the extension, so we use a template
    audio_path_template = str(AUDIO_DIR / f"{filename}.%(ext)s")
    
    # Try different extractor options to bypass restrictions
    extractor_options = [
        # Method 1: Android client (often bypasses restrictions)
        {
            'extractor_args': {'youtube': {'player_client': ['android']}},
        },
        # Method 2: iOS client
        {
            'extractor_args': {'youtube': {'player_client': ['ios']}},
        },
        # Method 3: TV client
        {
            'extractor_args': {'youtube': {'player_client': ['tv_embedded']}},
        },
        # Method 4: Default web client
        {},
    ]
    
    # Retry logic with different clients
    for attempt in range(max_retries):
        for method_idx, extractor_opts in enumerate(extractor_options):
            try:
                # Get video info first to extract thumbnail
                info_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    **extractor_opts
                }
                
                with YoutubeDL(info_opts) as ydl:
                    video_info = ydl.extract_info(song_url, download=False)
                    thumbnail_url = video_info.get('thumbnail', '')
                
                # Download thumbnail
                if thumbnail_url:
                    thumbnail_path = download_thumbnail(thumbnail_url, filename+".jpg")
                else:
                    raise Exception("Could not get thumbnail URL")
                
                # Download audio with specific format
                download_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': audio_path_template,
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,
                    **extractor_opts
                }
                
                with YoutubeDL(download_opts) as ydl:
                    ydl.download([song_url])
                
                # Find the downloaded file (yt-dlp may use different extensions)
                downloaded_files = list(AUDIO_DIR.glob(f"{filename}.*"))
                if not downloaded_files:
                    raise Exception("Downloaded file not found")
                
                # Get the actual downloaded file
                audio_path = downloaded_files[0]
                audio_filename = audio_path.name
                thumbnail_filename = Path(thumbnail_path).name
                
                audio_url = f"{base_url}/audio/{audio_filename}" if base_url else f"/audio/{audio_filename}"
                thumbnail_url_final = f"{base_url}/thumbnails/{thumbnail_filename}" if base_url else f"/thumbnails/{thumbnail_filename}"
                
                return {
                    "filename": filename,
                    "audio_url": audio_url,
                    "thumbnail_url": thumbnail_url_final,
                }
                
            except Exception as e:
                error_msg = str(e)
                # If this is the last method and last attempt, raise error
                if method_idx == len(extractor_options) - 1 and attempt == max_retries - 1:
                    raise Exception(f"Failed after {max_retries} attempts with all methods: {error_msg}")
                # Otherwise, try next method or retry
                if method_idx < len(extractor_options) - 1:
                    continue  # Try next method
                else:
                    # All methods failed, wait and retry
                    wait_time = (2 ** attempt) * 2  # 2, 4, 8 seconds
                    time.sleep(wait_time)
                    break  # Break inner loop to retry with first method

def delete_song(filename):
    # Find audio file (may have different extensions)
    audio_files = list(AUDIO_DIR.glob(f"{filename}.*"))
    thumbnail_path = THUMBNAIL_DIR / f"{filename}.jpg"
    
    # Delete audio file(s) if found
    for audio_file in audio_files:
        if audio_file.exists():
            audio_file.unlink()
    
    # Delete thumbnail if exists
    if thumbnail_path.exists():
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