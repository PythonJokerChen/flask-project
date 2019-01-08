from flask_migrate import Migrate, MigrateCommand
from info import app_factory, mysql_db, models
from flask_script import Manager

# 通过配置工厂创建app, 并可以选择传入development/production/testing
from info.models import User

app = app_factory('development')

# Flask_Script
manager = Manager(app)
# 数据库迁移
Migrate(app, mysql_db)
manager.add_command('db', MigrateCommand)


# 创建管理员账户
@manager.option('-n', '-name', dest='name')
@manager.option('-p', '-password', dest='password')
def createsuperuser(name, password):
    """创建管理员用户"""
    if not all([name, password]):
        print('参数不足')
        return

    user = User()
    user.mobile = name
    user.nick_name = name
    user.password = password
    user.is_admin = True

    try:
        mysql_db.session.add(user)
        mysql_db.session.commit()
        print("创建成功")
    except Exception as e:
        print(e)
        mysql_db.session.rollback()


if __name__ == '__main__':
    manager.run()
