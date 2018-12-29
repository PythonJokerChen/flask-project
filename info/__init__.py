from logging.handlers import RotatingFileHandler
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from config import config
from flask import Flask
import logging
import redis

mysql_db = SQLAlchemy()
redis_db = None


def log_factory(config_name):
    """通过此工厂函数判断当前的开发模式并配置相关日志"""
    # 设置当前日志的记录等级
    logging.basicConfig(level=config[config_name].LOG_LEVEL)
    # 创建日志记录器, 参数分别是保存路径, 日志文件大小, 文件个数上限
    log_file = RotatingFileHandler('logs/log', maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志的记录格式, 参数分别是日志等级, 文件名, 行数, 日志信息
    log_format = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 设置日志记录器的日志记录格式
    log_file.setFormatter(log_format)
    # 给全局的日志工具对象添加日志记录器
    logging.getLogger().addHandler(log_file)


def app_factory(config_name):
    """通过此工厂函数将传入的不同配置名字初始化对应配置的实例对象"""
    # 配置项目日志
    log_factory(config_name)
    app = Flask(__name__)
    # 设置session保护
    Session(app)
    # 开启csrf保护
    CSRFProtect(app)
    # 导入配置文件
    app.config.from_object(config[config_name])
    # 配置mysql
    mysql_db.init_app(app)
    # 配置redis
    redis_db = redis.StrictRedis(
        host=config[config_name].REDIS_HOST,
        port=config[config_name].REDIS_PORT
    )

    return app
