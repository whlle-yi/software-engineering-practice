-- PiAgent 排课系统 · MySQL 8.0 建库脚本（概要设计表 5-1~5-3）
-- 用法：mysql -uroot -p < db/schema.sql
CREATE DATABASE IF NOT EXISTS course_scheduling DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'course'@'localhost' IDENTIFIED BY 'course123';
GRANT ALL PRIVILEGES ON course_scheduling.* TO 'course'@'localhost';
FLUSH PRIVILEGES;
-- 表结构由 SQLAlchemy models.py 自动创建（flask init-db / app 启动时 create_all），
-- 本脚本仅负责数据库、字符集与账号；列约束的权威定义见 backend/models.py。
