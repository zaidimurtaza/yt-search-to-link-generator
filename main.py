from dotenv import load_dotenv
import os
from googleapiclient.discovery import build
from yt_dlp import YoutubeDL
import datetime
import time
from pathlib import Path
import requests
import base64
import tempfile
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
    audio_path_template = str(AUDIO_DIR / f"{filename}.%(ext)s")
    
    # Check for cookies - try multiple methods
    cookies_path = None
    
    # Method 1: Check environment variable for file path
    cookies_file = os.getenv('YOUTUBE_COOKIES_FILE', 'cookies.txt')
    if Path(cookies_file).exists():
        cookies_path = Path(cookies_file)
    elif Path('cookies.txt').exists():
        cookies_path = Path('cookies.txt')
    
    # Method 2: Check for base64 encoded cookies in environment
    cookies_b64 = os.getenv('YOUTUBE_COOKIES_B64')
    if not cookies_path and cookies_b64:
        try:
            cookies_content = base64.b64decode(cookies_b64).decode('utf-8')
            # Create temporary cookies file
            temp_cookies = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_cookies.write(cookies_content)
            temp_cookies.close()
            cookies_path = Path(temp_cookies.name)
        except Exception:
            pass
    
    # Most aggressive bypass options
    base_opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'format': 'bestaudio/best',
        'outtmpl': audio_path_template,
        'socket_timeout': 60,
        'extractor_retries': 5,
        'fragment_retries': 5,
        'retries': 5,
        'file_access_retries': 3,
        'http_chunk_size': 10485760,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
        'extractor_args': {
            'youtube': {
                'player_client': ['android'],
                'player_skip': ['webpage', 'configs'],
                'skip': ['dash', 'hls'],
            }
        },
        'http_headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }
    }
    
    if cookies_path:
        base_opts['cookiefile'] = str(cookies_path)
    
    # Try different client strategies in order of effectiveness
    client_strategies = [
        {
            'player_client': ['android'],
            'player_skip': ['webpage', 'configs'],
            'skip': ['dash', 'hls'],
        },
        {
            'player_client': ['android_embedded'],
            'player_skip': ['webpage', 'configs'],
        },
        {
            'player_client': ['ios'],
            'player_skip': ['webpage', 'configs'],
        },
        {
            'player_client': ['tv_embedded'],
            'player_skip': ['webpage'],
        },
        {
            'player_client': ['web'],
            'player_skip': [],
        },
    ]
    
    last_error = None
    for attempt in range(max_retries):
        for strategy_idx, strategy in enumerate(client_strategies):
            try:
                opts = base_opts.copy()
                opts['extractor_args'] = {'youtube': strategy}
                
                # Extract video ID for thumbnail fallback
                video_id = None
                try:
                    video_id = song_url.split('v=')[-1].split('&')[0].split('?')[0]
                except:
                    pass
                
                # First, get video info to extract thumbnail
                info_opts = opts.copy()
                info_opts['skip_download'] = True
                
                video_info = None
                thumbnail_url = None
                
                try:
                    with YoutubeDL(info_opts) as ydl:
                        video_info = ydl.extract_info(song_url, download=False)
                        thumbnail_url = (video_info.get('thumbnail') or 
                                       (video_info.get('thumbnails', [{}])[0].get('url') if video_info.get('thumbnails') else None))
                        
                        if not thumbnail_url and video_id:
                            thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
                except Exception as info_error:
                    # Fallback: Use YouTube Data API to get thumbnail
                    if video_id and API_KEY:
                        try:
                            api_response = YOUTUBE.videos().list(
                                part='snippet',
                                id=video_id
                            ).execute()
                            if api_response.get('items'):
                                thumbnail_url = api_response['items'][0]['snippet']['thumbnails']['high']['url']
                        except:
                            pass
                    
                    # Final fallback: construct thumbnail URL from video ID
                    if not thumbnail_url and video_id:
                        thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
                
                # Download thumbnail if we have a URL
                thumbnail_path = None
                if thumbnail_url:
                    try:
                        thumbnail_path = download_thumbnail(thumbnail_url, filename+".jpg")
                    except:
                        # Thumbnail download failed, continue anyway
                        pass
                
                # Now download the audio
                download_opts = opts.copy()
                download_opts.pop('skip_download', None)
                
                with YoutubeDL(download_opts) as ydl:
                    ydl.download([song_url])
                
                # Find the downloaded file
                downloaded_files = list(AUDIO_DIR.glob(f"{filename}.*"))
                if not downloaded_files:
                    raise Exception("Downloaded file not found after download")
                
                audio_path = downloaded_files[0]
                audio_filename = audio_path.name
                thumbnail_filename = Path(thumbnail_path).name if thumbnail_path else f"{filename}.jpg"
                
                audio_url = f"{base_url}/audio/{audio_filename}" if base_url else f"/audio/{audio_filename}"
                thumbnail_url_final = f"{base_url}/thumbnails/{thumbnail_filename}" if base_url else f"/thumbnails/{thumbnail_filename}"
                
                return {
                    "filename": filename,
                    "audio_url": audio_url,
                    "thumbnail_url": thumbnail_url_final,
                }
                
            except Exception as e:
                last_error = str(e)
                error_lower = last_error.lower()
                
                # Check for bot detection
                is_bot_error = any(keyword in error_lower for keyword in ['bot', 'sign in', 'cookies', 'confirm you'])
                
                # If it's the last attempt with last strategy, raise
                if strategy_idx == len(client_strategies) - 1 and attempt == max_retries - 1:
                    if is_bot_error:
                        raise Exception(f"YouTube bot detection: {last_error[:300]}. Solution: Add cookies.txt file or set YOUTUBE_COOKIES_FILE environment variable.")
                    raise Exception(f"Download failed: {last_error[:300]}")
                
                # Wait before next attempt
                if strategy_idx < len(client_strategies) - 1:
                    time.sleep(0.5)
                else:
                    time.sleep(2 * (attempt + 1))
                    break
    
    raise Exception(f"All attempts failed. Last error: {last_error[:300] if last_error else 'Unknown error'}")

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