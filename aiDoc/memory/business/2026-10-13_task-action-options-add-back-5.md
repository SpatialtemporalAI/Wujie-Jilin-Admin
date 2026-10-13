# 巡逻任务运控动作下拉加回 5 项

## 需求描述

任务管理新增/编辑任务中，巡逻任务的运控动作下拉添加：击掌(high_five)、拥抱(hug)、右手飞吻(right_kiss)、双手飞吻(two_hand_kiss)、动感光波(x_ray)。

## 状态

已完成

## 涉及范围

### 前端

- `views/task/modules/task-operate-drawer.vue` 的 `actionOptions` 加回 5 项（按 2026-07-01 版 14 项顺序插入，不含 left_kiss）；播报动作选项 `broadcastActionOptions` 由 filter 派生，自动包含

### 后端

无改动：`TaskActionItem.action` 为 `str(max_length=20)`，无枚举校验，且描述注释本来就列有这 14 项。

## 约束与备注

- 这 5 项是 2026-07-02 精简时移除项的子集；`TaskAction` 联合类型（`typings/api/task.d.ts`）与详情抽屉 `actionLabel`（`task-detail-drawer.vue`）从未删过这些值，本次只需改下拉选项一处
- 左手飞吻(left_kiss) 未在需求中，未加回

## 相关文件

- `frontend/src/views/task/modules/task-operate-drawer.vue`

## 记录日期

2026-10-13
