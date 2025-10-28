import os
import re
import shutil
import yt_dlp
from flask import Flask, request, send_file, render_template_string

app = Flask(__name__)

# ---------- Utility to sanitize filenames ----------
def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)

# ---------- Remove ANSI escape codes from yt-dlp errors ----------
def clean_error_message(err_str):
    # Remove ANSI color codes like \x1b[0;31m
    ansi_escape = re.compile(r'\x1b$$[0-9;]*m')
    cleaned = ansi_escape.sub('', err_str)
    # Also remove common prefixes like "ERROR: "
    if cleaned.startswith("ERROR: "):
        cleaned = cleaned[7:]
    return cleaned.strip()

# ---------- Simple HTML form ----------
HTML_FORM = '''
<!doctype html>
<html>
<head><title>YouTube to Audio</title></head>
<body style="font-family:sans-serif;">
  <h2>🎵 YouTube to Audio (.m4a / .webm)</h2>
  <form method="post">
    <input type="url" name="url" placeholder="Paste YouTube URL" required style="width:400px;padding:8px;">
    <button type="submit" style="padding:8px 16px;">Download Audio</button>
  </form>
  {% if error %}
    <p style="color:red;">❌ {{ error }}</p>
  {% endif %}
</body>
</html>
'''

# ---------- Main route ----------
@app.route('/', methods=['GET', 'POST'])
def download_audio():
    if request.method == 'POST':
        url = request.form.get('url')
        if not url:
            return render_template_string(HTML_FORM, error="URL is required")

        downloads_dir = os.path.join(os.getcwd(), "downloads")
        os.makedirs(downloads_dir, exist_ok=True)

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'format': 'bestaudio[acodec=m4a]/bestaudio',
                'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                'quiet': True,
                'noplaylist': True,
                'nocheckcertificate': True,
                'no_warnings': True,
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    original_filename = ydl.prepare_filename(info)
                    safe_title = sanitize_filename(info.get('title', 'audio'))
                    ext = info.get('ext', 'm4a')
                    download_name = f"{safe_title}.{ext}"

                    final_path = os.path.join(downloads_dir, download_name)
                    shutil.copyfile(original_filename, final_path)

                    return send_file(
                        final_path,
                        as_attachment=True,
                        download_name=download_name,
                        mimetype='audio/mp4' if ext == 'm4a' else 'audio/webm'
                    )

            except Exception as e:
                err_msg = clean_error_message(str(e))
                # Show a slightly friendlier message for common network issues
                if "getaddrinfo failed" in err_msg or "Failed to resolve" in err_msg:
                    user_msg = "Temporary network issue. Please try again in a few seconds."
                else:
                    user_msg = err_msg or "Download failed. The video may be unavailable."
                return render_template_string(HTML_FORM, error=user_msg)

    return render_template_string(HTML_FORM)

# ---------- Run app ----------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Running on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)  # ⚠️ Set debug=False for production!