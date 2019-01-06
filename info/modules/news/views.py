from flask import render_template, g, current_app, abort, request, jsonify
from info import constants
from info.models import News
from info.utils.common import user_login_data
from info.utils.response_code import RET
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

    # 查询新闻数据
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        abort(404)

    if not news:
        abort(404)

    # 更新新闻的点击次数
    news.clicks += 1

    # 收藏逻辑代码
    is_collected = False
    if g.user:
        if news in g.user.collection_news:
            is_collected = True

    # 准备数据字典
    data = {
        "user_info": g.user.to_dict() if g.user else None,
        "click_list": click_list,
        "news": news.to_dict(),
        "is_collected": is_collected
    }
    return render_template("news/detail.html", data=data)


@news_blue.route('/news_collect', methods=["POST"])
@user_login_data
def collected_news():
    """收藏新闻"""
    if not g.user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    # 1.接收参数
    news_id = request.json.get('news_id')
    action = request.json.get('action')

    # 2.校验参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ["collect", "cancel_collect"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3.查询新闻
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询错误")

    # 4.判断是否存在
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

    # 5.收藏以及取消收藏
    if action == "cancel_collect":
        # 取消收藏
        if news in g.user.collection_news:
            g.user.collection_news.remove(news)
    else:
        # 进行收藏
        if news not in g.user.collection_news:
            g.user.collection_news.append(news)

    # 6.返回响应
    return jsonify(errno=RET.OK, errmsg="收藏成功")
