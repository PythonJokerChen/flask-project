from flask import request, abort, current_app, make_response, jsonify, json
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from info.libs.yuntongxun.sms import CCP
from info import redis_db, constants
from . import passport_blue
import random
import re


@passport_blue.route('/image_code')
def get_image_code():
    """生成图片验证码并返回"""
    # 1:取到参数
    # args:取到url中?后面的参数
    img_code_id = request.args.get("imageCodeId", None)
    # 2:判断值
    if not img_code_id:
        return abort(403)
    # 3.生成图片验证码
    name, text, image = captcha.generate_captcha()
    # 4.保存图片验证码到redis数据库
    try:
        redis_db.set("ImageCodeId_" + img_code_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        # 如果操作失败, 将错误信息保存到日志里面
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询错误")
    # 5.返回图片验证码
    response = make_response(image)
    response.headers["Content-Type"] = "image/jpg"
    return response


@passport_blue.route('/sms_code', methods=['POST'])
def register():
    """
    1. 接收参数并判断是否有值
    2. 校验手机号是正确
    3. 通过传入的图片编码去redis中查询真实的图片验证码内容
    4. 进行验证码内容的比对
    5. 生成发送短信的内容并发送短信
    6. redis中保存短信验证码内容
    7. 返回发送成功的响应
    :return:
    """
    # 1. 接收参数并判断是否有值
    params_dict = request.json
    mobile = params_dict.get('mobile')  # 手机号
    image_code = params_dict.get('image_code')  # 用户输入的图片验证码信息
    image_code_id = params_dict.get('image_code_id')  # 真实图片验证码编号
    print(mobile, image_code, image_code_id)
    # 1.1 校验参数
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")
    # 2. 校验手机号码
    phone_num = re.match("^1[3578][0-9]{9}$", mobile)
    if not phone_num:
        return jsonify(errno=RET.DATAERR, errmsg='手机号错误')
    # 3. 通过传入的图片编码去redis中查询真实的图片验证码内容
    try:
        real_img_code = redis_db.get("ImageCodeId_" + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取图片验证码失败')
    # 3.1 判断验证码是否存在, 是否过期
    if not real_img_code:
        return jsonify(errno=RET.DBERR, errmsg='验证码已过期')
    # 4. 进行验证码内容的比对, 需要将双方数据处理到同一格式再进行比较
    if image_code.upper() != real_img_code.decode('utf-8').upper():
        return jsonify(errno=RET.DATAERR, errmsg='验证码输入错误')
    # 5. 生成发送短信的内容并发送短信
    random_num = random.randint(0, 999999)
    sms_code = "%06d" % random_num
    current_app.logger.debug("短信验证码的内容：%s" % sms_code)
    result = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], "1")
    print(result)
    if result != 0:
        # 发送短信失败
        return jsonify(errno=RET.THIRDERR, errmsg="发送短信失败")
    print(random_num)
    # 6. redis中保存短信验证码内容
    try:
        redis_db.set("SMS_" + mobile, sms_code, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='存储短信验证码失败')
    # 7. 返回发送短信成功的响应
    return jsonify(errno=RET.OK, errmsg="发送成功")