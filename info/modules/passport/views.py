from flask import request, abort, current_app, make_response
from info.utils.captcha.captcha import captcha
from info import redis_db, constants
from . import passport_blue


@passport_blue.route('/image_code')
def get_image_code():
    """生成图片验证码并返回"""
    # 1:取到参数
    # args:取到url中?后面的参数
    code_id = request.args.get("imageCodeId", None)
    # 2:判断值
    if not code_id:
        return abort(403)
    # 3.生成图片验证码
    name, text, image = captcha.generate_captcha()
    # 4.保存图片验证码到redis数据库
    try:
        redis_db.set("ImageCodeId_"+code_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
    # 5.返回图片验证码
    response = make_response(image)
    response.headers["Content-Type"] = "image/jpg"
    return response
