from flask import render_template, g, current_app, abort
from info import constants
from info.models import News
from info.utils.common import user_login_data
from . import news_blue


@news_blue.route("/<int:news_id>")
@user_login_data
def news_detail(news_id):
    """显示首页"""
    # 查询新闻点击量数据
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        abort(404)
    click_list = []
    if news_list:
        for news in news_list:
            click_list.append(news.to_basic_dict())

    # # 查询新闻数据
    # news = None
    # try:
    #     news = News.query.get(news_id)
    # except Exception as e:
    #     current_app.logger.error(e)
    #     abort(404)
    # if not news:
    #     abort(404)
    # # 更新新闻的点击次数
    # news.clicks += 1

    # 准备数据字典
    data = {
        "user_info": g.user.to_dict() if g.user else None,
        "click_list": click_list,
        "news": news.to_dict()
    }
    return render_template("news/detail.html", data=data)
