<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { enableStatusOptions } from '@/constants/business';
import { fetchCreateMerchant, fetchGetMerchant, fetchGetRobotList, fetchUpdateMerchant } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { booleanToEnableStatus } from '@/utils/status';

defineOptions({
  name: 'MerchantOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Merchant.Merchant | null;
}

const props = defineProps<Props>();

interface Emits {
  (e: 'submitted'): void;
  (e: 'created', cred: Api.Merchant.ApiCredentials): void;
}

const emit = defineEmits<Emits>();

const visible = defineModel<boolean>('visible', {
  default: false
});

const { formRef, validate, restoreValidation } = useNaiveForm();
const { defaultRequiredRule } = useFormRules();

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: $t('page.manage.merchant.addMerchant'),
    edit: $t('page.manage.merchant.editMerchant')
  };
  return titles[props.operateType];
});

interface Model {
  name: string;
  code: string;
  contact_name: string;
  contact_phone: string;
  contact_email: string;
  status: Api.Common.EnableStatus;
  remark: string;
  robot_ids: number[];
}

const model = ref<Model>(createDefaultModel());

function createDefaultModel(): Model {
  return {
    name: '',
    code: '',
    contact_name: '',
    contact_phone: '',
    contact_email: '',
    status: '1',
    remark: '',
    robot_ids: []
  };
}

type RuleKey = Extract<keyof Model, 'name' | 'code' | 'status'>;

const rules: Record<RuleKey, App.Global.FormRule> = {
  name: defaultRequiredRule,
  code: defaultRequiredRule,
  status: defaultRequiredRule
};

const merchantId = computed(() => props.rowData?.id || -1);
const isEdit = computed(() => props.operateType === 'edit');

// 可绑定机器人选项
const robotOptions = ref<{ label: string; value: number }[]>([]);

async function loadRobotOptions() {
  const { error, data } = await fetchGetRobotList({ page: 1, page_size: 1000 });
  if (!error && data) {
    robotOptions.value = data.records.map(r => ({
      label: `${r.name}（${r.serial_number}）`,
      value: r.id
    }));
  }
}

async function loadDetail() {
  if (isEdit.value && merchantId.value > 0) {
    const { error, data } = await fetchGetMerchant(merchantId.value);
    if (!error && data) {
      model.value.robot_ids = data.robot_ids || [];
    }
  } else {
    model.value.robot_ids = [];
  }
}

function handleInitModel() {
  model.value = createDefaultModel();

  if (props.operateType === 'edit' && props.rowData) {
    const clonedData = jsonClone(props.rowData);
    model.value.name = clonedData.name || '';
    model.value.code = clonedData.code || '';
    model.value.contact_name = clonedData.contact_name || '';
    model.value.contact_phone = clonedData.contact_phone || '';
    model.value.contact_email = clonedData.contact_email || '';
    model.value.status = booleanToEnableStatus(clonedData.status);
    model.value.remark = clonedData.remark || '';
  }
}

function closeDrawer() {
  visible.value = false;
}

async function handleSubmit() {
  await validate();

  const submitData: Api.Merchant.MerchantCreate = {
    name: model.value.name,
    code: model.value.code,
    contact_name: model.value.contact_name || undefined,
    contact_phone: model.value.contact_phone || undefined,
    contact_email: model.value.contact_email || undefined,
    status: model.value.status,
    remark: model.value.remark || undefined,
    robot_ids: model.value.robot_ids
  };

  if (isEdit.value) {
    const { error } = await fetchUpdateMerchant(merchantId.value, submitData);
    if (!error) {
      window.$message?.success($t('common.updateSuccess'));
      closeDrawer();
      emit('submitted');
    }
  } else {
    const { error, data } = await fetchCreateMerchant(submitData);
    if (!error && data) {
      window.$message?.success($t('common.addSuccess'));
      closeDrawer();
      emit('created', data);
    }
  }
}

watch(visible, async () => {
  if (visible.value) {
    handleInitModel();
    restoreValidation();
    await loadRobotOptions();
    await loadDetail();
  }
});
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="420">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="model" :rules="rules" label-placement="left" :label-width="90">
        <NFormItem :label="$t('page.manage.merchant.merchantName')" path="name">
          <NInput v-model:value="model.name" :placeholder="$t('page.manage.merchant.form.merchantName')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.merchant.merchantCode')" path="code">
          <NInput v-model:value="model.code" :placeholder="$t('page.manage.merchant.form.merchantCode')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.merchant.merchantStatus')" path="status">
          <NRadioGroup v-model:value="model.status">
            <NRadio v-for="item in enableStatusOptions" :key="item.value" :value="item.value" :label="item.label" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.manage.merchant.contactName')" path="contact_name">
          <NInput v-model:value="model.contact_name" :placeholder="$t('page.manage.merchant.form.contactName')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.merchant.contactPhone')" path="contact_phone">
          <NInput v-model:value="model.contact_phone" :placeholder="$t('page.manage.merchant.form.contactPhone')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.merchant.contactEmail')" path="contact_email">
          <NInput v-model:value="model.contact_email" :placeholder="$t('page.manage.merchant.form.contactEmail')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.merchant.bindRobot')" path="robot_ids">
          <NSelect
            v-model:value="model.robot_ids"
            multiple
            filterable
            :placeholder="$t('page.manage.merchant.form.bindRobot')"
            :options="robotOptions"
          />
        </NFormItem>
        <NFormItem :label="$t('page.manage.merchant.remark')" path="remark">
          <NInput v-model:value="model.remark" type="textarea" :placeholder="$t('page.manage.merchant.form.remark')" />
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
