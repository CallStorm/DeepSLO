-- MySQL初始化脚本
-- 创建deepslo数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS deepslo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建deepslo用户（如果不存在）
CREATE USER IF NOT EXISTS 'deepslo'@'%' IDENTIFIED BY 'deepslo';

-- 授予权限
GRANT ALL PRIVILEGES ON deepslo.* TO 'deepslo'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 使用deepslo数据库
USE deepslo;

