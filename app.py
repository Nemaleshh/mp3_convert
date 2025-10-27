import os
import re
import tempfile
import yt_dlp
from flask import Flask, request, send_file, render_template_string

app = Flask(__name__)

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)

HTML_FORM = '''
<!doctype html>
<html>
<head><title>YouTube to Audio</title></head>
<body>
  <h2>Download YouTube Audio (.m4a)</h2>
  <form method="post">
    <input type="url" name="url" placeholder="Paste YouTube URL" required style="width:400px;padding:8px;">
    <button type="submit">Download Audio</button>
  </form>
  {% if error %}
    <p style="color:red;">❌ {{ error }}</p>
  {% endif %}
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def download_audio():
    if request.method == 'POST':
        url = request.form.get('url')
        if not url:
            return render_template_string(HTML_FORM, error="URL is required")

        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'format': 'bestaudio[acodec=m4a]/bestaudio',  # More reliable
                'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                'quiet': True,
                'noplaylist': True,
                'extractaudio': False,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'no_warnings': True,
                'socket_timeout': 10,  # Avoid hanging
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    original_filename = ydl.prepare_filename(info)
                    full_path = os.path.join(tmpdir, os.path.basename(original_filename))

                    # Sanitize for safe download name
                    safe_title = sanitize_filename(info.get('title', 'audio'))
                    ext = info.get('ext', 'm4a')
                    download_name = f"{safe_title}.{ext}"

                    return send_file(
                        full_path,
                        as_attachment=True,
                        download_name=download_name,
                        mimetype='audio/mp4' if ext == 'm4a' else 'audio/webm'
                    )

            except Exception as e:
                return render_template_string(HTML_FORM, error=f"Download failed: {str(e)}")

    return render_template_string(HTML_FORM)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)