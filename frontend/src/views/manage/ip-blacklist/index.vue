<script setup lang="tsx">
import { reactive } from 'vue';
import { NButton, NCard, NDataTable, NPopconfirm, NTag, useMessage } from 'naive-ui';
import {
  fetchBatchDeleteIpBlacklist,
  fetchDeleteIpBlacklist,
  fetchGetIpBlacklistList
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import IpBlacklistOperateDrawer from './modules/ip-blacklist-operate-drawer.vue';
import IpBlacklistSearch from './modules/ip-blacklist-search.vue';

const appStore = useAppStore();
const message = useMessage();
const { hasAuth } = useAuth();

const searchParams: Api.SystemManage.IpBlacklistSearchParams = reactive({
  page: 1,
  page_size: 10,
  ip: null,
  type: null,
  start_date: null,
  end_date: null
});

const typeOptions = [
  { label: $t('page.manage.ipBlacklist.typePermanent'), value: 'permanent' },
  { label: $t('page.manage.ipBlacklist.typeTemporary'), value: 'temporary' }
];

const {
  columns,
  columnChecks,
  data: tableData,
  getData,
  getDataByPage,
  loading,
  mobilePagination
} = useNaivePaginatedTable({
  api: () => fetchGetIpBlacklistList(searchParams),
  transform: response => defaultTransform(response),
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
      align: 'center',
      width: 64,
      render: (_, index) => index + 1
    },
    {
      key: 'ip',
      title: $t('page.manage.ipBlacklist.ip'),
      align: 'center',
      minWidth: 140
    },
    {
      key: 'type',
      title: $t('page.manage.ipBlacklist.type'),
      align: 'center',
      width: 100,
      render: row => {
        const isPermanent = row.type === 'permanent';
        return <NTag type={isPermanent ? 'error' : 'warning'}>{isPermanent ? $t('page.manage.ipBlacklist.typePermanent') : $t('page.manage.ipBlacklist.typeTemporary')}</NTag>;
      }
    },
    {
      key: 'reason',
      title: $t('page.manage.ipBlacklist.reason'),
      align: 'center',
      minWidth: 180,
      ellipsis: { tooltip: true }
    },
    {
      key: 'expire_at',
      title: $t('page.manage.ipBlacklist.expireAt'),
      align: 'center',
      width: 180,
      render: row => row.expire_at || '-'
    },
    {
      key: 'created_at',
      title: $t('page.manage.ipBlacklist.createdAt'),
      align: 'center',
      width: 180,
      render: row => row.created_at || '-'
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 100,
      fixed: 'right',
      render: row => {
        return (
          <div class="flex-center gap-8px">
            {hasAuth('sys:blacklist:remove') && (
              <NPopconfirm onPositiveClick={() => handleDelete(row.id)}>
                {{
                  default: () => $t('common.confirmDelete'),
                  trigger: () => (
                    <NButton type="error" ghost size="small">
                      {$t('common.delete')}
                    </NButton>
                  )
                }}
              </NPopconfirm>
            )}
          </div>
        );
      }
    }
  ]
});

const {
  drawerVisible,
  operateType,
  handleAdd,
  checkedRowKeys,
  onBatchDeleted,
  onDeleted
} = useTableOperate(tableData, 'id', getData);

async function handleDelete(id: number) {
  try {
    await fetchDeleteIpBlacklist(id);
    message.success($t('common.deleteSuccess'));
    onDeleted();
  } catch (error) {
    console.error('删除失败:', error);
  }
}

async function handleBatchDelete() {
  if (checkedRowKeys.value.length === 0) {
    return;
  }
  try {
    await fetchBatchDeleteIpBlacklist(checkedRowKeys.value.map(Number));
    message.success($t('common.deleteSuccess'));
    onBatchDeleted();
  } catch (error) {
    console.error('批量删除失败:', error);
  }
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <IpBlacklistSearch v-model:model="searchParams" @search="getDataByPage" />
    <NCard :title="$t('page.manage.ipBlacklist.title')" :bordered="false" size="small" class="card-wrapper sm:flex-1-hidden">
      <template #header-extra>
        <TableHeaderOperation
          v-model:columns="columnChecks"
          :disabled-delete="checkedRowKeys.length === 0"
          :loading="loading"
          @add="handleAdd"
          @delete="handleBatchDelete"
          @refresh="getData"
        >
          <template #default>
            <NButton v-if="hasAuth('sys:blacklist:add')" size="small" ghost type="primary" @click="handleAdd">
              <template #icon>
                <icon-ic-round-plus class="text-icon" />
              </template>
              {{ $t('common.add') }}
            </NButton>
            <NPopconfirm v-if="hasAuth('sys:blacklist:remove')" @positive-click="handleBatchDelete">
              <template #trigger>
                <NButton size="small" ghost type="error" :disabled="checkedRowKeys.length === 0">
                  <template #icon>
                    <icon-ic-round-delete class="text-icon" />
                  </template>
                  {{ $t('common.batchDelete') }}
                </NButton>
              </template>
              {{ $t('common.confirmDelete') }}
            </NPopconfirm>
          </template>
        </TableHeaderOperation>
      </template>
      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        :columns="columns"
        :data="tableData"
        size="small"
        :flex-height="!appStore.isMobile"
        :scroll-x="1000"
        :loading="loading"
        remote
        :row-key="row => row.id"
        :pagination="mobilePagination"
        class="sm:h-full"
      />
      <IpBlacklistOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>

<style scoped></style>
