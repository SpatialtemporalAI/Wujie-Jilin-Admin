<script setup lang="tsx">
import { computed, reactive, watch, ref } from 'vue';
import { useVModel } from '@vueuse/core';
import {
  NButton,
  NDrawer,
  NDrawerContent,
  NForm,
  NFormItem,
  NFormItemGi,
  NGrid,
  NInput,
  NSelect,
  NSwitch,
  useMessage
} from 'naive-ui';
import { yesOrNoOptions } from '@/constants/business';
import { fetchCreateConfig, fetchUpdateConfig } from '@/service/api';
import { $t } from '@/locales';

export type OperateType = NaiveUI.TableOperateType | 'addChild';

interface Props {
  visible: boolean;
  operateType: OperateType;
  rowData?: Api.SystemManage.Config | null;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  'update:visible': [visible: boolean];
  submitted: [];
}>();

const message = useMessage();
const visible = useVModel(props, 'visible');

const formRef = ref();
const formRules = {
  key: { required: true, message: $t('form.required'), trigger: 'blur' },
  value: { required: true, message: $t('form.required'), trigger: 'blur' }
};

/** 配置类型选项 */
const configTypeOptions = [
  { label: $t('page.manage.config.type.string'), value: 'string' },
  { label: $t('page.manage.config.type.number'), value: 'number' },
  { label: $t('page.manage.config.type.boolean'), value: 'boolean' },
  { label: $t('page.manage.config.type.json'), value: 'json' },
  { label: $t('page.manage.config.type.array'), value: 'array' }
];

/** 配置分组选项 */
const configGroupOptions = [
  { label: $t('page.manage.config.group.system'), value: 'system' },
  { label: $t('page.manage.config.group.security'), value: 'security' },
  { label: $t('page.manage.config.group.log'), value: 'log' },
  { label: $t('page.manage.config.group.network'), value: 'network' },
  { label: $t('page.manage.config.group.storage'), value: 'storage' },
  { label: $t('page.manage.config.group.custom'), value: 'custom' }
];

const defaultFormValue: Api.SystemManage.ConfigCreate = {
  key: '',
  value: '',
  default_value: '',
  validation_rule: '',
  description: '',
  type: 'string',
  group: 'system',
  editable: '1',
  is_system: '2',
  required: '2'
};

const form = reactive<Api.SystemManage.ConfigCreate>({ ...defaultFormValue });

const drawerTitle = computed(() => {
  return props.operateType === 'add' ? $t('page.manage.config.addConfig') : $t('page.manage.config.editConfig');
});

watch(
  () => props.visible,
  val => {
    if (val) {
      if (props.operateType === 'edit' && props.rowData) {
        Object.assign(form, props.rowData);
      } else {
        Object.assign(form, defaultFormValue);
      }
    }
  }
);

async function handleSubmit() {
  try {
    await formRef.value?.validate();
    if (props.operateType === 'add') {
      await fetchCreateConfig(form);
      message.success($t('common.addSuccess'));
    } else if (props.operateType === 'edit' && props.rowData) {
      await fetchUpdateConfig(props.rowData.id, form);
      message.success($t('common.updateSuccess'));
    }
    emit('submitted');
    visible.value = false;
  } catch (error) {
    console.error('提交失败:', error);
  }
}
</script>

<template>
  <NDrawer v-model:show="visible" :width="560" preset="card">
    <NDrawerContent :title="drawerTitle" :native-scrollbar="false">
      <NForm ref="formRef" :model="form" :rules="formRules" label-placement="left" label-width="auto" size="small">
        <NGrid :x-gap="16" :cols="24">
          <NFormItemGi :span="24" :label="$t('page.manage.config.configKey')" path="key">
            <NInput v-model:value="form.key" :placeholder="$t('page.manage.config.form.configKey')" />
          </NFormItemGi>
          <NFormItemGi :span="24" :label="$t('page.manage.config.configValue')" path="value">
            <NInput v-model:value="form.value" :placeholder="$t('page.manage.config.form.configValue')" type="textarea"
              :autosize="{ minRows: 2, maxRows: 4 }" />
          </NFormItemGi>
          <NFormItemGi :span="24" :label="$t('page.manage.config.defaultValue')">
            <NInput v-model:value="form.default_value" :placeholder="$t('page.manage.config.form.defaultValue')" />
          </NFormItemGi>
          <NFormItemGi :span="24" :label="$t('page.manage.config.configDesc')">
            <NInput v-model:value="form.description" :placeholder="$t('page.manage.config.form.configDesc')"
              type="textarea" :autosize="{ minRows: 2, maxRows: 3 }" />
          </NFormItemGi>
          <NFormItemGi :span="12" :label="$t('page.manage.config.configType')">
            <NSelect v-model:value="form.type" :options="configTypeOptions"
              :placeholder="$t('page.manage.config.form.configType')" />
          </NFormItemGi>
          <NFormItemGi :span="12" :label="$t('page.manage.config.configGroup')">
            <NSelect v-model:value="form.group" :options="configGroupOptions"
              :placeholder="$t('page.manage.config.form.configGroup')" />
          </NFormItemGi>
          <NFormItemGi :span="12" :label="$t('page.manage.config.validationRule')">
            <NInput v-model:value="form.validation_rule" :placeholder="$t('page.manage.config.form.validationRule')" />
          </NFormItemGi>
          <NFormItemGi :span="12" :label="$t('page.manage.config.editable')">
            <NSelect v-model:value="form.editable" :options="yesOrNoOptions"
              :placeholder="$t('page.manage.config.form.editable')" />
          </NFormItemGi>
          <NFormItemGi :span="12" :label="$t('page.manage.config.isSystem')">
            <NSelect v-model:value="form.is_system" :options="yesOrNoOptions"
              :placeholder="$t('page.manage.config.form.isSystem')" />
          </NFormItemGi>
          <NFormItemGi :span="12" :label="$t('page.manage.config.required')">
            <NSelect v-model:value="form.required" :options="yesOrNoOptions"
              :placeholder="$t('page.manage.config.form.required')" />
          </NFormItemGi>
        </NGrid>
      </NForm>
      <template #footer>
        <div class="flex-justify-end gap-12px">
          <NButton size="small" @click="visible = false">
            {{ $t('common.cancel') }}
          </NButton>
          <NButton type="primary" size="small" @click="handleSubmit">
            {{ $t('common.confirm') }}
          </NButton>
        </div>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped></style>
