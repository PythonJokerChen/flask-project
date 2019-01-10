from flask import render_template, g, redirect, request, jsonify, current_app, abort

from info import constants, mysql_db
from info.models import Category, News, User
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import profile_blue


@profile_blue.route('/info')
@user_login_data
def user_info():
    """用户中心主页面"""
    user = g.user

    # 如果用户没有登录则重定向到首页
    if not user:
        return redirect("/")

    data = {
        "user_info": user.to_dict()
    }

    return render_template('news/user.html', data=data)


@profile_blue.route('/base_info', methods=["GET", "POST"])
@user_login_data
def base_info():
    """修改个人信息"""
    if request.method == "GET":
        # 代表显示页面
        return render_template('news/user_base_info.html', data={"user_info": g.user.to_dict()})
    # 代表修改用户数据
    # 1.获取参数
    nick_name = request.json.get("nick_name")
    signature = request.json.get("signature")
    gender = request.json.get("gender")

    # 2.校验参数
    if not all([nick_name, signature, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if gender not in ["MAN", "WOMAN"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3.更新user模型的数据
    user = g.user
    user.signature = signature
    user.gender = gender
    user.nick_name = nick_name

    return jsonify(errno=RET.OK, errmsg="修改成功")


@profile_blue.route('/pic_info', methods=["GET", "POST"])
@user_login_data
def pic_info():
    """上传头像"""
    if request.method == "GET":
        # 代表显示页面
        return render_template('news/user_pic_info.html', data={"user_info": g.user.to_dict()})

    # 1.取到上传的图片
    try:
        avatar = request.files.get("avatar").read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="请选择图片")

    # 2.通过七牛云上传头像
    try:
        key = storage(avatar)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传头像失败")

    # 3.保存头像地址到数据库
    g.user.avatar_url = key

    return jsonify(errno=RET.OK, errmsg="上传头像成功", data={'avatar_url': constants.QINIU_DOMIN_PREFIX + key})


@profile_blue.route('/pass_info', methods=["GET", "POST"])
@user_login_data
def pass_info():
    """修改密码"""
    if request.method == "GET":
        # 代表显示页面
        return render_template('news/user_pass_info.html', data={"user_info": g.user.to_dict()})

    # 1.获取到传入参数
    data_dict = request.json
    old_password = data_dict.get("old_password")
    new_password = data_dict.get("new_password")

    # 2.校验参数
    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    # 3.获取当前登录用户的信息
    user = g.user

    if not user.check_password(old_password):
        return jsonify(errno=RET.PWDERR, errmsg="原密码错误")

    # 4.更新数据
    user.password = new_password

    return jsonify(errno=RET.OK, errmsg="保存成功")


@profile_blue.route('/collection')
@user_login_data
def user_collection():
    """新闻收藏"""
    # 1.获取参数
    page = request.args.get("p", 1)

    # 2.判断参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3.查询用户指定页数的收藏新闻
    user = g.user
    paginate = user.collection_news.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
    current_page = paginate.page
    total_page = paginate.pages
    news_list = paginate.items

    news_dict_li = []
    for news in news_list:
        news_dict_li.append(news.to_basic_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "collections": news_dict_li
    }

    # 4.返回响应和数据
    return render_template('news/user_collection.html', data=data)


@profile_blue.route('/news_release', methods=["GET", "POST"])
@user_login_data
def news_release():
    """发布新闻"""
    if request.method == "GET":
        # 1.加载新闻分类数据
        categories = []
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)

        category_dict_li = []
        for category in categories:
            category_dict_li.append(category.to_dict())

        # 移除 "最新" 分类
        category_dict_li.pop(0)

        # 2.渲染模板
        return render_template('news/user_news_release.html', data={"categories": category_dict_li})

    # 1.获取参数
    title = request.form.get("title")  # 标题
    source = "个人发布"  # 新闻来源
    digest = request.form.get("digest")  # 摘要
    content = request.form.get("content")  # 新闻内容
    index_image = request.files.get("index_image")  # 索引图片
    category_id = request.form.get("category_id")  # 分类id

    # 2.校验参数
    if not all([title, source, digest, content, index_image, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    try:
        category_id = int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3.取到图片并上传到七牛云
    try:
        index_image_data = index_image.read()
        key = storage(index_image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")

    # 4.初始化新闻模型，并设置相关数据
    news = News()
    news.title = title
    news.digest = digest
    news.source = source
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
    news.category_id = category_id
    news.user_id = g.user.id
    # 1代表待审核状态
    news.status = 1
    # 将数据保存到数据库
    try:
        mysql_db.session.add(news)
        mysql_db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        mysql_db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    # 5. 返回结果
    return jsonify(errno=RET.OK, errmsg="发布成功，等待审核")


@profile_blue.route('/news_list')
@user_login_data
def user_news_list():
    """用户新闻列表"""
    # 1.获取页数
    p = request.args.get("p", 1)
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    # 2.查询当前用户发布的新闻
    user = g.user
    news_li = []
    current_page = 1
    total_page = 1
    try:
        paginate = News.query.filter(News.user_id == user.id).paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
        # 获取当前页数据
        news_li = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    # 3.准备数据
    news_dict_li = []
    for news_item in news_li:
        news_dict_li.append(news_item.to_review_dict())
    data = {
        "news_list": news_dict_li,
        "total_page": total_page,
        "current_page": current_page
    }

    # 4.渲染模板
    return render_template('news/user_news_list.html', data=data)


@profile_blue.route("/user_follow")
@user_login_data
def user_follow():
    # 获取参数
    user = g.user
    page = request.args.get("p", 1)

    # 校验参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 定义默认参数
    follows = []
    current_page = 1
    total_page = 1
    try:
        paginate = user.followed.paginate(page, constants.USER_FOLLOWED_MAX_COUNT, False)
        current_page = paginate.page
        total_page = paginate.pages
        follows = paginate.items
    except Exception as e:
        current_app.logger.error(e)

    # 将模型数据转换成字典列表
    user_dict_li = []
    for follower in follows:
        user_dict_li.append(follower.to_dict())

    data = {
        "users": user_dict_li,
        "total_page": total_page,
        "current_page": current_page,

    }
    return render_template("news/user_follow.html", data=data)


@profile_blue.route("/other_info")
@user_login_data
def other_info():
    """查看其他用户信息"""
    user = g.user
    # 获取其他用户的id
    user_id = request.args.get("id")
    if not user_id:
        abort(404)
    # 根据用户Id查找模型
    other = None
    try:
        other = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)

    if not other:
        abort(404)

    # 判断当前登录用户是否关注过该用户
    is_followed = False
    if user:
        try:
            if other.followers.filter(User.id == user.id).count():
                is_followed = True
        except Exception as e:
            current_app.logger.error(e)

    # 渲染模板
    data = {
        "user_info": user.to_dict(),
        "other_info": other.to_dict(),
        "is_followed": is_followed,
    }
    return render_template("news/other.html", data=data)


@profile_blue.route("/other_news_list")
@user_login_data
def other_news_list():
    # 获取页数
    page = request.args.get("p", 1)
    user = g.user

    # 校验参数
    if not all([page, user]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 定义默认数据
    news_li = []
    current_page = 1
    total_page = 1
    # 根据数据查询模型
    try:
        paginate = News.query.filter(News.user_id == user.id).paginate(page, constants.OTHER_NEWS_PAGE_MAX_COUNT, False)
        # 获取当前页数据
        news_li = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages

    except Exception as e:
        current_app.logger.error(e)

    # 将模型添加到字典列表
    news_dict_li = []

    for news_item in news_li:
        news_dict_li.append(news_item.to_review_dict())

    # 渲染模板
    data = {
        "news_list": news_dict_li,
        "current_page": current_page,
        "total_page": total_page,
    }

    return jsonify(errno=RET.OK, errmsg="OK", data=data)