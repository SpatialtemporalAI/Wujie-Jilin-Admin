<script setup lang="tsx">
import { computed, reactive, ref, watch } from 'vue';
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
  NInputNumber,
  NSelect,
  NSwitch,
  useMessage
} from 'naive-ui';
import { enableStatusOptions, yesOrNoOptions } from '@/constants/business';
import { fetchCreateDict, fetchUpdateDict } from '@/service/api';
import { $t } from '@/locales';

interface Props {
  visible: boolean;
  operateType: Api.OperateType;
  rowData?: Api.SystemManage.Dict | null;
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
  name: { required: true, message: $t('form.required'), trigger: 'blur' },
  code: { required: true, message: $t('form.required'), trigger: 'blur' }
};

const defaultFormValue: Api.SystemManage.DictCreate = {
  name: '',
  code: '',
  description: '',
  status: '1',
  is_system: '2',
  sort: 0
};

const form = reactive<Api.SystemManage.DictCreate>({ ...defaultFormValue });

const drawerTitle = computed(() => {
  return props.operateType === 'add' ? $t('page.manage.dict.addDict') : $t('page.manage.dict.editDict');
});

watch(
  () => props.visible,
  val => {
    if (val) {
      if (props.operateType === 'edit' && props.rowData) {
        Object.assign(form, props.rowData);
        // Normalize backend boolean fields to frontend enum string fields.
        if (typeof props.rowData.status === 'boolean') {
          form.status = props.rowData.status ? '1' : '2';
        }
        if (typeof props.rowData.is_system === 'boolean') {
          form.is_system = props.rowData.is_system ? '1' : '2';
        }
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
      await fetchCreateDict(form);
      message.success($t('common.addSuccess'));
    } else if (props.operateType === 'edit' && props.rowData) {
      await fetchUpdateDict(props.rowData.id, form);
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
  <NDrawer v-model:show="visible" :width="480" preset="card">
    <NDrawerContent :title="drawerTitle" :native-scrollbar="false">
      <NForm ref="formRef" :model="form" :rules="formRules" label-placement="left" label-width="auto" size="small">
        <NGrid :x-gap="16" :cols="24">
          <NFormItemGi :span="24" :label="$t('page.manage.dict.dictName')" path="name">
            <NInput v-model:value="form.name" :placeholder="$t('page.manage.dict.form.dictName')" />
          </NFormItemGi>
          <NFormItemGi :span="24" :label="$t('page.manage.dict.dictCode')" path="code">
            <NInput v-model:value="form.code" :placeholder="$t('page.manage.dict.form.dictCode')" />
          </NFormItemGi>
          <NFormItemGi :span="24" :label="$t('page.manage.dict.dictDesc')">
            <NInput
              v-model:value="form.description"
              :placeholder="$t('page.manage.dict.form.dictDesc')"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 5 }"
            />
          </NFormItemGi>
          <NFormItemGi :span="12" :label="$t('page.manage.dict.dictStatus')">
            <NSelect
              v-model:value="form.status"
              :options="enableStatusOptions"
              :placeholder="$t('page.manage.dict.form.dictStatus')"
            />
          </NFormItemGi>
          <NFormItemGi :span="12" :label="$t('page.manage.dict.isSystem')">
            <NSelect
              v-model:value="form.is_system"
              :options="yesOrNoOptions"
              :placeholder="$t('page.manage.dict.form.isSystem')"
              clearable
            />
          </NFormItemGi>
          <NFormItemGi :span="12" :label="$t('page.manage.dict.sort')">
            <NInputNumber
              v-model:value="form.sort"
              :placeholder="$t('page.manage.dict.form.sort')"
              style="width: 100%"
            />
          </NFormItemGi>
        </NGrid>
      </NForm>
      <template #footer>
        <div class="gap-12px flex-justify-end">
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
