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


@admin_blue.route('/index')
@user_login_data
def admin_index():
    """后台主页"""
    user = g.user
    return render_template('admin/index.html', user=user.to_dict())
