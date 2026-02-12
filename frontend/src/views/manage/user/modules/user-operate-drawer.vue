<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { enableStatusOptions, userGenderOptions } from '@/constants/business';
import { fetchGetAllRoles, fetchCreateUser, fetchUpdateUser } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({
  name: 'UserOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.SystemManage.User | null;
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

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: $t('page.manage.user.addUser'),
    edit: $t('page.manage.user.editUser')
  };
  return titles[props.operateType];
});

type Model = Pick<
  Api.SystemManage.User,
  'username' | 'nickname' | 'phone' | 'email' | 'userRoles' | 'status'
> & {
  password: string;
  confirmPassword: string;
};

const model = ref(createDefaultModel());

function createDefaultModel(): Model {
  return {
    username: '',
    nickname: '',
    phone: '',
    email: '',
    password: '',
    confirmPassword: '',
    userRoles: [],
    status: '1'
  };
}

type RuleKey = Extract<keyof Model, 'username' | 'status' | 'password' | 'confirmPassword'>;

const rules: Record<RuleKey, App.Global.FormRule> = {
  username: defaultRequiredRule,
  status: defaultRequiredRule,
  password: {
    required: props.operateType === 'add',
    message: $t('form.required'),
    trigger: ['input', 'blur']
  },
  confirmPassword: {
    required: props.operateType === 'add',
    message: $t('form.required'),
    trigger: ['input', 'blur'],
    validator: (rule, value) => {
      if (model.value.password !== value) {
        return new Error($t('page.manage.user.form.passwordNotMatch'));
      }
      return true;
    }
  }
};

/** the enabled role options */
const roleOptions = ref<CommonType.Option<string>[]>([]);

async function getRoleOptions() {
  const { error, data } = await fetchGetAllRoles();

  if (!error) {
    const options = data.map(item => ({
      label: item.roleName,
      value: item.roleCode
    }));

    // the mock data does not have the roleCode, so fill it
    // if the real request, remove the following code
    const userRoleOptions = model.value.userRoles.map(item => ({
      label: item,
      value: item
    }));
    // end

    roleOptions.value = [...userRoleOptions, ...options];
  }
}

function handleInitModel() {
  model.value = createDefaultModel();

  if (props.operateType === 'edit' && props.rowData) {
    Object.assign(model.value, jsonClone(props.rowData));
  }
}

function closeDrawer() {
  visible.value = false;
}

async function handleSubmit() {
  await validate();

  try {
    if (props.operateType === 'add') {
      // 创建用户
      await fetchCreateUser({
        username: model.value.username,
        nickname: model.value.nickname,
        phone: model.value.phone,
        email: model.value.email,
        password: model.value.password,
        status: model.value.status,
        userRoles: model.value.userRoles
      });
      window.$message?.success($t('common.addSuccess'));
    } else if (props.operateType === 'edit' && props.rowData) {
      // 更新用户
      await fetchUpdateUser(props.rowData.id, {
        username: model.value.username,
        nickname: model.value.nickname,
        phone: model.value.phone,
        email: model.value.email,
        status: model.value.status,
        userRoles: model.value.userRoles
      });
      window.$message?.success($t('common.updateSuccess'));
    }
    closeDrawer();
    emit('submitted');
  } catch (error) {
    window.$message?.error($t('request.error'));
    console.error('Failed to save user:', error);
  }
}

watch(visible, () => {
  if (visible.value) {
    handleInitModel();
    restoreValidation();
    getRoleOptions();
  }
});
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="360">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="model" :rules="rules">
        <NFormItem :label="$t('page.manage.user.userName')" path="username">
          <NInput v-model:value="model.username" :placeholder="$t('page.manage.user.form.userName')" />
        </NFormItem>
        <NFormItem v-if="props.operateType === 'add'" :label="$t('page.manage.user.password')" path="password">
          <NInput v-model:value="model.password" type="password"
            :placeholder="$t('page.manage.user.form.newPassword')" />
        </NFormItem>
        <NFormItem v-if="props.operateType === 'add'" :label="$t('page.manage.user.confirmPassword')"
          path="confirmPassword">
          <NInput v-model:value="model.confirmPassword" type="password"
            :placeholder="$t('page.manage.user.form.confirmPassword')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.user.nickName')" path="nickname">
          <NInput v-model:value="model.nickname" :placeholder="$t('page.manage.user.form.nickName')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.user.userPhone')" path="phone">
          <NInput v-model:value="model.phone" :placeholder="$t('page.manage.user.form.userPhone')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.user.userEmail')" path="email">
          <NInput v-model:value="model.email" :placeholder="$t('page.manage.user.form.userEmail')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.user.userStatus')" path="status">
          <NRadioGroup v-model:value="model.status">
            <NRadio v-for="item in enableStatusOptions" :key="item.value" :value="item.value" :label="$t(item.label)" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.manage.user.userRole')" path="userRoles">
          <NSelect v-model:value="model.userRoles" multiple :options="roleOptions"
            :placeholder="$t('page.manage.user.form.userRole')" />
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
