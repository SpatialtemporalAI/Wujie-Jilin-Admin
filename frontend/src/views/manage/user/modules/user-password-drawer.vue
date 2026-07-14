<script setup lang="ts">
import { ref } from 'vue';
import { fetchChangeUserPassword } from '@/service/api/system-manage';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

interface Props {
  /** 用户ID */
  userId: number;
}

const props = defineProps<Props>();

interface Emits {
  (e: 'submitted'): void;
}

const emit = defineEmits<Emits>();

const visible = defineModel<boolean>('visible', {
  default: false
});

const { formRef, validate, restoreValidation } = useNaiveForm();
const { defaultRequiredRule } = useFormRules();

const title = $t('page.manage.user.changePassword');

type Model = {
  newPassword: string;
  confirmPassword: string;
};

const model = ref<Model>({
  newPassword: '',
  confirmPassword: ''
});

const rules: Record<keyof Model, App.Global.FormRule[]> = {
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

function closeDrawer() {
  visible.value = false;
  model.value = {
    newPassword: '',
    confirmPassword: ''
  };
}

async function handleSubmit() {
  await validate();

  try {
    // 调用修改密码的API
    const { error, data } = await fetchChangeUserPassword(props.userId, model.value.newPassword);

    if (!error) {
      window.$message?.success($t('common.updateSuccess'));
      closeDrawer();
      emit('submitted');
    } else {
      window.$message?.error(error.message || $t('common.updateFailed'));
    }
  } catch (error) {
    window.$message?.error($t('common.updateFailed'));
  }
}
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="360">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="model" :rules="rules">
        <NFormItem :label="$t('page.manage.user.form.newPassword')" path="newPassword">
          <NInput
            v-model:value="model.newPassword"
            type="password"
            :maxlength="20"
            :placeholder="$t('page.manage.user.form.newPassword')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.manage.user.form.confirmPassword')" path="confirmPassword">
          <NInput
            v-model:value="model.confirmPassword"
            type="password"
            :maxlength="20"
            :placeholder="$t('page.manage.user.form.confirmPassword')"
          />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace :size="16">
          <NButton @click="closeDrawer">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped></style>
