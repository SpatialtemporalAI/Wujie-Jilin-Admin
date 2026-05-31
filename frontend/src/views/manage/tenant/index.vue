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
import { $t } from '@/locales';
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
      title: $t('common.index'),
      width: 64,
      align: 'center',
      render: (_: any, index: number) => index + 1
    },
    {
      key: 'name',
      title: $t('page.manage.tenant.tenantName'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'code',
      title: $t('page.manage.tenant.tenantCode'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'contact_name',
      title: $t('page.manage.tenant.contactName'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'max_users',
      title: $t('page.manage.tenant.maxUsers'),
      align: 'center',
      width: 80
    },
    {
      key: 'status',
      title: $t('common.status'),
      align: 'center',
      width: 80,
      render: (row: any) => {
        if (row.status === null) return null;
        const tagMap: Record<string, any> = { '1': 'success', '2': 'warning' };
        const labelMap: Record<string, string> = {
          '1': $t('page.manage.common.status.enable'),
          '2': $t('page.manage.common.status.disable')
        };
        return <NTag type={tagMap[row.status]}>{labelMap[row.status]}</NTag>;
      }
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      minWidth: 200,
      render: (row: any) => (
        <div class="flex flex-wrap justify-center gap-8px">
          {hasAuth('tenant:tenant:edit') && (
            <NButton type="primary" text size="small" onClick={() => edit(row.id)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('tenant:tenant:status') && (
            <NButton
              type={row.status === '1' ? 'warning' : 'success'}
              text
              size="small"
              onClick={() => handleToggleStatus(row)}
            >
              {row.status === '1' ? $t('page.manage.common.status.disable') : $t('page.manage.common.status.enable')}
            </NButton>
          )}
          {hasAuth('tenant:tenant:delete') && (
            <NPopconfirm onPositiveClick={() => handleDelete(row.id)}>
              {{
                default: () => $t('page.manage.tenant.confirmDelete'),
                trigger: () => (
                  <NButton type="error" text size="small">
                    {$t('common.delete')}
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
    window.$message?.success($t('page.manage.tenant.deleteSuccess'));
    onDeleted();
  }
}

async function handleToggleStatus(row: any) {
  const newStatus = row.status === '1' ? false : true;
  const { error } = await fetchUpdateTenantStatus(row.id, newStatus);
  if (!error) {
    window.$message?.success($t('page.manage.tenant.statusUpdateSuccess'));
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
    <NCard :title="$t('page.manage.tenant.title')" :bordered="false" size="small" class="card-wrapper sm:flex-1-hidden">
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
