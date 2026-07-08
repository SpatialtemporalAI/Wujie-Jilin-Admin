<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NCard, NDataTable, NPopconfirm, NTag, useMessage } from 'naive-ui';
import {
  fetchBatchDeleteMerchantCallLog,
  fetchClearMerchantCallLog,
  fetchDeleteMerchantCallLog,
  fetchGetMerchantCallLogList
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { useExportSubmit } from '@/hooks/business/export-task';
import { $t } from '@/locales';
import CallLogSearch from './modules/call-log-search.vue';
import CallLogDetailDrawer from './modules/call-log-detail-drawer.vue';

const appStore = useAppStore();
const message = useMessage();
const { hasAuth } = useAuth();
const { submitting, submitExport } = useExportSubmit();

const searchParams: Api.Merchant.CallLogSearchParams = reactive({
  page: 1,
  page_size: 10,
  merchant_id: null,
  action: null,
  success: null,
  api_key: null,
  start_time: null,
  end_time: null
});

const {
  columns,
  columnChecks,
  data,
  getData,
  getDataByPage,
  loading,
  mobilePagination
} = useNaivePaginatedTable({
  api: () => fetchGetMerchantCallLogList(searchParams),
  transform: response => {
    return defaultTransform(response);
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
      align: 'center',
      width: 64,
      render: (_, index) => index + 1
    },
    {
      key: 'merchant_name',
      title: $t('page.manage.callLog.merchantName'),
      align: 'center',
      minWidth: 120,
      render: row => row.merchant_name || row.merchant_code || '-'
    },
    {
      key: 'api_key_masked',
      title: $t('page.manage.callLog.apiKey'),
      align: 'center',
      minWidth: 140,
      ellipsis: { tooltip: true }
    },
    {
      key: 'action',
      title: $t('page.manage.callLog.action'),
      align: 'center',
      minWidth: 110
    },
    {
      key: 'method',
      title: $t('page.manage.callLog.method'),
      align: 'center',
      width: 80,
      render: row => {
        const methodColorMap: Record<string, NaiveUI.ThemeColor> = {
          GET: 'success',
          POST: 'info',
          PUT: 'warning',
          DELETE: 'error',
          PATCH: 'default'
        };
        return (
          <NTag type={methodColorMap[row.method ?? ''] || 'default'} size="small">
            {row.method}
          </NTag>
        );
      }
    },
    {
      key: 'path',
      title: $t('page.manage.callLog.path'),
      align: 'center',
      minWidth: 180,
      ellipsis: { tooltip: true }
    },
    {
      key: 'ip',
      title: $t('page.manage.callLog.ip'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'success',
      title: $t('page.manage.callLog.success'),
      align: 'center',
      width: 90,
      render: row => {
        if (row.success == null) return '-';
        return (
          <NTag type={row.success ? 'success' : 'error'} size="small">
            {row.success ? $t('page.manage.callLog.successTrue') : $t('page.manage.callLog.successFalse')}
          </NTag>
        );
      }
    },
    {
      key: 'response_code',
      title: $t('page.manage.callLog.responseCode'),
      align: 'center',
      width: 90,
      render: row => {
        if (!row.response_code) return '-';
        const type: NaiveUI.ThemeColor = row.response_code < 400 ? 'success' : 'error';
        return <NTag type={type} size="small">{row.response_code}</NTag>;
      }
    },
    {
      key: 'elapsed_ms',
      title: $t('page.manage.callLog.elapsedMs'),
      align: 'center',
      width: 90,
      render: row => {
        if (row.elapsed_ms == null) return '-';
        return <span>{Math.round(row.elapsed_ms)}ms</span>;
      }
    },
    {
      key: 'created_at',
      title: $t('page.manage.callLog.callTime'),
      align: 'center',
      minWidth: 160
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 140,
      render: row => {
        return (
          <div class="flex flex-wrap justify-center gap-8px">
            <NButton type="primary" text size="small" onClick={() => handleViewDetail(row.id)}>
              {$t('page.manage.callLog.viewDetail')}
            </NButton>
            {hasAuth('merchant:call-log:delete') && (
              <NPopconfirm onPositiveClick={() => handleDelete(row.id)}>
                {{
                  default: () => $t('common.confirmDelete'),
                  trigger: () => (
                    <NButton type="error" text size="small">
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

const { checkedRowKeys, onBatchDeleted, onDeleted } = useTableOperate(data, 'id', getData);

const detailDrawerVisible = ref(false);
const detailLogId = ref<number | null>(null);

function handleViewDetail(id: number) {
  detailLogId.value = id;
  detailDrawerVisible.value = true;
}

async function handleDelete(id: number) {
  try {
    await fetchDeleteMerchantCallLog(id);
    onDeleted();
  } catch (error) {
    console.error('删除调用日志失败:', error);
  }
}

async function handleBatchDelete() {
  if (checkedRowKeys.value.length === 0) {
    message.warning($t('common.selectAtLeastOne'));
    return;
  }
  try {
    await fetchBatchDeleteMerchantCallLog(checkedRowKeys.value.map(Number));
    onBatchDeleted();
  } catch (error) {
    message.error($t('common.deleteFailed'));
  }
}

async function handleClear() {
  try {
    await fetchClearMerchantCallLog(30);
    message.success($t('common.deleteSuccess'));
    getData();
  } catch (error) {
    message.error($t('common.deleteFailed'));
  }
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-12px overflow-hidden lt-sm:overflow-auto">
    <div class="flex-y-center justify-between gap-12px">
      <CallLogSearch v-model:model="searchParams" @search="getDataByPage" />
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :disabled-delete="checkedRowKeys.length === 0"
        :loading="loading"
        :show-add="false"
        delete-auth="merchant:call-log:delete"
        @delete="handleBatchDelete"
        @refresh="getData"
      >
        <template #prefix>
          <NPopconfirm v-if="hasAuth('merchant:call-log:delete')" @positive-click="handleClear">
            {{ $t('page.manage.callLog.clearConfirm') }}
            <template #trigger>
              <NButton type="warning" ghost size="small" :disabled="loading">
                {{ $t('page.manage.callLog.clear') }}
              </NButton>
            </template>
          </NPopconfirm>
          <NButton
            type="primary"
            ghost
            size="small"
            :loading="submitting"
            :disabled="loading"
            @click="submitExport('merchant_call_log', searchParams)"
          >
            {{ $t('common.export') }}
          </NButton>
        </template>
      </TableHeaderOperation>
    </div>
    <NCard :bordered="false" size="small" class="flex-1-hidden card-wrapper">
      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        :columns="columns"
        :data="data"
        size="small"
        :flex-height="!appStore.isMobile"
        :scroll-x="1500"
        :loading="loading"
        remote
        :row-key="row => row.id"
        :pagination="mobilePagination"
        class="sm:h-full"
      />
      <CallLogDetailDrawer v-model:visible="detailDrawerVisible" :log-id="detailLogId" />
    </NCard>
  </div>
</template>
