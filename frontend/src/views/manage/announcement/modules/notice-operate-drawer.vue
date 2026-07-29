<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { fetchCreateNotice, fetchUpdateNotice } from '@/service/api';
import { useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({
  name: 'NoticeOperateDrawer'
});

interface Props {
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.Notification.Notice | null;
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

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: '新增通知',
    edit: '编辑通知'
  };
  return titles[props.operateType];
});

const model = ref(createDefaultModel());

function createDefaultModel(): Api.Notification.NoticeCreate {
  return {
    title: '',
    content: '',
    type: 'system',
    target_type: 'all',
    target_role_ids: undefined,
    target_user_ids: undefined,
    priority: 'normal'
  };
}

const rules = {
  title: { required: true, message: '请输入通知标题', trigger: 'blur' },
  content: { required: true, message: '请输入通知内容', trigger: 'blur' },
  type: { required: true, message: '请选择通知类型', trigger: 'change' },
  target_type: { required: true, message: '请选择推送范围', trigger: 'change' },
  priority: { required: true, message: '请选择优先级', trigger: 'change' }
};

const noticeId = computed(() => props.rowData?.id || -1);
const isEdit = computed(() => props.operateType === 'edit');

function handleInitModel() {
  model.value = createDefaultModel();

  if (props.operateType === 'edit' && props.rowData) {
    const clonedData = jsonClone(props.rowData);
    model.value.title = clonedData.title || '';
    model.value.content = clonedData.content || '';
    model.value.type = clonedData.type || 'system';
    model.value.target_type = clonedData.target_type || 'all';
    model.value.target_role_ids = clonedData.target_role_ids || undefined;
    model.value.target_user_ids = clonedData.target_user_ids || undefined;
    model.value.priority = clonedData.priority || 'normal';
  }
}

function closeDrawer() {
  visible.value = false;
}

async function handleSubmit() {
  await validate();

  let error: unknown = null;

  if (isEdit.value) {
    const result = await fetchUpdateNotice(noticeId.value, model.value);
    error = result.error;
  } else {
    const result = await fetchCreateNotice(model.value);
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
  <NDrawer v-model:show="visible" display-directive="show" :width="560">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="model" :rules="rules">
        <NFormItem label="通知标题" path="title">
          <NInput v-model:value="model.title" placeholder="请输入通知标题" maxlength="200" show-count />
        </NFormItem>
        <NFormItem label="通知内容" path="content">
          <NInput v-model:value="model.content" type="textarea" placeholder="请输入通知内容" :rows="6" />
        </NFormItem>
        <NFormItem label="通知类型" path="type">
          <NRadioGroup v-model:value="model.type">
            <NRadio value="announcement">公告</NRadio>
            <NRadio value="system">系统</NRadio>
            <NRadio value="operation">操作提醒</NRadio>
            <NRadio value="approval">审批通知</NRadio>
          </NRadioGroup>
        </NFormItem>
        <NFormItem label="推送范围" path="target_type">
          <NRadioGroup v-model:value="model.target_type">
            <NRadio value="all">全员广播</NRadio>
            <NRadio value="role">按角色</NRadio>
            <NRadio value="user">按指定用户</NRadio>
          </NRadioGroup>
        </NFormItem>
        <NFormItem
          v-if="model.target_type === 'role'"
          label="目标角色"
          path="target_role_ids"
          :rule="{ required: true, message: '请输入角色ID', type: 'array', trigger: 'change' }"
        >
          <NSelect
            v-model:value="model.target_role_ids"
            multiple
            placeholder="请输入角色ID（多选）"
            :options="[]"
            tag
            filterable
          />
        </NFormItem>
        <NFormItem
          v-if="model.target_type === 'user'"
          label="目标用户"
          path="target_user_ids"
          :rule="{ required: true, message: '请输入用户ID', type: 'array', trigger: 'change' }"
        >
          <NSelect
            v-model:value="model.target_user_ids"
            multiple
            placeholder="请输入用户ID（多选）"
            :options="[]"
            tag
            filterable
          />
        </NFormItem>
        <NFormItem label="优先级" path="priority">
          <NRadioGroup v-model:value="model.priority">
            <NRadio value="low">低</NRadio>
            <NRadio value="normal">普通</NRadio>
            <NRadio value="high">高</NRadio>
            <NRadio value="urgent">紧急</NRadio>
          </NRadioGroup>
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
