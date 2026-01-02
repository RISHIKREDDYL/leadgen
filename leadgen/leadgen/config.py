import os

domain = 'mits.ac.in'
# Use environment variable for download folder, defaulting to a Linux-friendly path
download_folder = os.getenv('DOWNLOAD_FOLDER', os.path.join('files', 'mits.ac.in', 'downloaded'))
