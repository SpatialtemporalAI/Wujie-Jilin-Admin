# 前端页面组件示例

## 用途

展示如何组织一个标准的页面组件。

## 核心原则

- 每个页面有独立文件夹
- 主文件为 `index.vue`
- 子组件放在 `modules/` 子目录
- 共享逻辑放在 `shared.ts` 中
- 使用 NaiveUI 组件库

## 目录结构

```
src/views/manage/user/
├── index.vue              # 主页面（表格 + 搜索 + 分页）
├── modules/
│   ├── UserOperateDrawer.vue  # 新增/编辑抽屉组件
│   └── UserDetailModal.vue    # 详情弹窗组件
└── shared.ts              # 共享类型和工具函数
```

## 示例

### 主页面 `index.vue`

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { NButton, NDataTable, NSpace, NPagination } from 'naive-ui';
import { fetchGetUserList, fetchDeleteUser } from '@/service/api/system-manage';
import { useTable } from '@/hooks/common/table';
import UserOperateDrawer from './modules/UserOperateDrawer.vue';

const { data, loading, pagination, getData } = useTable(fetchGetUserList);
const operateDrawerVisible = ref(false);
const editingRow = ref<Api.SystemManage.UserInfo | null>(null);

function handleAdd() {
  editingRow.value = null;
  operateDrawerVisible.value = true;
}

function handleEdit(row: Api.SystemManage.UserInfo) {
  editingRow.value = row;
  operateDrawerVisible.value = true;
}

async function handleDelete(row: Api.SystemManage.UserInfo) {
  await fetchDeleteUser(row.id);
  await getData();
}
</script>

<template>
  <div class="h-full flex-col-stretch gap-16px overflow-hidden lt-sm:gap-12px">
    <NDataTable :columns="columns" :data="data" :loading="loading" />
    <NPagination v-model:page="pagination.page" :page-count="pagination.totalPages" />
  </div>
</template>
```

## 关键点

- 页面组件只负责布局和交互，业务逻辑通过 API 函数调用
- 使用 NaiveUI 组件库（`NDataTable`、`NForm`、`NModal` 等）
- 子组件通过 `defineEmits` 和 `defineProps` 与父组件通信
- 状态管理使用 `ref` / `reactive`（组件内）或 Pinia（跨组件）

## 真实参考文件

- `frontend/src/views/manage/`
- `frontend/src/views/home/`
