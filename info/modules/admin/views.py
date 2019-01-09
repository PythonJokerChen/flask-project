import time
from datetime import datetime, timedelta

from flask import render_template, request, current_app, session, redirect, url_for, g, jsonify

from info import constants, mysql_db
from info.models import User, News, Category
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import admin_blue


@admin_blue.route('/login', methods=['POST', 'GET'])
def admin_login():
    """后台页面登录"""
    if request.method == "GET":
        # 判断当前是否登录, 如果登录直接跳转到主页
        user_id = session.get("user_id", None)
        is_admin = session.get("is_admin", False)
        if user_id and is_admin:
            return redirect(url_for('admin.admin_index'))

        return render_template('admin/login.html')

    # 1.获取参数
    username = request.form.get("username")
    password = request.form.get("password")

    # 2.校验参数
    if not all([username, password]):
        return render_template('admin/login.html', errmsg="参数不足")

    # 3.与数据库内的信息进行对比
    try:
        user = User.query.filter(User.mobile == username, User.is_admin).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html', errmsg="权限不足")

    if not user:
        return render_template('admin/login.html', errmsg="未查询到用户信息")

    if not user.check_password(password):
        return render_template('admin/login.html', errmsg="密码错误")

    # 4.保存用户的登录信息
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    session["is_admin"] = True

    # 5.跳转到后台管理主页
    return redirect(url_for('admin.admin_index'))


@admin_blue.route('/index', methods=['POST', 'GET'])
@user_login_data
def admin_index():
    """后台主页"""
    user = g.user
    return render_template('admin/index.html', user=user.to_dict())


@admin_blue.route("/user_count")
def user_count():
    """用户统计"""
    # 1.获取参数
    # 总人数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)

    # 查询月新增数
    mon_count = 0
    t = time.localtime()
    begin_mon_date = datetime.strptime("%d-%02d-01" % (t.tm_year, t.tm_mon), "%Y-%m-%d")
    try:
        mon_count = User.query.filter(User.is_admin == False, User.create_time > begin_mon_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 查询日新增数
    day_count = 0
    begin_day_date = datetime.strptime("%d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday), "%Y-%m-%d")
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time > begin_day_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 折线图数据
    active_date = []
    active_count = []

    # 查询今天的时间
    begin_today_date = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')

    for i in range(0, 31):
        begin_date = begin_today_date - timedelta(days=i)
        end_date = begin_today_date - timedelta(days=(i - 1))

        count = User.query.filter(User.is_admin == False, User.last_login >= begin_date,
                                  User.last_login <= end_date).count()

        active_count.append(count)
        active_date.append(begin_date.strftime('%Y-%m-%d'))

        active_date.sort()
        active_count.reverse()

    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_count": active_count,
        "active_date": active_date
    }

    return render_template("admin/user_count.html", data=data)


@admin_blue.route('/user_list')
def user_list():
    """用户列表"""
    # 获取参数
    page = request.args.get("p", 1)

    # 校验参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 定义参数默认值
    users = []
    current_page = 1
    total_page = 1

    # 查询数据
    try:
        paginate = User.query.filter(User.is_admin == False). \
            order_by(User.last_login.desc()).paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT)
        users = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    # 将模型列表转换为字典列表
    users_list = []
    for user in users:
        users_list.append(user.to_admin_dict())

    # 返回数据
    data = {
        "total_page": total_page,
        "current_page": current_page,
        "users": users_list,
    }
    return render_template("admin/user_list.html", data=data)


@admin_blue.route("/news_review")
def news_review():
    """新闻审核, 搜索"""
    # 获取参数
    page = request.args.get("p", 1)
    kwarg = request.args.get("kwarg", "")

    # 校验参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 定义参数默认值
    news = []
    current_page = 1
    total_page = 1
    filters = [News.status != 0]
    # 如果关键字存在, 就添加关键字搜索
    if kwarg:
        filters.append(News.title.contains(kwarg))
    # 查询数据
    try:
        paginate = News.query.filter(*filters). \
            order_by(News.create_time.desc()).paginate(page, constants.ADMIN_NEWS_PAGE_MAX_COUNT)
        news = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    # 将模型列表转换为字典列表
    news_list = []
    for new in news:
        news_list.append(new.to_review_dict())

    # 准备数据
    data = {
        "news_list": news_list,
        "current_page": current_page,
        "total_page": total_page,
    }

    return render_template("admin/news_review.html", data=data)


@admin_blue.route('/news_review_detail', methods=["POST", "GET"])
def news_review_detail():
    """新闻审核"""
    if request.method == "GET":
        # 获取新闻id
        news_id = request.args.get("news_id")
        if not news_id:
            return render_template('admin/news_review_detail.html', data={"errmsg": "未查询到此新闻"})

        # 通过id查询新闻
        news = None
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)

        if not news:
            return render_template('admin/news_review_detail.html', data={"errmsg": "未查询到此新闻"})

        # 返回数据
        data = {"news": news.to_dict()}
        return render_template('admin/news_review_detail.html', data=data)

    # 代码执行到此说明要对内容进行审核操作
    # 获取参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    # 校验参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 查询新闻
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到数据")

    # 根据action的值进行相应操作
    if action == "accept":
        news.status = 0
    else:
        # 代表没有通过审核, 需要说明原因
        reason = request.json.get("reason")
        if not reason:
            return jsonify(errno=RET.NODATA, errmsg="请说明拒绝原因")
        news.status = -1

    # 提交数据到数据库
    try:
        mysql_db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        mysql_db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据保存失败")

    # 返回数据
    return jsonify(errno=RET.OK, errmsg="操作成功")


