from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from info import constants
from . import mysql_db


class BaseModel(object):
    """模型基类，为每个模型补充创建时间与更新时间"""
    create_time = mysql_db.Column(mysql_db.DateTime, default=datetime.now)  # 记录的创建时间
    update_time = mysql_db.Column(mysql_db.DateTime, default=datetime.now, onupdate=datetime.now)  # 记录的更新时间


# 用户收藏表，建立用户与其收藏新闻多对多的关系
tb_user_collection = mysql_db.Table(
    "info_user_collection",
    mysql_db.Column("user_id", mysql_db.Integer, mysql_db.ForeignKey("info_user.id"), primary_key=True),  # 新闻编号
    mysql_db.Column("news_id", mysql_db.Integer, mysql_db.ForeignKey("info_news.id"), primary_key=True),  # 分类编号
    mysql_db.Column("create_time", mysql_db.DateTime, default=datetime.now)  # 收藏创建时间
)

tb_user_follows = mysql_db.Table(
    "info_user_fans",
    mysql_db.Column('follower_id', mysql_db.Integer, mysql_db.ForeignKey('info_user.id'), primary_key=True),  # 粉丝id
    mysql_db.Column('followed_id', mysql_db.Integer, mysql_db.ForeignKey('info_user.id'), primary_key=True)  # 被关注人的id
)


