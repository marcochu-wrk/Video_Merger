from flask import Flask
from pywebio.input import file_upload
from pywebio.output import put_text, put_buttons, put_file, popup, clear_scope, use_scope
from pywebio.platform.flask import webio_view
from pywebio import start_server
from moviepy.editor import VideoFileClip, concatenate_videoclips
import os
import tempfile

app = Flask(__name__)

# Function to initialize or reset the user interface
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
    # Completely clear the uploads scope and reinitialize the interface
    setup_interface()

app.add_url_rule('/', 'webio_view', webio_view(setup_interface), methods=['GET', 'POST', 'OPTIONS'])

if __name__ == '__main__':
    start_server(setup_interface, port=80)