@admin_blue.route("/news_edit")
def news_edit():
    """新闻版式编辑"""
    # 获取参数
    page = request.args.get("p", 1)
    kwarg = request.args.get("kwarg", "")

    # 校验参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 定义参数默认值
    news = []
    current_page = 1
    total_page = 1
    filters = [News.status == 0]
    # 如果关键字存在, 就添加关键字搜索
    if kwarg:
        filters.append(News.title.contains(kwarg))
    # 查询数据
    try:
        paginate = News.query.filter(*filters). \
            order_by(News.create_time.desc()).paginate(page, constants.ADMIN_NEWS_PAGE_MAX_COUNT)
        news = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    # 将模型列表转换为字典列表
    news_list = []
    for new in news:
        news_list.append(new.to_review_dict())

    # 准备数据
    data = {
        "news_list": news_list,
        "current_page": current_page,
        "total_page": total_page,
    }

    return render_template("admin/news_edit.html", data=data)


@admin_blue.route('/news_edit_detail', methods=["POST", "GET"])
def news_edit_detail():
    """新闻编辑详情"""
    if request.method == "GET":
        # 获取参数
        news_id = request.args.get("news_id")

        # 校验参数
        if not news_id:
            return render_template('admin/news_edit_detail.html', data={"errmsg": "未查询到此新闻"})

        # 查询新闻
        news = None
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)

        if not news:
            return render_template('admin/news_edit_detail.html', data={"errmsg": "未查询到此新闻"})

        # 查询新闻的分类
        categories = None
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)

        if not categories:
            return render_template('admin/news_edit_detail.html', data={"errmsg": "未查询到此新闻"})

        # 将模型转换成字典列表
        categories_li = []
        for category in categories:
            categories_li.append(category.to_dict())

        # 移除 "最新" 分类
        categories_li.pop(0)
        # 渲染模板
        data = {
            "news": news.to_dict(),
            "categories": categories_li
        }
        return render_template("admin/news_edit_detail.html", data=data)

    # 代码执行至此说明为编辑操作
    # 获取参数
    news_id = request.form.get("news_id")  # 新闻id
    title = request.form.get("title")  # 标题
    digest = request.form.get("digest")  # 摘要
    content = request.form.get("content")  # 内容
    index_image = request.files.get("index_image")  # 索引图片
    category_id = request.form.get("category_id")  # 分类

    # 判断数据是否有值
    if not all([title, digest, content, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    # 根据新闻id查询新闻
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

    # 读取图片内容
    if index_image:
        try:
            index_image = index_image.read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

        # 将图片上传七牛云
        try:
            key = storage(index_image)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + key

    # 提交到数据库
    news.title = title
    news.digest = digest
    news.content = content
    news.category_id = category_id

    try:
        mysql_db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        mysql_db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    # 返回结果
    return jsonify(errno=RET.OK, errmsg="编辑成功")


@admin_blue.route("/news_type")
def news_type():
    """获取所有分类"""
    # 获取参数
    categories = Category.query.all()

    # 定义列表保存分类数据
    categories_dicts = []
    for category in categories:
        # 获取字典
        cate_dict = category.to_dict()
        # 拼接内容
        categories_dicts.append(cate_dict)
    # 删除 "最新" 分类
    categories_dicts.pop(0)
    return render_template('admin/news_type.html', data={"categories": categories_dicts})


@admin_blue.route('/add_category', methods=["POST"])
def add_category():
    """修改或者添加分类"""
    # 获取参数
    category_id = request.json.get("id")
    category_name = request.json.get("name")

    # 校验参数
    if not category_name:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    if category_id:
        # 根据id查询数据库
        try:
            category = Category.query.get(category_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

        if not category:
            return jsonify(errno=RET.NODATA, errmsg="未查询到分类信息")

        # 添加数据到数据库
        category.name = category_name

    else:
        # 没有分类id, 说明是添加分类
        category = Category()
        category.name = category_name
        mysql_db.session.add(category)

    try:
        mysql_db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        mysql_db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    return jsonify(errno=RET.OK, errmsg="保存数据成功")


@admin_blue.route('/logout', methods=["POST"])
def logout():
    """
    登出
    清除session中的对应登录之后保存的信息
    :return:
    """
    session.pop("user_id", None)
    session.pop("nick_name", None)
    session.pop("mobile", None)
    session.pop("is_admin", None)
    return jsonify(errno=RET.OK, errmsg="登出成功")
