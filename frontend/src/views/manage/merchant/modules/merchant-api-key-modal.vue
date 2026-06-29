<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { $t } from '@/locales';

defineOptions({
  name: 'MerchantApiKeyModal'
});

interface Props {
  credentials: Api.Merchant.ApiCredentials | null;
}

const props = defineProps<Props>();

const visible = defineModel<boolean>('visible', { default: false });

const showSecret = ref(false);

const apiKey = computed(() => props.credentials?.api_key ?? '');
const apiSecret = computed(() => props.credentials?.api_secret ?? '');
const maskedSecret = computed(() => (showSecret.value ? apiSecret.value : '*'.repeat(Math.min(apiSecret.value.length, 40))));

watch(visible, v => {
  if (!v) {
    showSecret.value = false;
  }
});

async function copyText(text: string) {
  if (!text) return;
  try {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(text);
    } else {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    window.$message?.success($t('page.manage.merchant.copySuccess'));
  } catch {
    window.$message?.error($t('page.manage.merchant.copyFailed'));
  }
}
</script>

<template>
  <NModal
    v-model:show="visible"
    preset="card"
    :title="$t('page.manage.merchant.apiKeyTitle')"
    class="w-560px"
    :mask-closable="false"
    :close-on-esc="false"
  >
    <NAlert type="warning" :show-icon="true" class="mb-16px">
      {{ $t('page.manage.merchant.secretOnceTip') }}
    </NAlert>
    <NSpace vertical :size="16">
      <div>
        <div class="mb-8px font-medium">{{ $t('page.manage.merchant.apiKey') }}</div>
        <NInputGroup>
          <NInput :value="apiKey" readonly />
          <NButton type="primary" @click="copyText(apiKey)">{{ $t('page.manage.merchant.copy') }}</NButton>
        </NInputGroup>
      </div>
      <div>
        <div class="mb-8px flex items-center justify-between">
          <span class="font-medium">{{ $t('page.manage.merchant.apiSecret') }}</span>
          <NButton text type="primary" size="small" @click="showSecret = !showSecret">
            {{ showSecret ? $t('page.manage.merchant.hideSecret') : $t('page.manage.merchant.showSecret') }}
          </NButton>
        </div>
        <NInputGroup>
          <NInput :value="maskedSecret" readonly />
          <NButton type="primary" @click="copyText(apiSecret)">{{ $t('page.manage.merchant.copy') }}</NButton>
        </NInputGroup>
      </div>
    </NSpace>
    <template #footer>
      <div class="flex justify-end">
        <NButton type="primary" @click="visible = false">{{ $t('common.confirm') }}</NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped></style>
