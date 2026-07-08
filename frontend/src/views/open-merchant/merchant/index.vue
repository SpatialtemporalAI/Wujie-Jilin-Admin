<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NPopconfirm, NTag } from 'naive-ui';
import { enableStatusRecord } from '@/constants/business';
import {
  fetchDeleteMerchant,
  fetchGetMerchantList,
  fetchResetMerchantApiKey
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import { booleanToEnableStatus } from '@/utils/status';
import MerchantOperateDrawer from './modules/merchant-operate-drawer.vue';
import MerchantSearch from './modules/merchant-search.vue';
import MerchantApiKeyModal from './modules/merchant-api-key-modal.vue';

const appStore = useAppStore();
const { hasAuth } = useAuth();

const searchParams: Api.Merchant.MerchantSearchParams = reactive({
  page: 1,
  page_size: 10,
  name: null,
  code: null,
  status: null
});

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetMerchantList(searchParams),
  transform: response => {
    const result = defaultTransform(response);
    result.data = result.data.map((merchant: Api.Merchant.Merchant) => ({
      ...merchant,
      status: booleanToEnableStatus(merchant.status)
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
      render: (_, index) => index + 1
    },
    {
      key: 'name',
      title: $t('page.manage.merchant.merchantName'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'code',
      title: $t('page.manage.merchant.merchantCode'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'api_key',
      title: $t('page.manage.merchant.apiKey'),
      minWidth: 200,
      ellipsis: { tooltip: true }
    },
    {
      key: 'contact_name',
      title: $t('page.manage.merchant.contactName'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'contact_phone',
      title: $t('page.manage.merchant.contactPhone'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'status',
      title: $t('page.manage.merchant.merchantStatus'),
      align: 'center',
      width: 90,
      render: (row: Api.Merchant.Merchant) => {
        if (row.status === null) {
          return null;
        }

        const tagMap: Record<Api.Common.EnableStatus, NaiveUI.ThemeColor> = {
          '1': 'success',
          '2': 'warning'
        };

        const label = $t(enableStatusRecord[row.status]);

        return <NTag type={tagMap[row.status]}>{label}</NTag>;
      }
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      minWidth: 200,
      render: (row: Api.Merchant.Merchant) => {
        return (
          <div class="flex flex-wrap justify-center gap-8px">
            {hasAuth('merchant:edit') && (
              <NButton type="primary" text size="small" onClick={() => edit(row.id)}>
                {$t('common.edit')}
              </NButton>
            )}
            {hasAuth('merchant:edit') && (
              <NPopconfirm onPositiveClick={() => handleResetApiKey(row.id)}>
                {{
                  default: () => $t('page.manage.merchant.resetConfirm'),
                  trigger: () => (
                    <NButton type="warning" text size="small">
                      {$t('page.manage.merchant.resetApiKey')}
                    </NButton>
                  )
                }}
              </NPopconfirm>
            )}
            {hasAuth('merchant:delete') && (
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

const { drawerVisible, operateType, editingData, handleAdd, handleEdit, checkedRowKeys, onDeleted } = useTableOperate<
  Api.Merchant.Merchant
>(data, 'id', getData);

// API 凭证弹窗（新增/重置时展示，secret 仅一次）
const keyModalVisible = ref(false);
const keyModalCredentials = ref<Api.Merchant.ApiCredentials | null>(null);

async function handleDelete(id: number) {
  const { error } = await fetchDeleteMerchant(id);
  if (!error) {
    onDeleted();
  }
}

async function handleResetApiKey(id: number) {
  const { error, data: cred } = await fetchResetMerchantApiKey(id);
  if (!error && cred) {
    keyModalCredentials.value = cred;
    keyModalVisible.value = true;
    getDataByPage();
  }
}

function onCreated(cred: Api.Merchant.ApiCredentials) {
  keyModalCredentials.value = cred;
  keyModalVisible.value = true;
  getDataByPage();
}

function edit(id: number) {
  handleEdit(id);
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <div class="flex-y-center justify-between gap-12px">
      <MerchantSearch v-model:model="searchParams" @search="getDataByPage" />
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :disabled-delete="checkedRowKeys.length === 0"
        :loading="loading"
        add-auth="merchant:add"
        delete-auth="merchant:delete"
        @add="handleAdd"
        @refresh="getData"
      />
    </div>
    <NCard :bordered="false" size="small" class="card-wrapper sm:flex-1-hidden">
      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        :columns="columns"
        :data="data"
        size="small"
        :flex-height="!appStore.isMobile"
        :scroll-x="1100"
        :loading="loading"
        remote
        :row-key="(row: Api.Merchant.Merchant) => row.id"
        :pagination="mobilePagination"
        class="sm:h-full"
      />
      <MerchantOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        @submitted="getDataByPage"
        @created="onCreated"
      />
      <MerchantApiKeyModal v-model:visible="keyModalVisible" :credentials="keyModalCredentials" />
    </NCard>
  </div>
</template>

<style scoped></style>