class User(BaseModel, mysql_db.Model):
    """用户"""
    __tablename__ = "info_user"

    id = mysql_db.Column(mysql_db.Integer, primary_key=True)  # 用户编号
    nick_name = mysql_db.Column(mysql_db.String(32), unique=True, nullable=False)  # 用户昵称
    password_hash = mysql_db.Column(mysql_db.String(128), nullable=False)  # 加密的密码
    mobile = mysql_db.Column(mysql_db.String(11), unique=True, nullable=False)  # 手机号
    avatar_url = mysql_db.Column(mysql_db.String(256))  # 用户头像路径
    last_login = mysql_db.Column(mysql_db.DateTime, default=datetime.now)  # 最后一次登录时间
    is_admin = mysql_db.Column(mysql_db.Boolean, default=False)
    signature = mysql_db.Column(mysql_db.String(512))  # 用户签名
    gender = mysql_db.Column(  # 订单的状态
        mysql_db.Enum(
            "MAN",  # 男
            "WOMAN"  # 女
        ),
        default="MAN")

    # 当前用户收藏的所有新闻
    collection_news = mysql_db.relationship("News", secondary=tb_user_collection, lazy="dynamic")  # 用户收藏的新闻
    # 用户所有的粉丝，添加了反向引用followed，代表用户都关注了哪些人
    followers = mysql_db.relationship('User',
                                      secondary=tb_user_follows,
                                      primaryjoin=id == tb_user_follows.c.followed_id,
                                      secondaryjoin=id == tb_user_follows.c.follower_id,
                                      backref=mysql_db.backref('followed', lazy='dynamic'),
                                      lazy='dynamic')

    @property
    def password(self):
        raise AttributeError("当前属性不允许读取")

    @password.setter
    def password(self, value):
        """对密码进行hash加密"""
        self.password_hash = generate_password_hash(value)

    def check_password(self, password):
        """校验密码"""
        return check_password_hash(self.password_hash, password)

    # 当前用户所发布的新闻
    news_list = mysql_db.relationship('News', backref='user', lazy='dynamic')

    def to_dict(self):
        resp_dict = {
            "id": self.id,
            "nick_name": self.nick_name,
            "avatar_url": constants.QINIU_DOMIN_PREFIX + self.avatar_url if self.avatar_url else "",
            "mobile": self.mobile,
            "gender": self.gender if self.gender else "MAN",
            "signature": self.signature if self.signature else "",
            "followers_count": self.followers.count(),
            "news_count": self.news_list.count()
        }
        return resp_dict

    def to_admin_dict(self):
        resp_dict = {
            "id": self.id,
            "nick_name": self.nick_name,
            "mobile": self.mobile,
            "register": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": self.last_login.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return resp_dict


class News(BaseModel, mysql_db.Model):
    """新闻"""
    __tablename__ = "info_news"

    id = mysql_db.Column(mysql_db.Integer, primary_key=True)  # 新闻编号
    title = mysql_db.Column(mysql_db.String(256), nullable=False)  # 新闻标题
    source = mysql_db.Column(mysql_db.String(64), nullable=False)  # 新闻来源
    digest = mysql_db.Column(mysql_db.String(512), nullable=False)  # 新闻摘要
    content = mysql_db.Column(mysql_db.Text, nullable=False)  # 新闻内容
    clicks = mysql_db.Column(mysql_db.Integer, default=0)  # 浏览量
    index_image_url = mysql_db.Column(mysql_db.String(256))  # 新闻列表图片路径
    category_id = mysql_db.Column(mysql_db.Integer, mysql_db.ForeignKey("info_category.id"))
    user_id = mysql_db.Column(mysql_db.Integer, mysql_db.ForeignKey("info_user.id"))  # 当前新闻的作者id
    status = mysql_db.Column(mysql_db.Integer, default=0)  # 当前新闻状态 如果为0代表审核通过，1代表审核中，-1代表审核不通过
    reason = mysql_db.Column(mysql_db.String(256))  # 未通过原因，status = -1 的时候使用
    # 当前新闻的所有评论
    comments = mysql_db.relationship("Comment", lazy="dynamic")

    def to_review_dict(self):
        resp_dict = {
            "id": self.id,
            "title": self.title,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": self.status,
            "reason": self.reason if self.reason else ""
        }
        return resp_dict

    def to_basic_dict(self):
        resp_dict = {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "digest": self.digest,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "index_image_url": self.index_image_url,
            "clicks": self.clicks,
        }
        return resp_dict

    def to_dict(self):
        resp_dict = {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "digest": self.digest,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "content": self.content,
            "comments_count": self.comments.count(),
            "clicks": self.clicks,
            "category": self.category.to_dict(),
            "index_image_url": self.index_image_url,
            "author": self.user.to_dict() if self.user else None
        }
        return resp_dict


class Comment(BaseModel, mysql_db.Model):
    """评论"""
    __tablename__ = "info_comment"

    id = mysql_db.Column(mysql_db.Integer, primary_key=True)  # 评论编号
    user_id = mysql_db.Column(mysql_db.Integer, mysql_db.ForeignKey("info_user.id"), nullable=False)  # 用户id
    news_id = mysql_db.Column(mysql_db.Integer, mysql_db.ForeignKey("info_news.id"), nullable=False)  # 新闻id
    content = mysql_db.Column(mysql_db.Text, nullable=False)  # 评论内容
    parent_id = mysql_db.Column(mysql_db.Integer, mysql_db.ForeignKey("info_comment.id"))  # 父评论id
    parent = mysql_db.relationship("Comment", remote_side=[id])  # 自关联
    like_count = mysql_db.Column(mysql_db.Integer, default=0)  # 点赞条数

    def to_dict(self):
        resp_dict = {
            "id": self.id,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "content": self.content,
            "parent": self.parent.to_dict() if self.parent else None,
            "user": User.query.get(self.user_id).to_dict(),
            "news_id": self.news_id,
            "like_count": self.like_count
        }
        return resp_dict


class CommentLike(BaseModel, mysql_db.Model):
    """评论点赞"""
    __tablename__ = "info_comment_like"
    comment_id = mysql_db.Column("comment_id", mysql_db.Integer, mysql_db.ForeignKey("info_comment.id"),
                                 primary_key=True)  # 评论编号
    user_id = mysql_db.Column("user_id", mysql_db.Integer, mysql_db.ForeignKey("info_user.id"),
                              primary_key=True)  # 用户编号


class Category(BaseModel, mysql_db.Model):
    """新闻分类"""
    __tablename__ = "info_category"

    id = mysql_db.Column(mysql_db.Integer, primary_key=True)  # 分类编号
    name = mysql_db.Column(mysql_db.String(64), nullable=False)  # 分类名
    news_list = mysql_db.relationship('News', backref='category', lazy='dynamic')

    def to_dict(self):
        resp_dict = {
            "id": self.id,
            "name": self.name
        }
        return resp_dict
