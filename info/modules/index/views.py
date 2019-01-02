from info import redis_db
from . import index_blue
from flask import render_template, current_app


@index_blue.route('/')
def index():
    redis_db.set('name', 'Joker')
    return render_template('news/index.html')


# 在访问网页的时候, 浏览器默认会请求/favicon.ico路径作为网站标签
# send_static_file 是flask去查找指定的静态文件所调用的方法
@index_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')