from info import redis_db
from . import index_blue


@index_blue.route('/')
def index():
    redis_db.set('name', 'Joker')
    return 'index'
