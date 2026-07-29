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
const maskedSecret = computed(() =>
  showSecret.value ? apiSecret.value : '*'.repeat(Math.min(apiSecret.value.length, 40))
);

watch(visible, v => {
  if (!v) {
    showSecret.value = false;
  }
});

async function tryClipboardApi(text: string): Promise<boolean> {
  // 仅安全上下文（HTTPS / localhost）下可用；HTTP 内网部署返回 false 走兜底
  if (!window.isSecureContext || !navigator.clipboard) return false;
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

function legacyCopy(text: string): boolean {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.setAttribute('readonly', '');
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  let ok = false;
  try {
    ok = document.execCommand('copy');
  } catch {
    ok = false;
  }
  document.body.removeChild(ta);
  return ok;
}

async function copyText(text: string) {
  if (!text) return;
  // Clipboard API 失败时回退到 execCommand，保证 HTTP 部署下也能复制
  const ok = (await tryClipboardApi(text)) || legacyCopy(text);
  if (ok) {
    window.$message?.success($t('page.manage.merchant.copySuccess'));
  } else {
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
