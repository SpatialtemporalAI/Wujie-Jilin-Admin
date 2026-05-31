# 多租户权限与表隔离分级设计

- **日期**: 2026-05-31
- **状态**: 已确认
- **类型**: 架构决策

## 需求描述

扩展多租户插件的 tenant_id 覆盖范围，明确各表的隔离模式和权限分级。

## 表分类

### 严格租户隔离（strict）

查询只返回当前租户数据，`tenant_id == current_tenant_id`。

| 表 | 说明 |
|---|------|
| sys_role | 角色按租户隔离 |
| sys_config | 配置按租户隔离 |
| sys_dict | 字典定义按租户隔离 |
| sys_dict_item | 字典项按租户隔离 |
| sys_file | 文件按租户隔离 |
| app_user | 业务用户按租户隔离 |
| sys_operation_log | 操作日志按租户隔离 |
| sys_login_log | 登录日志按租户隔离 |

### 可选租户隔离（optional）

查询返回当前租户 + 全局数据（`tenant_id IS NULL` 为全局）。

| 表 | 说明 |
|---|------|
| sys_menu | 全局菜单 + 租户可定制菜单 |
| sys_notice | 系统公告（全局）+ 租户通知 |

### 纯全局（不隔离）

不加 tenant_id，所有租户共享。

| 表 | 说明 |
|---|------|
| sys_user | 用户身份全局唯一 |
| sys_ip_blacklist | 安全策略全局统一 |

## 权限分级

### 超级管理员（平台级，is_superuser=true）

- 全量读写所有表，不受租户过滤限制
- 可管理租户、分配用户

### 租户管理员（tenant role: owner/admin）

- 读写本租户的 strict 表数据
- 管理（增删改）本租户的 optional 表数据
- **只读**本租户的 SysOperationLog、SysLoginLog（不可删除/篡改）
- **只读**全局的 SysIpBlacklist（不可修改安全规则）

### 普通租户用户（tenant role: member）

- 使用本租户的功能和数据
- 不可见 SysOperationLog、SysLoginLog、SysIpBlacklist

## 过滤机制

- **strict**：`with_loader_criteria` 添加 `tenant_id == current_tenant_id`
- **optional**：`with_loader_criteria` 添加 `tenant_id == current_tenant_id OR tenant_id IS NULL`
- **全局**：不过滤
- 超级管理员通过 `ignore_tenant=True` 跳过过滤
