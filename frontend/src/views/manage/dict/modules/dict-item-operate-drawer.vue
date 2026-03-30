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
  NRadio,
  NRadioGroup,
  NSelect,
  useMessage
} from 'naive-ui';
import { enableStatusOptions } from '@/constants/business';
import { fetchCreateDictItem, fetchUpdateDictItem } from '@/service/api';
import { $t } from '@/locales';

export type OperateType = NaiveUI.TableOperateType | 'addChild';

interface Props {
  visible: boolean;
  operateType: OperateType;
  rowData?: Api.SystemManage.DictItem | null;
  dictId?: number;
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
  value: { required: true, message: $t('form.required'), trigger: 'blur' },
  label: { required: true, message: $t('form.required'), trigger: 'blur' }
};

const defaultFormValue: Api.SystemManage.DictItemCreate = {
  dict_id: 0,
  value: '',
  label: '',
  description: '',
  ext_info: '',
  status: '1',
  sort: 0
};

const form = reactive<Api.SystemManage.DictItemCreate>({ ...defaultFormValue });

const drawerTitle = computed(() => {
  return props.operateType === 'add' ? $t('page.manage.dict.addDictItem') : $t('page.manage.dict.editDictItem');
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
      } else {
        Object.assign(form, {
          ...defaultFormValue,
          dict_id: props.dictId || 0
        });
      }
    }
  }
);

async function handleSubmit() {
  try {
    await formRef.value?.validate();
    if (props.operateType === 'add') {
      await fetchCreateDictItem(form);
      message.success($t('common.addSuccess'));
    } else if (props.operateType === 'edit' && props.rowData) {
      await fetchUpdateDictItem(props.rowData.id, form);
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
          <NFormItemGi :span="24" :label="$t('page.manage.dict.itemValue')" path="value">
            <NInput v-model:value="form.value" :placeholder="$t('page.manage.dict.form.itemValue')" />
          </NFormItemGi>
          <NFormItemGi :span="24" :label="$t('page.manage.dict.itemLabel')" path="label">
            <NInput v-model:value="form.label" :placeholder="$t('page.manage.dict.form.itemLabel')" />
          </NFormItemGi>
          <NFormItemGi :span="24" :label="$t('page.manage.dict.itemDesc')">
            <NInput
              v-model:value="form.description"
              :placeholder="$t('page.manage.dict.form.itemDesc')"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 5 }"
            />
          </NFormItemGi>
          <NFormItemGi :span="24" :label="$t('page.manage.dict.form.extInfo')">
            <NInput
              v-model:value="form.ext_info"
              :placeholder="$t('page.manage.dict.form.extInfo')"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 5 }"
            />
          </NFormItemGi>
          <NFormItemGi :span="12" :label="$t('page.manage.dict.itemStatus')">
            <NRadioGroup v-model:value="form.status">
              <NRadio v-for="item in enableStatusOptions" :key="item.value" :value="item.value" :label="item.label" />
            </NRadioGroup>
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
