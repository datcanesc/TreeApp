import time
from flask import Flask
from config import Config
from models import db, User
from routes.routes_users import bp_users
from routes.routes_files import bp_files
from werkzeug.security import generate_password_hash
import os
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(dotenv_path)

DEFAULT_USER = os.getenv('DEFAULT_USER')
DEFAULT_PASSWORD = os.getenv('DEFAULT_PASSWORD')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    try:
        db.init_app(app)
        with app.app_context():
            # Introduce a delay to ensure DB is fully set up
            time.sleep(5)  # Delay in seconds
            db.create_all()
            print("Veritabanı bağlantısı başarılı ve tablolar oluşturuldu.")
            
    except Exception as e:
        print(f"Veritabanına bağlanırken hata oluştu: {e}")

    app.register_blueprint(bp_users, url_prefix='/api')
    app.register_blueprint(bp_files)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
