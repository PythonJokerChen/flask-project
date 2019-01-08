from flask import render_template, g, current_app, abort, request, jsonify
from info import constants, mysql_db
from info.models import News, Comment, CommentLike, User
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import news_blue


@news_blue.route("/<int:news_id>")
@user_login_data
def news_detail(news_id):
    """显示首页"""
    # 查询新闻点击量数据
    user = g.user
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        abort(404)
    click_list = []
    if news_list:
        for news in news_list:
            click_list.append(news.to_basic_dict())

    # 查询新闻数据
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        abort(404)

    if not news:
        abort(404)

    # 更新新闻的点击次数
    news.clicks += 1

    # 判断是否收藏新闻
    is_collected = False
    # 判断收否关注作者
    is_followed = False
    if g.user:
        if news in user.collection_news:
            is_collected = True
        if news.user in user.followers:
            is_followed = True

    # 查询评论数据
    comments = []
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)

    comment_like_ids = []
    if user:
        try:
            # 查询当前用户在当前新闻里面点赞了哪些评论
            # 1.查询当前新闻的所有评论, 取到所有的评论id
            comment_ids = [comment.id for comment in comments]
            # 2.查询当前评论中哪些评论被当前用户点赞
            comment_likes = CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids),
                                                     CommentLike.user_id == g.user.id).all()
            # 3.取到所有被点赞的评论id
            comment_like_ids = [comments_like.comment_id for comments_like in comment_likes]

        except Exception as e:
            current_app.logger.error(e)

    comment_dict_li = []
    for comment in comments:
        # 代表默认没有点赞
        comment_dict = comment.to_dict()
        comment_dict["is_like"] = False
        # 判断当前遍历到的评论是否在取到的被点赞评论id列表内, 如果在就显示为点赞
        if comment.id in comment_like_ids:
            comment_dict["is_like"] = True
        comment_dict_li.append(comment_dict)

    # 准备数据字典
    data = {
        "user_info": user.to_dict() if user else None,
        "click_list": click_list,
        "news": news.to_dict(),
        "is_collected": is_collected,
        "is_followed": is_followed,
        "comments": comment_dict_li
    }
    return render_template("news/detail.html", data=data)


@news_blue.route('/news_collect', methods=["POST"])
@user_login_data
def collected_news():
    """收藏新闻"""
    if not g.user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    # 1.接收参数
    news_id = request.json.get('news_id')
    action = request.json.get('action')

    # 2.校验参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ["collect", "cancel_collect"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3.查询新闻
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询错误")

    # 4.判断是否存在
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

    # 5.收藏以及取消收藏
    if action == "cancel_collect":
        # 取消收藏
        if news in g.user.collection_news:
            g.user.collection_news.remove(news)
    else:
        # 进行收藏
        if news not in g.user.collection_news:
            g.user.collection_news.append(news)

    # 6.返回响应
    return jsonify(errno=RET.OK, errmsg="收藏成功")


@news_blue.route('/news_comment', methods=["POST"])
@user_login_data
def comment_news():
    """评论新闻"""
    # 1.判断用户是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 2.获取参数
    news_id = request.json.get("news_id")
    comment_content = request.json.get("comment")
    parent_id = request.json.get("parent_id")

    # 3.校验参数
    if not all([news_id, comment_content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    try:
        news_id = int(news_id)
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 查询新闻是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询错误")
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

    # 4.初始化模型, 添加评论到数据库
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = comment_content
    if parent_id:
        comment.parent_id = parent_id
    # 添加数据到数据库
    try:
        mysql_db.session.add(comment)
        mysql_db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        mysql_db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据存储错误")

    # 5.返回响应
    return jsonify(errno=RET.OK, errmsg="OK", data=comment.to_dict())


@news_blue.route("/comment_like", methods=["POST"])
@user_login_data
def comment_like():
    """评论点赞"""
    # 1.判断用户是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 2.获取参数
    comment_id = request.json.get("comment_id")
    action = request.json.get("action")

    # 3.校验参数
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ["add", "remove"]:
        return jsonify(errno=RET.PARAMERR, errmsg=" 参数错误")

    try:
        comment_id = int(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 4.从数据库取出点赞的数据
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询错误")

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论不存在")

    # 5.根据action的参数选择点赞或者取消
    comment_likes = CommentLike.query.filter(CommentLike.user_id == user.id,
                                             CommentLike.comment_id == comment_id).first()

    if action == "add":
        # 点赞
        if not comment_likes:
            comment_likes = CommentLike()
            comment_likes.user_id = user.id
            comment_likes.comment_id = comment_id
            mysql_db.session.add(comment_likes)
            comment.like_count += 1
    else:
        # 取消赞
        if comment_likes:
            mysql_db.session.delete(comment_likes)
            comment.like_count -= 1
    try:
        mysql_db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        mysql_db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据存储错误")

    # 6.返回响应
    return jsonify(errno=RET.OK, errmsg="OK")


@news_blue.route("/followed_user", methods=["POST"])
@user_login_data
def followed_user():
    """关注与取消关注"""
    if not g.user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    # 1.获取参数
    user_id = request.json.get("user_id")
    action = request.json.get("action")

    # 2.校验参数
    if not all([user_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ("follow", "unfollow"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3.查询用户相关信息
    try:
        target_user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询失败")

    if not target_user:
        return jsonify(errno=RET.NODATA, errmsg="未查询到用户信息")

    # 4.关注和取消关注的相关逻辑
    if action == "follow":
        if target_user.followers.filter(User.id == g.user.id).count() > 0:
            return jsonify(errno=RET.DATAEXIST, errmsg="当前已关注")
        target_user.followers.append(g.user)
    else:
        if target_user.followers.filter(User.id == g.user.id).count() > 0:
            target_user.followers.remove(g.user)

    # 5.保存数据到数据库
    try:
        mysql_db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存失败")

    # 6.返回响应
    return jsonify(errno=RET.OK, errmsg="操作成功")