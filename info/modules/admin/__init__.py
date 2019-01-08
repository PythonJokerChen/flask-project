from flask import Blueprint, session, request, url_for, redirect

admin_blue = Blueprint("admin", __name__, url_prefix='/admin')

from . import views


@admin_blue.before_request
def before_request():
    # 如果不是管理员就跳转到主页
    is_admin = session.get("is_admin", False)
    # 如果访问的url不是登录页面也跳转到主页
    url = request.url.endswith(url_for("admin.admin_login"))
    if not is_admin and not url:
        return redirect("/")