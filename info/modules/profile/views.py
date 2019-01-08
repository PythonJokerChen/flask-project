from flask import render_template, g, redirect, request, jsonify, current_app

from info import constants
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import profile_blue


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
