<script setup lang="ts">
import { ref, watch } from 'vue';
import {
  NButton,
  NDescriptions,
  NDescriptionsItem,
  NDrawer,
  NDrawerContent,
  NDivider,
  NScrollbar,
  NSpin,
  NTag
} from 'naive-ui';
import { fetchGetMerchantCallLog } from '@/service/api';
import { $t } from '@/locales';

defineOptions({
  name: 'CallLogDetailDrawer'
});

interface Props {
  logId: number | null;
}

const props = defineProps<Props>();

const visible = defineModel<boolean>('visible', { required: true });

const loading = ref(false);
const detail = ref<Api.Merchant.CallLogDetail | null>(null);

watch(
  () => props.logId,
  async newId => {
    if (newId && visible.value) {
      await loadDetail(newId);
    }
  }
);

watch(visible, async val => {
  if (val && props.logId) {
    await loadDetail(props.logId);
  }
  if (!val) {
    detail.value = null;
  }
});

async function loadDetail(id: number) {
  loading.value = true;
  try {
    const { data, error } = await fetchGetMerchantCallLog(id);
    if (!error) {
      detail.value = data;
    }
  } catch (error) {
    console.error('获取调用日志详情失败:', error);
  } finally {
    loading.value = false;
  }
}

function formatJson(str: string | null): string {
  if (!str) return '-';
  try {
    return JSON.stringify(JSON.parse(str), null, 2);
  } catch {
    return str;
  }
}
</script>

<template>
  <NDrawer v-model:show="visible" :width="520" display-directive="show">
    <NDrawerContent :title="$t('page.manage.callLog.detailTitle')" :native-scrollbar="false" closable>
      <NSpin :show="loading">
        <template v-if="detail">
          <NDescriptions label-placement="left" bordered :column="1" size="small">
            <NDescriptionsItem :label="$t('page.manage.callLog.merchantName')">
              {{ detail.merchant_name || detail.merchant_code || '-' }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.callLog.apiKey')">
              {{ detail.api_key_masked || '-' }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.callLog.action')">
              {{ detail.action || '-' }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.callLog.method')">
              {{ detail.method || '-' }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.callLog.path')">
              {{ detail.path || '-' }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.callLog.ip')">
              {{ detail.ip || '-' }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.callLog.success')">
              <NTag v-if="detail.success != null" :type="detail.success ? 'success' : 'error'" size="small">
                {{ detail.success ? $t('page.manage.callLog.successTrue') : $t('page.manage.callLog.successFalse') }}
              </NTag>
              <span v-else>-</span>
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.callLog.responseCode')">
              {{ detail.response_code ?? '-' }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.callLog.elapsedMs')">
              {{ detail.elapsed_ms != null ? `${Math.round(detail.elapsed_ms)}ms` : '-' }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.callLog.errorMsg')">
              {{ detail.error_msg || '-' }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.callLog.callTime')">
              {{ detail.created_at || '-' }}
            </NDescriptionsItem>
          </NDescriptions>

          <NDivider>{{ $t('page.manage.callLog.requestParams') }}</NDivider>
          <NScrollbar x-scrollable style="max-height: 200px">
            <pre class="whitespace-pre-wrap break-all rounded bg-gray-100 p-12px text-13px dark:bg-dark-800">{{ formatJson(detail.request_params) }}</pre>
          </NScrollbar>

          <NDivider>{{ $t('page.manage.callLog.responseResult') }}</NDivider>
          <NScrollbar x-scrollable style="max-height: 200px">
            <pre class="whitespace-pre-wrap break-all rounded bg-gray-100 p-12px text-13px dark:bg-dark-800">{{ formatJson(detail.response_result) }}</pre>
          </NScrollbar>
        </template>
      </NSpin>
      <template #footer>
        <NButton @click="visible = false">{{ $t('common.close') }}</NButton>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>
