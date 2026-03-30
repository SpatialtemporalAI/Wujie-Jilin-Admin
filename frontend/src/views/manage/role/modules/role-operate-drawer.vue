<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { useBoolean } from '@sa/hooks';
import { enableStatusOptions } from '@/constants/business';
import { fetchCreateRole, fetchUpdateRole } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import MenuAuthModal from './menu-auth-modal.vue';
import ButtonAuthModal from './button-auth-modal.vue';

defineOptions({
  name: 'RoleOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.SystemManage.Role | null;
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
const { bool: menuAuthVisible, setTrue: openMenuAuthModal } = useBoolean();
const { bool: buttonAuthVisible, setTrue: openButtonAuthModal } = useBoolean();

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: $t('page.manage.role.addRole'),
    edit: $t('page.manage.role.editRole')
  };
  return titles[props.operateType];
});

type Model = Pick<Api.SystemManage.Role, 'name' | 'code' | 'desc' | 'status'>;

const model = ref(createDefaultModel());

function createDefaultModel(): Model {
  return {
    name: '',
    code: '',
    desc: '',
    status: '1'
  };
}

type RuleKey = Exclude<keyof Model, 'desc'>;

const rules: Record<RuleKey, App.Global.FormRule> = {
  name: defaultRequiredRule,
  code: defaultRequiredRule,
  status: defaultRequiredRule
};

const roleId = computed(() => props.rowData?.id || -1);

const isEdit = computed(() => props.operateType === 'edit');

function handleInitModel() {
  model.value = createDefaultModel();

  if (props.operateType === 'edit' && props.rowData) {
    const clonedData = jsonClone(props.rowData);
    // 确保 status 字段格式正确

    // 将 rowData 的字段映射到 model 的字段
    model.value.name = clonedData.name || '';
    model.value.code = clonedData.code || '';
    model.value.desc = clonedData.desc || '';
    model.value.status = clonedData.status;
  }
}

function closeDrawer() {
  visible.value = false;
}

async function handleSubmit() {
  await validate();

  let error: any = null;

  if (isEdit.value) {
    const result = await fetchUpdateRole(roleId.value, model.value);
    error = result.error;
  } else {
    const result = await fetchCreateRole(model.value);
    error = result.error;
  }

  if (!error) {
    window.$message?.success(isEdit.value ? $t('common.updateSuccess') : $t('common.addSuccess'));
    closeDrawer();
    emit('submitted');
  }
}

watch(visible, () => {
  if (visible.value) {
    handleInitModel();
    restoreValidation();
  }
});
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="360">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="model" :rules="rules">
        <NFormItem :label="$t('page.manage.role.roleName')" path="roleName">
          <NInput v-model:value="model.name" :placeholder="$t('page.manage.role.form.roleName')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.role.roleCode')" path="roleCode">
          <NInput v-model:value="model.code" :placeholder="$t('page.manage.role.form.roleCode')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.role.roleStatus')" path="status">
          <NRadioGroup v-model:value="model.status">
            <NRadio v-for="item in enableStatusOptions" :key="item.value" :value="item.value" :label="$t(item.label)" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.manage.role.roleDesc')" path="desc">
          <NInput v-model:value="model.desc" :placeholder="$t('page.manage.role.form.roleDesc')" />
        </NFormItem>
      </NForm>
      <NSpace v-if="isEdit">
        <NButton @click="openMenuAuthModal">{{ $t('page.manage.role.menuAuth') }}</NButton>
        <MenuAuthModal v-model:visible="menuAuthVisible" :role-id="roleId" />
        <NButton @click="openButtonAuthModal">{{ $t('page.manage.role.buttonAuth') }}</NButton>
        <ButtonAuthModal v-model:visible="buttonAuthVisible" :role-id="roleId" />
      </NSpace>
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
