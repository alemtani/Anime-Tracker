import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAL_BASE_URL = os.environ.get('MAL_BASE_URL')
    MAL_HEADERS = {'X-MAL-CLIENT-ID': os.environ.get('MAL_CLIENT_ID')}
    ANIMES_PER_PAGE = 10
    TRACKERS_PER_PAGE = 1