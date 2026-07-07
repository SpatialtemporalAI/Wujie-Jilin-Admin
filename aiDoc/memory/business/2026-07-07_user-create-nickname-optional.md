# 用户新增·昵称改为非必填

## 需求描述

系统用户新增接口 `nickname`（昵称）由必填改为非必填。前端表单本就允许留空，但后端 `SysUserCreate.nickname` 声明为 `str = Field(...)` 必填，触发全局非空校验，导致留空提交时报「用户昵称不能为空」。

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/admin/schemas/sys/user.py` 的 `SysUserCreate.nickname`：`str = Field(..., max_length=100)` → `Optional[str] = Field(None, max_length=100)`，与 `SysUserUpdate.nickname` 写法对齐。

### 前端

无需改动。`user-operate-drawer.vue` 的 `rules` 本就不含 nickname（`RuleKey` 未列入），NFormItem 也未传 rule，前端一直不强制昵称。

## 约束与备注

- 数据库 `sys_user.nickname` 本就是 `nullable=True`（ORM `SysUser.nickname` 显式 `nullable=True`，alembic 0001 同步），存 NULL 合法。
- 前端留空时提交空字符串 `""`（`createDefaultModel` 默认 `nickname: ''`）；改 Optional 后空串被 Pydantic 接受，`_check_required_non_empty` 因字段 `is_required()=False` 跳过，最终存空串。展示层有 `nickname or username` 回退（如 `notice_service` / `online_user_service`），空串不影响显示。
- 全局校验机制见 [2026-07-06 全局必填字段非空校验](./2026-07-06_global-required-validation.md)：仅 `Field(...)` 必填字段才做非空校验，带默认值的非必填字段天然跳过——这是「非必填字段不做非空校验」原则的框架层保障。

## 相关文件

- backend/modules/admin/schemas/sys/user.py
- backend/database/models/sys/user.py
- backend/modules/admin/services/sys/user_service.py
- frontend/src/views/manage/user/modules/user-operate-drawer.vue

## 记录日期

2026-07-07
