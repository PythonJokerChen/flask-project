from info import constants
from info.models import User, News
from . import index_blue
from flask import render_template, current_app, session


@index_blue.route('/')
def index():
    """
    显示首页
    1.如果用户已经登录, 将当前登录用户的数据传到模板中
    :return:
    """
    user_id = session.get("user_id", None)
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
    news_dict = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    click_list = []
    if news_dict:
        for news in news_dict:
            click_list.append(news.to_basic_dict())
    data = {
        "user_info": user.to_dict() if user else None,
        "click_list": click_list
    }
    return render_template('news/index.html', data=data)


# 在访问网页的时候, 浏览器默认会请求/favicon.ico路径作为网站标签
# send_static_file 是flask去查找指定的静态文件所调用的方法
@index_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')
