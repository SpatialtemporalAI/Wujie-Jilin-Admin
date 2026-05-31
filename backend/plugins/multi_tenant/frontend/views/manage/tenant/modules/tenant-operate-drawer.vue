<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { NInput, NInputNumber, NSelect } from 'naive-ui';
import { fetchCreateTenant, fetchUpdateTenant, fetchGetTenant } from '@/plugins/multi_tenant/api/tenant';

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
  name: [{ required: true, message: '请输入租户名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入租户编码', trigger: 'blur' },
    { pattern: /^[a-z0-9_-]+$/, message: '仅支持小写字母、数字、下划线和连字符', trigger: 'blur' }
  ]
};

const title = computed(() => (props.operateType === 'add' ? '新增租户' : '编辑租户'));

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
        window.$message?.success('创建成功');
        emit('submitted');
        handleClose();
      }
    } else if (props.rowData) {
      const { error } = await fetchUpdateTenant(props.rowData.id, formData.value);
      if (!error) {
        window.$message?.success('更新成功');
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
        <NFormItem label="租户名称" path="name">
          <NInput v-model:value="formData.name" placeholder="请输入租户名称" />
        </NFormItem>
        <NFormItem label="租户编码" path="code">
          <NInput v-model:value="formData.code" placeholder="仅限小写字母、数字" :disabled="operateType === 'edit'" />
        </NFormItem>
        <NFormItem label="描述">
          <NInput v-model:value="formData.description" type="textarea" placeholder="租户描述（可选）" :rows="3" />
        </NFormItem>
        <NFormItem label="联系人">
          <NInput v-model:value="formData.contact_name" placeholder="联系人姓名" />
        </NFormItem>
        <NFormItem label="联系邮箱">
          <NInput v-model:value="formData.contact_email" placeholder="联系邮箱" />
        </NFormItem>
        <NFormItem label="联系手机">
          <NInput v-model:value="formData.contact_phone" placeholder="联系手机号" />
        </NFormItem>
        <NFormItem label="最大用户数">
          <NInputNumber v-model:value="formData.max_users" :min="1" :max="99999" class="w-full" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace>
          <NButton @click="handleClose">取消</NButton>
          <NButton type="primary" :loading="loading" @click="handleSubmit">提交</NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>
