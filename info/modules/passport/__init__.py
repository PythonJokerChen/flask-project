# 登录注册的相关业务逻辑
from flask import Blueprint

passport_blue = Blueprint('passport', __name__, url_prefix='/passport')

from . import views