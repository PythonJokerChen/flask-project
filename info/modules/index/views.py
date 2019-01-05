from info import constants
from info.models import News, Category
from info.utils.response_code import RET
from info.utils.common import user_login_data
from . import index_blue
from flask import render_template, current_app, session, request, jsonify, g


@index_blue.route('/')
@user_login_data
def index():
    """显示首页"""

    # 查询新闻数据
    news_dict = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    click_list = []
    if news_dict:
        for news in news_dict:
            click_list.append(news.to_basic_dict())

    # 查询分类数据
    categories = Category.query.all()
    category_li = []
    if categories:
        for category in categories:
            category_li.append(category.to_dict())

    # 准备数据字典
    data = {
        "user_info": g.user.to_dict() if g.user else None,
        "click_list": click_list,
        "category_li": category_li
    }

    # 返回数据渲染模板
    return render_template('news/index.html', data=data)


# 在访问网页的时候, 浏览器默认会请求/favicon.ico路径作为网站标签
# send_static_file 是flask去查找指定的静态文件所调用的方法
@index_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')


@index_blue.route('/news_list')
def news_list():
    """获取首页新闻数据"""
    # 1.获取数据
    cid = request.args.get('cid', '1')  # 新闻分类的id
    page = request.args.get('page', '1')  # 第几页, 默认第一页
    per_page = request.args.get('per_page', '10')  # 一页有多少个

    # 2.校验参数
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 3.查询数据
    filters = []  # 查询的不是最新的数据
    if cid != 1:
        # 需要添加条件
        filters.append(News.category_id == cid)
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
        db_list = paginate.items  # 每一页的模型列表
        total_page = paginate.pages  # 当前总页数
        current_page = paginate.page  # 当前页的页数
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据错误")

    # 4.将模型对象进行解析放入列表
    news_dict_li = []
    for news in db_list:
        news_dict_li.append(news.to_basic_dict())

    # 5.准备数据
    data = {
        "total_page": total_page,
        "current_page": current_page,
        "news_dict_li": news_dict_li
    }
    # 6.返回响应和数据
    return jsonify(errno=RET.OK, errmsg="OK", data=data)
