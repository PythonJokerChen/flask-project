from flask_migrate import Migrate, MigrateCommand
from info import app_factory, mysql_db
from flask_script import Manager

# 通过配置工厂创建app, 并可以选择传入development/production/testing
app = app_factory('development')

# Flask_Script
manager = Manager(app)
# 数据库迁移
Migrate(app, mysql_db)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
