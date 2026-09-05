from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@upload_bp.route('/api/v1/upload', methods=['POST'])
def upload_imagery():
    if 'file' not in request.files:
        return jsonify({"error": "No file parameter in request"}), 400
        
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid or missing file format. Upload GeoTIFF/PNG/JPG"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    return jsonify({
        "status": "uploaded",
        "filename": filename,
        "filepath": filepath,
        "size_mb": round(os.path.getsize(filepath) / (1024 * 1024), 2)
    }), 200