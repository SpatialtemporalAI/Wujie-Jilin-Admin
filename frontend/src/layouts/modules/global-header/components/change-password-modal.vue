<script setup lang="ts">
import { ref } from 'vue';
import { fetchChangeOwnPassword } from '@/service/api/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({
  name: 'ChangePasswordModal'
});

const authStore = useAuthStore();

const visible = defineModel<boolean>('visible', {
  default: false
});

const { formRef, validate, restoreValidation } = useNaiveForm();
const { defaultRequiredRule } = useFormRules();

type Model = {
  oldPassword: string;
  newPassword: string;
  confirmPassword: string;
};

const model = ref<Model>({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
});

const rules: Record<keyof Model, App.Global.FormRule[]> = {
  oldPassword: [defaultRequiredRule],
  newPassword: [
    defaultRequiredRule,
    {
      min: 6,
      max: 20,
      trigger: 'blur',
      message: $t('page.manage.user.form.passwordLength')
    }
  ],
  confirmPassword: [
    defaultRequiredRule,
    {
      validator: (rule, value) => {
        if (value !== model.value.newPassword) {
          return new Error($t('page.manage.user.form.passwordNotMatch'));
        }
        return true;
      },
      trigger: 'blur'
    }
  ]
};

function closeModal() {
  visible.value = false;
  model.value = {
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  };
  restoreValidation();
}

async function handleSubmit() {
  await validate();

  const { error } = await fetchChangeOwnPassword(model.value.oldPassword, model.value.newPassword);

  if (!error) {
    window.$message?.success($t('common.updateSuccess'));
    closeModal();
    // 密码已修改，强制重新登录
    authStore.resetStore();
  }
}
</script>

<template>
  <NModal
    v-model:show="visible"
    preset="card"
    :title="$t('common.changePassword')"
    style="width: 420px; max-width: 90vw"
    :bordered="false"
    @after-leave="closeModal"
  >
    <NForm ref="formRef" :model="model" :rules="rules">
      <NFormItem :label="$t('page.manage.user.form.oldPassword')" path="oldPassword">
        <NInput
          v-model:value="model.oldPassword"
          type="password"
          show-password-on="click"
          :maxlength="20"
          :placeholder="$t('page.manage.user.form.oldPassword')"
        />
      </NFormItem>
      <NFormItem :label="$t('page.manage.user.form.newPassword')" path="newPassword">
        <NInput
          v-model:value="model.newPassword"
          type="password"
          show-password-on="click"
          :maxlength="20"
          :placeholder="$t('page.manage.user.form.newPassword')"
        />
      </NFormItem>
      <NFormItem :label="$t('page.manage.user.form.confirmPassword')" path="confirmPassword">
        <NInput
          v-model:value="model.confirmPassword"
          type="password"
          show-password-on="click"
          :maxlength="20"
          :placeholder="$t('page.manage.user.form.confirmPassword')"
        />
      </NFormItem>
    </NForm>
    <template #footer>
      <NSpace :size="16" justify="end">
        <NButton @click="closeModal">{{ $t('common.cancel') }}</NButton>
        <NButton type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<style scoped></style>
