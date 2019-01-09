import time
from datetime import datetime, timedelta

from flask import render_template, request, current_app, session, redirect, url_for, g

from info.models import User
from info.utils.common import user_login_data
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
    # 1.获取参数
    # 总人数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
    # 月新增数
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
    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
    }

    # 查询今天的时间
    today_date_str = ("%d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday))
    # 转成时间对象
    today_date = datetime.strptime(today_date_str, "%Y-%m-%d")
    active_date = []
    active_count = []
    for i in range(0, 31):
        # 取到某一天的0点0分
        begin_date = today_date - timedelta(days=i)
        # 取到下一天的0点0分
        end_date = today_date - timedelta(days=(i - 1))
        active_date.append(begin_date.strftime('%Y-%m-%d'))
        # 日新增数
        data_count = 0

    return render_template("admin/user_count.html", data=data)
