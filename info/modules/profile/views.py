from flask import render_template, g, redirect, request, jsonify

from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import profile_blue


@profile_blue.route('/base_info', methods=["GET", "POST"])
@user_login_data
def base_info():
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


@profile_blue.route('/info')
@user_login_data
def user_info():
    user = g.user

    # 如果用户没有登录则重定向到首页
    if not user:
        return redirect("/")

    data = {
        "user_info": user.to_dict()
    }

    return render_template('news/user.html', data=data)
