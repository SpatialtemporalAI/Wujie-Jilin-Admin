# 用户密码长度统一限定 6-20 字符

## 需求描述

用户管理「修改密码」时，新密码过长会触发后端 422（`SysUserPasswordUpdate.new_password`
原 `max_length=100`）。期望新增用户与修改密码两处密码统一限定 **6-20 字符**，前端在提交前
就用友好提示拦住，后端兜底校验。

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/admin/schemas/sys/user.py`
  - `SysUserCreate.password`：本就 `min_length=6, max_length=20`，无需改
  - `SysUserPasswordUpdate.new_password`：`max_length=100` → `max_length=20`（修复 422）

### 前端

- `frontend/src/views/manage/user/modules/user-password-drawer.vue`（修改密码）
  - `newPassword` 规则补 `max: 20`，文案由 `passwordMinLength`（仅「至少 6 位」）换为
    `passwordLength`（「6-20 字符」），与新增加用户一致
  - `newPassword` / `confirmPassword` 两个 NInput 加 `:maxlength="20"`，输入即封顶
- `frontend/src/views/manage/user/modules/user-operate-drawer.vue`（新增用户）
  - 规则本就有 `min:6, max:20`，仅给 `password` / `confirmPassword` NInput 补 `:maxlength="20"`

### i18n

- 复用已有 `page.manage.user.form.passwordLength`（中：「密码长度必须在6-20个字符之间」/
  英：「password length must be between 6 and 20 characters」），未新增 key

## 关键决策

### 不动登录密码字段

`auth.py` 登录用的 password 字段不加长度上限——历史用户可能已设置更长密码，登录校验放宽
避免误伤。长度约束只作用于「写」入口（新增 / 改密）。

### 仅约束长度，不加复杂度

与现有 `SysUserCreate` 保持一致，只限 6-20 长度，不引入大小写/数字/符号等复杂度规则。

## 验证

- `python -m py_compile backend/modules/admin/schemas/sys/user.py` 通过
- 前端 `pnpm typecheck` 通过

## 相关文件

- `backend/modules/admin/schemas/sys/user.py`
- `frontend/src/views/manage/user/modules/user-password-drawer.vue`
- `frontend/src/views/manage/user/modules/user-operate-drawer.vue`

## 记录日期

2026-07-14
