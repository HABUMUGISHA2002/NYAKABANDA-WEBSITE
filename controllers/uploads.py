import os
from datetime import datetime

from flask import current_app
from werkzeug.utils import secure_filename


def save_upload(file, folder):
    if not file or not file.filename:
        return None
    filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}")
    rel_path = os.path.join(folder, filename)
    abs_path = os.path.join(current_app.config["UPLOAD_FOLDER"], rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    file.save(abs_path)
    return rel_path.replace("\\", "/")
