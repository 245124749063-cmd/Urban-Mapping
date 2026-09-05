from flask import Flask
from flask_cors import CORS
from config import Config
from routes.upload import upload_bp
from routes.inference import inference_bp
from routes.validation import validation_bp
from routes.export import export_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.init_app(app)

    # Enable CORS for frontend integration
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register Route Blueprints
    app.register_blueprint(upload_bp)
    app.register_blueprint(inference_bp)
    app.register_blueprint(validation_bp)
    app.register_blueprint(export_bp)

    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Internal Server Error in ELARA Pipeline", "details": str(error)}, 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)