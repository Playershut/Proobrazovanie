import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI') or 'mysql+pymysql://ldrshza:x3E2JBC!X9KG4HWC@127.0.0.1:3308/ldrshza'

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['player15hut@gmail.com']
    POSTS_PER_PAGE = 10
    UPLOAD_FOLDER = './uploaded_files'
    ALLOWED_EXTENSIONS = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'odt', 'ods', 'odp', 'txt', 'rtf', 'jpg',
                          'jpeg', 'png', 'gif', 'svg', 'mp3', 'wav', 'm4a', 'mp4', 'mov', 'avi', 'wmv', 'mkv', 'zip']
    MAX_CONTENT_LENGTH = 512 * 1024 * 1024  # 1 GB
    MAX_IMAGE_SIZE = (128, 128)
    JPEG_QUALITY = 85
