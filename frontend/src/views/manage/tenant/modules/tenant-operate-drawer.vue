<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { NInput, NInputNumber } from 'naive-ui';
import { fetchCreateTenant, fetchUpdateTenant, fetchGetTenant } from '@/plugins/multi_tenant/api/tenant';
import { $t } from '@/locales';

interface Props {
  visible: boolean;
  operateType: 'add' | 'edit';
  rowData?: Api.SystemManage.Role | null;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void;
  (e: 'submitted'): void;
}>();

const formRef = ref();
const loading = ref(false);

const formData = ref({
  name: '',
  code: '',
  description: null as string | null,
  contact_name: null as string | null,
  contact_email: null as string | null,
  contact_phone: null as string | null,
  max_users: 100
});

const rules = {
  name: [{ required: true, message: $t('page.manage.tenant.form.tenantName'), trigger: 'blur' }],
  code: [
    { required: true, message: $t('page.manage.tenant.form.tenantCode'), trigger: 'blur' },
    { pattern: /^[a-z0-9_-]+$/, message: $t('page.manage.tenant.form.tenantCodeRule'), trigger: 'blur' }
  ]
};

const title = computed(() =>
  props.operateType === 'add' ? $t('page.manage.tenant.addTenant') : $t('page.manage.tenant.editTenant')
);

watch(
  () => props.visible,
  async val => {
    if (val && props.operateType === 'edit' && props.rowData) {
      const { data } = await fetchGetTenant(props.rowData.id);
      if (data) {
        formData.value = { ...formData.value, ...data };
      }
    } else if (val) {
      formData.value = {
        name: '',
        code: '',
        description: null,
        contact_name: null,
        contact_email: null,
        contact_phone: null,
        max_users: 100
      };
    }
  }
);

function handleClose() {
  emit('update:visible', false);
}

async function handleSubmit() {
  await formRef.value?.validate();
  loading.value = true;
  try {
    if (props.operateType === 'add') {
      const { error } = await fetchCreateTenant(formData.value);
      if (!error) {
        window.$message?.success($t('page.manage.tenant.createSuccess'));
        emit('submitted');
        handleClose();
      }
    } else if (props.rowData) {
      const { error } = await fetchUpdateTenant(props.rowData.id, formData.value);
      if (!error) {
        window.$message?.success($t('page.manage.tenant.updateSuccess'));
        emit('submitted');
        handleClose();
      }
    }
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <NDrawer :show="visible" :width="480" @update:show="handleClose">
    <NDrawerContent :title="title" closable>
      <NForm ref="formRef" :model="formData" :rules="rules" label-placement="top">
        <NFormItem :label="$t('page.manage.tenant.tenantName')" path="name">
          <NInput v-model:value="formData.name" :placeholder="$t('page.manage.tenant.form.tenantName')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.tenant.tenantCode')" path="code">
          <NInput v-model:value="formData.code" :placeholder="$t('page.manage.tenant.form.tenantCodePlaceholder')" :disabled="operateType === 'edit'" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.tenant.description')">
          <NInput v-model:value="formData.description" type="textarea" :placeholder="$t('page.manage.tenant.form.description')" :rows="3" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.tenant.contactName')">
          <NInput v-model:value="formData.contact_name" :placeholder="$t('page.manage.tenant.form.contactName')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.tenant.contactEmail')">
          <NInput v-model:value="formData.contact_email" :placeholder="$t('page.manage.tenant.form.contactEmail')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.tenant.contactPhone')">
          <NInput v-model:value="formData.contact_phone" :placeholder="$t('page.manage.tenant.form.contactPhone')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.tenant.maxUsersLabel')">
          <NInputNumber v-model:value="formData.max_users" :min="1" :max="99999" class="w-full" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace>
          <NButton @click="handleClose">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" :loading="loading" @click="handleSubmit">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>
