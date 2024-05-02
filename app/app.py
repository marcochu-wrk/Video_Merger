from flask import Flask
from pywebio.input import file_upload
from pywebio.output import put_text, put_buttons, put_file, use_scope, clear_scope
from pywebio.platform.flask import webio_view
from moviepy.editor import VideoFileClip, concatenate_videoclips
import tempfile
import threading
import webbrowser
import logging
import os
import subprocess

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
    logging.debug("Starting to process files.")
    put_text("Merging files, please wait...", scope='uploads')
    with tempfile.TemporaryDirectory() as temp_dir:
        video_paths = []
        for file in uploaded_files:
            if file['content'] is None:
                logging.error(f"No content in file {file['filename']}")
                continue
            file_path = os.path.join(temp_dir, file['filename'])
            with open(file_path, 'wb') as f:
                f.write(file['content'])
            video_paths.append(file_path)

        clips = []
        for path in video_paths:
            temp_output = os.path.join(temp_dir, "temp.mp4")
            command = f'ffmpeg -i "{path}" -c copy -an "{temp_output}"'
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                logging.error(f"FFmpeg error for {path}: {result.stderr}")
                continue

            try:
                clip = VideoFileClip(temp_output)
                clips.append(clip)
            finally:
                clip.close()  # Ensure clip is closed
                if os.path.exists(temp_output):
                    os.remove(temp_output)  # Remove the file after closing the clip

        if not clips:
            put_text("Failed to process any video clips.", scope='uploads')
            return

        try:
            final_clip = concatenate_videoclips(clips, method="compose")
            output_path = os.path.join(temp_dir, "merged_output.mp4")
            final_clip.write_videofile(output_path, codec="libx264", verbose=False, logger=None)
        finally:
            for clip in clips:
                clip.close()

        with open(output_path, "rb") as f:
            video_data = f.read()

        clear_scope('uploads')
        put_file("merged_output.mp4", video_data, "Download merged video")
        put_buttons(['Reset'], [reset_app], scope='uploads')

def reset_app():
    setup_interface()

app.add_url_rule('/', 'webio_view', webio_view(setup_interface), methods=['GET', 'POST', 'OPTIONS'])

def run_flask_app():
    app.run(host='127.0.0.1', port=8080, debug=True, use_reloader=False)

def open_browser():
    threading.Event().wait(1)
    webbrowser.open_new("http://127.0.0.1:8080")

if __name__ == '__main__':
    logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
    server_thread = threading.Thread(target=run_flask_app)
    server_thread.start()
    open_browser()
    server_thread.join()