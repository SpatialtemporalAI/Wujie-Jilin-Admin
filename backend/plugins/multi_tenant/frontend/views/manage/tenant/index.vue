<script setup lang="tsx">
import { reactive } from 'vue';
import { NButton, NPopconfirm, NTag } from 'naive-ui';
import {
  fetchGetTenantList,
  fetchDeleteTenant,
  fetchUpdateTenantStatus
} from '@/plugins/multi_tenant/api/tenant';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { booleanToEnableStatus } from '@/utils/status';
import TenantOperateDrawer from './modules/tenant-operate-drawer.vue';
import TenantSearch from './modules/tenant-search.vue';

const appStore = useAppStore();
const { hasAuth } = useAuth();

const searchParams = reactive({
  page: 1,
  page_size: 10,
  name: null as string | null,
  code: null as string | null,
  status: null as string | null
});

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetTenantList(searchParams),
  transform: response => {
    const result = defaultTransform(response);
    result.data = result.data.map((item: any) => ({
      ...item,
      status: booleanToEnableStatus(item.status)
    }));
    return result;
  },
  onPaginationParamsChange: params => {
    searchParams.page = params.page;
    searchParams.page_size = params.pageSize;
  },
  columns: () => [
    {
      type: 'selection',
      align: 'center',
      width: 48
    },
    {
      key: 'index',
      title: '序号',
      width: 64,
      align: 'center',
      render: (_: any, index: number) => index + 1
    },
    {
      key: 'name',
      title: '租户名称',
      align: 'center',
      minWidth: 120
    },
    {
      key: 'code',
      title: '租户编码',
      align: 'center',
      minWidth: 100
    },
    {
      key: 'contact_name',
      title: '联系人',
      align: 'center',
      minWidth: 100
    },
    {
      key: 'max_users',
      title: '用户上限',
      align: 'center',
      width: 80
    },
    {
      key: 'status',
      title: '状态',
      align: 'center',
      width: 80,
      render: (row: any) => {
        if (row.status === null) return null;
        const tagMap: Record<string, any> = { '1': 'success', '2': 'warning' };
        const labelMap: Record<string, string> = { '1': '启用', '2': '禁用' };
        return <NTag type={tagMap[row.status]}>{labelMap[row.status]}</NTag>;
      }
    },
    {
      key: 'operate',
      title: '操作',
      align: 'center',
      minWidth: 200,
      render: (row: any) => (
        <div class="flex flex-wrap justify-center gap-8px">
          {hasAuth('tenant:tenant:edit') && (
            <NButton type="primary" text size="small" onClick={() => edit(row.id)}>
              编辑
            </NButton>
          )}
          {hasAuth('tenant:tenant:status') && (
            <NButton
              type={row.status === '1' ? 'warning' : 'success'}
              text
              size="small"
              onClick={() => handleToggleStatus(row)}
            >
              {row.status === '1' ? '禁用' : '启用'}
            </NButton>
          )}
          {hasAuth('tenant:tenant:delete') && (
            <NPopconfirm onPositiveClick={() => handleDelete(row.id)}>
              {{
                default: () => '确认删除该租户？',
                trigger: () => (
                  <NButton type="error" text size="small">
                    删除
                  </NButton>
                )
              }}
            </NPopconfirm>
          )}
        </div>
      )
    }
  ]
});

const { drawerVisible, operateType, editingData, handleAdd, handleEdit, checkedRowKeys, onDeleted } = useTableOperate(
  data,
  'id',
  getData
);

async function handleDelete(id: number) {
  const { error } = await fetchDeleteTenant(id);
  if (!error) {
    window.$message?.success('删除成功');
    onDeleted();
  }
}

async function handleToggleStatus(row: any) {
  const newStatus = row.status === '1' ? false : true;
  const { error } = await fetchUpdateTenantStatus(row.id, newStatus);
  if (!error) {
    window.$message?.success('状态更新成功');
    getData();
  }
}

function edit(id: number) {
  handleEdit(id);
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <TenantSearch v-model:model="searchParams" @search="getDataByPage" />
    <NCard title="租户管理" :bordered="false" size="small" class="card-wrapper sm:flex-1-hidden">
      <template #header-extra>
        <TableHeaderOperation
          v-model:columns="columnChecks"
          :disabled-delete="checkedRowKeys.length === 0"
          :loading="loading"
          add-auth="tenant:tenant:add"
          delete-auth="tenant:tenant:delete"
          @add="handleAdd"
          @refresh="getData"
        />
      </template>
      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        :columns="columns"
        :data="data"
        size="small"
        :flex-height="!appStore.isMobile"
        :scroll-x="800"
        :loading="loading"
        remote
        :row-key="(row: any) => row.id"
        :pagination="mobilePagination"
        class="sm:h-full"
      />
      <TenantOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
