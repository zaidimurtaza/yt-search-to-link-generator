from flask import Flask, request, jsonify, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from main import get_top_songs, download_song, delete_song, AUDIO_DIR, THUMBNAIL_DIR

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per day", "10 per hour"]
)

@app.route("/")
@limiter.limit("25/minute")
def index():
    return jsonify({"message": "Hello, World!", "status": "success","get_remote_address": get_remote_address()})

@app.route("/search/<song_name>")
@limiter.limit("8/minute")
def search(song_name):
    try:
        max_results = request.args.get("max_results", 2)
        songs = get_top_songs(song_name, max_results=max_results)
        return jsonify({"message": "Songs found", "status": "success","get_remote_address": get_remote_address(), "songs": songs})
    except Exception as e:
        return jsonify({"message": "No songs found", "status": "error","get_remote_address": get_remote_address(), "error": str(e)})

@app.route("/download")
@limiter.limit("8/minute")
def download():
    try:
        song_url = request.args.get("url")
        title = request.args.get("title", "unknown")
        base_url = request.url_root.rstrip('/')
        song_data = download_song(song_url, title, base_url)
        return jsonify({"message": "Song downloaded", "status": "success","get_remote_address": get_remote_address(), "song_data": song_data})
    except Exception as e:
        return jsonify({"message": "No song found", "status": "error","get_remote_address": get_remote_address(), "error": str(e)})

@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(str(AUDIO_DIR), filename)

@app.route("/thumbnails/<filename>")
def serve_thumbnail(filename):
    return send_from_directory(str(THUMBNAIL_DIR), filename)

@app.route("/delete/<filename>")
@limiter.limit("8/minute")
def delete(filename):
    try:
        result = delete_song(filename)
        return jsonify({"message": "Song deleted", "status": "success", "get_remote_address": get_remote_address(), "result": result})
    except FileNotFoundError as e:
        return jsonify({"message": "File not found", "status": "error", "get_remote_address": get_remote_address(), "error": str(e)})
    except Exception as e:
        return jsonify({"message": "Error deleting song", "status": "error", "get_remote_address": get_remote_address(), "error": str(e)})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)