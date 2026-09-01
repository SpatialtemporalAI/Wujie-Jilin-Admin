# 业务需求模板

## 需求描述

登录后头像下拉菜单（原仅"退出登录"）上方新增"修改密码"入口，当前登录用户可自助修改密码（需验证旧密码），成功后强制重新登录。

## 状态

已完成

## 涉及范围

### 后端

- 新增 `PUT /admin/auth/password`（`backend/modules/admin/endpoints/auth.py`）：仅要求登录态（`current_user`），不要求 `sys:user:edit` 权限；`old_password` 必填校验；复用 `UserService.update_user_password` 并传入 `current_user=user`（超管本人可改自己密码，走旧密码校验）；加 `@log_operation` 操作日志
- 原 `PUT /admin/sys/user/{user_id}/password` 保持管理员改他人密码用途，未改动

### 前端

- `frontend/src/service/api/auth.ts` 新增 `fetchChangeOwnPassword(oldPassword, newPassword)`
- 新建 `frontend/src/layouts/modules/global-header/components/change-password-modal.vue`：NModal(preset=card) + NForm，旧密码/新密码(6-20位)/确认密码三项，成功后 toast + `authStore.resetStore()` 强制重新登录
- `user-avatar.vue` 下拉在 logout 上方插入"修改密码"（`common.changePassword`，图标 `ph:lock-key`）
- i18n：`page.manage.user.form.oldPassword` 补中英文 + `typings/app.d.ts` 类型

## 约束与备注

- 自助改密必须验证旧密码（后端 `RequestError("旧密码不能为空")` + service 层 `ForbiddenError("旧密码错误")`）
- 新密码长度 6-20 位，与既有用户密码规则一致
- 改密成功后强制重新登录

## 相关文件

- `backend/modules/admin/endpoints/auth.py`
- `backend/modules/admin/services/sys/user_service.py`（复用，未改）
- `frontend/src/layouts/modules/global-header/components/user-avatar.vue`
- `frontend/src/layouts/modules/global-header/components/change-password-modal.vue`
- `frontend/src/service/api/auth.ts`
- `frontend/src/locales/langs/zh-cn.ts` / `en-us.ts`、`frontend/src/typings/app.d.ts`

## 记录日期

2026-09-01
