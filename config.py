import logging
import redis


class Config:
    """工程配置信息"""
    SECRET_KEY = "EjpNVSNQTyGi1VvWECj9TvC/+kq3oujee2kTfQUs8yCM6xX9Yjq52v54g+HVoknA"

    # mySQL数据库的配置信息
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/news"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis数据库的配置信息
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = "6379"

    # Session的配置信息
    SESSION_TYPE = "redis"  # 将session保存到redis中
    SESSION_USE_SIGNER = True  # 让cookie中的session_id被加密处理
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)  # 使用 redis 的实例
    SESSION_PERMANENT = False  # 设置session需要过期
    PERMANENT_SESSION_LIFETIME = 86400  # 设置session的有效时限

    # 默认的日志等级, 在开发模式下使用DEBUG等级记录所有产生的事件
    LOG_LEVEL = logging.DEBUG
    num =1

class DevelopmentConfig(Config):
    """开发模式下的配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产模式下的配置"""
    # 在生产模式下只记录发成的错误, 减少I/O操作提升服务器性能
    LOG_LEVEL = logging.ERROR


# 配置字典, 通过此字典给__init__.py文件传入不同的配置信息
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig
}
