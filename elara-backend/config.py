import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'elara-sih2026-production-secret-key')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # File Storage Paths
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'storage', 'uploads')
    EXPORT_FOLDER = os.path.join(BASE_DIR, 'storage', 'exports')
    
    # Allowed Formats
    ALLOWED_EXTENSIONS = {'tif', 'tiff', 'png', 'jpg', 'jpeg'}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024 * 1024  # 5 GB Max limit

    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.EXPORT_FOLDER, exist_ok=True)