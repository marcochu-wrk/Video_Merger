from flask import Flask
from pywebio.input import file_upload
from pywebio.output import put_text, put_buttons, put_file, popup, clear_scope, use_scope
from pywebio.platform.flask import webio_view
from moviepy.editor import VideoFileClip, concatenate_videoclips
import os
import tempfile
import threading
import webbrowser

app = Flask(__name__)

def setup_interface():
    with use_scope('uploads', clear=True):
        put_text("Upload new files to merge:", scope='uploads')
        uploaded_files = file_upload("Select MP4 files", accept=".mp4", multiple=True)
        if uploaded_files:
            display_uploaded_files(uploaded_files)

def display_uploaded_files(uploaded_files):
    clear_scope('uploads')
    for file in uploaded_files:
        put_text(f"Uploaded: {file['filename']}", scope='uploads')
    put_buttons(['Merge and Download'], [lambda: process_files(uploaded_files)], scope='uploads')

def process_files(uploaded_files):
    put_text("Merging files, please wait...", scope='uploads')
    with tempfile.TemporaryDirectory() as temp_dir:
        video_paths = []
        for file in uploaded_files:
            file_path = os.path.join(temp_dir, file['filename'])
            with open(file_path, 'wb') as f:
                f.write(file['content'])
            video_paths.append(file_path)

        clips = [VideoFileClip(path) for path in video_paths]
        final_clip = concatenate_videoclips(clips, method="compose")
        output_path = os.path.join(temp_dir, "merged_output.mp4")
        final_clip.write_videofile(output_path, codec="libx264")

        clear_scope('uploads')
        put_file("merged_output.mp4", open(output_path, "rb").read(), "Download merged video")
        put_buttons(['Reset'], [reset_app], scope='uploads')

def reset_app():
    setup_interface()

app.add_url_rule('/', 'webio_view', webio_view(setup_interface), methods=['GET', 'POST', 'OPTIONS'])

def run_flask_app():
    app.run(host='127.0.0.1', port=8080, debug=True, use_reloader=False)

def open_browser():
    """Open a browser after waiting for the server to start."""
    threading.Event().wait(1)  # Wait for 1 second to give the server time to start
    webbrowser.open_new("http://127.0.0.1:8080")

if __name__ == '__main__':
    # Remove daemon=True to ensure that the Flask server thread isn't killed when main thread exits
    server_thread = threading.Thread(target=run_flask_app)
    server_thread.start()  # Start the server thread

    open_browser()  # Open the browser

    server_thread.join()  # Wait for the server thread to finish