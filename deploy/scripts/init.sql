-- EasySync 数据库初始化脚本

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 创建数据库（如果不存在）
-- 注意：数据库由docker-compose的环境变量自动创建，这里不需要再创建

-- 创建用户和授权
CREATE USER IF NOT EXISTS 'easysync'@'%' IDENTIFIED BY 'EasySyncUser2025!';
GRANT ALL PRIVILEGES ON easysync.* TO 'easysync'@'%';
FLUSH PRIVILEGES;

SET FOREIGN_KEY_CHECKS = 1;