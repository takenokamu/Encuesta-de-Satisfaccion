import os
from datetime import timedelta

class Config:
    """Configuración base para la aplicación"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'tu_clave_secreta_temporal')
    
    # Configuración MySQL
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'Ericko11$')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'encuestas_db')
    
    # Configuración Email
    EMAIL_SENDER = os.environ.get('EMAIL_SENDER', 'takenokamu@gmail.com')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'kcdvjijtgcsucvmb')
    
    # Configuración de carpetas
    STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    IMAGES_FOLDER = os.path.join(STATIC_FOLDER, 'images')
    
    # Sesión permanente
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

class DevelopmentConfig(Config):
    """Configuración para entorno de desarrollo"""
    DEBUG = True

class ProductionConfig(Config):
    """Configuración para entorno de producción"""
    DEBUG = False
    
    # En producción, asegúrate de que estas variables estén configuradas en el entorno
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

class TestingConfig(Config):
    """Configuración para pruebas"""
    TESTING = True
    # Puedes configurar una base de datos de prueba
    MYSQL_DB = 'encuestas_test_db'

# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Asegurar que exista la carpeta de imágenes
os.makedirs(Config.IMAGES_FOLDER, exist_ok=True)