<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import {
  NSelect,
  NInput,
  NInputNumber,
  NCard,
  NForm,
  NFormItem,
  NButton,
  NSpace,
  NSpin,
  NGrid,
  NGi,
  NDivider
} from 'naive-ui';
import {
  fetchGetTenantList,
  fetchGetTenantConfig,
  fetchUpdateTenantConfig
} from '@/plugins/multi_tenant/api/tenant';

const algorithmOptions = [
  { label: 'HS256', value: 'HS256' },
  { label: 'HS384', value: 'HS384' },
  { label: 'HS512', value: 'HS512' }
];

const tenantOptions = ref<{ label: string; value: number }[]>([]);
const selectedTenantId = ref<number | null>(null);
const loading = ref(false);
const saving = ref(false);
const formRef = ref();

const formData = ref({
  jwt_config: {
    secret_key: null as string | null,
    algorithm: null as string | null,
    access_lifetime: null as number | null,
    refresh_lifetime: null as number | null
  },
  login_url: null as string | null
});

onMounted(async () => {
  const { data } = await fetchGetTenantList({ page: 1, page_size: 200 });
  if (data) {
    tenantOptions.value = (data.records || []).map((t: any) => ({
      label: `${t.name} (${t.code})`,
      value: t.id
    }));
  }
});

watch(selectedTenantId, async id => {
  if (!id) {
    resetForm();
    return;
  }
  loading.value = true;
  try {
    const { data } = await fetchGetTenantConfig(id);
    if (data) {
      formData.value = {
        jwt_config: {
          secret_key: data.jwt_config?.secret_key ?? null,
          algorithm: data.jwt_config?.algorithm ?? null,
          access_lifetime: data.jwt_config?.access_lifetime ?? null,
          refresh_lifetime: data.jwt_config?.refresh_lifetime ?? null
        },
        login_url: data.login_url ?? null
      };
    }
  } finally {
    loading.value = false;
  }
});

function resetForm() {
  formData.value = {
    jwt_config: {
      secret_key: null,
      algorithm: null,
      access_lifetime: null,
      refresh_lifetime: null
    },
    login_url: null
  };
}

async function handleSave() {
  if (!selectedTenantId.value) {
    window.$message?.warning('请先选择租户');
    return;
  }
  saving.value = true;
  try {
    const payload: any = {
      jwt_config: {
        secret_key: formData.value.jwt_config.secret_key || null,
        algorithm: formData.value.jwt_config.algorithm || null,
        access_lifetime: formData.value.jwt_config.access_lifetime ?? null,
        refresh_lifetime: formData.value.jwt_config.refresh_lifetime ?? null
      },
      login_url: formData.value.login_url || null
    };
    const { error } = await fetchUpdateTenantConfig(selectedTenantId.value, payload);
    if (!error) {
      window.$message?.success('配置保存成功');
    }
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <NCard title="租户配置" :bordered="false" size="small" class="card-wrapper">
      <template #header-extra>
        <NSpace align="center">
          <span class="text-14px">选择租户：</span>
          <NSelect
            v-model:value="selectedTenantId"
            :options="tenantOptions"
            placeholder="请选择租户"
            clearable
            style="width: 280px"
          />
        </NSpace>
      </template>

      <NSpin :show="loading">
        <NForm
          ref="formRef"
          :model="formData"
          label-placement="left"
          label-width="120px"
          class="max-w-800px"
        >
          <NDivider title-placement="left">JWT 配置</NDivider>

          <NGrid :cols="1" :x-gap="24" responsive="screen" item-responsive>
            <NGi span="1">
              <NFormItem label="密钥" path="jwt_config.secret_key">
                <NInput
                  v-model:value="formData.jwt_config.secret_key"
                  type="password"
                  show-password-on="click"
                  placeholder="留空则使用全局默认值"
                />
              </NFormItem>
            </NGi>
            <NGi span="1">
              <NFormItem label="签名算法" path="jwt_config.algorithm">
                <NSelect
                  v-model:value="formData.jwt_config.algorithm"
                  :options="algorithmOptions"
                  placeholder="留空则使用全局默认值"
                  clearable
                />
              </NFormItem>
            </NGi>
            <NGi span="1">
              <NFormItem label="过期时间" path="jwt_config.access_lifetime">
                <NInputNumber
                  v-model:value="formData.jwt_config.access_lifetime"
                  :min="1"
                  :max="86400"
                  placeholder="留空则使用全局默认值"
                  class="w-full"
                >
                  <template #suffix>秒</template>
                </NInputNumber>
              </NFormItem>
            </NGi>
            <NGi span="1">
              <NFormItem label="有效期" path="jwt_config.refresh_lifetime">
                <NInputNumber
                  v-model:value="formData.jwt_config.refresh_lifetime"
                  :min="1"
                  :max="604800"
                  placeholder="留空则使用全局默认值"
                  class="w-full"
                >
                  <template #suffix>秒</template>
                </NInputNumber>
              </NFormItem>
            </NGi>
          </NGrid>

          <NDivider title-placement="left">登录配置</NDivider>

          <NGrid :cols="1" :x-gap="24" responsive="screen" item-responsive>
            <NGi span="1">
              <NFormItem label="登录 URL" path="login_url">
                <NInput
                  v-model:value="formData.login_url"
                  placeholder="留空则使用系统默认登录页，例: https://tenant.example.com/login"
                />
              </NFormItem>
            </NGi>
          </NGrid>

          <NSpace class="mt-16px">
            <NButton
              type="primary"
              :loading="saving"
              :disabled="!selectedTenantId"
              @click="handleSave"
            >
              保存配置
            </NButton>
          </NSpace>
        </NForm>
      </NSpin>
    </NCard>
  </div>
</template>
