<script setup lang="ts">
import { $t } from '@/locales';

interface Emits {
  (e: 'search'): void;
  (e: 'reset'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.Notification.NoticeSearchParams>('model', { required: true });

function handleSearch() {
  emit('search');
}

function handleReset() {
  model.value = {
    page: 1,
    page_size: 10,
    title: null,
    type: null,
    target_type: null,
    status: null,
    priority: null
  };
  emit('reset');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NForm
      :model="model"
      label-placement="left"
      :label-width="80"
      inline
      :show-feedback="false"
    >
      <NFormItem :label="$t('common.title')" path="title">
        <NInput
          v-model:value="model.title"
          :placeholder="$t('common.pleaseEnter') + $t('common.title')"
          clearable
          @keyup.enter="handleSearch"
        />
      </NFormItem>
      <NFormItem label="类型" path="type">
        <NSelect
          v-model:value="model.type"
          :options="[
            { label: '公告', value: 'announcement' },
            { label: '系统', value: 'system' },
            { label: '操作提醒', value: 'operation' },
            { label: '审批通知', value: 'approval' }
          ]"
          clearable
          placeholder="请选择类型"
          class="w-160px"
        />
      </NFormItem>
      <NFormItem label="推送范围" path="target_type">
        <NSelect
          v-model:value="model.target_type"
          :options="[
            { label: '全员', value: 'all' },
            { label: '按角色', value: 'role' },
            { label: '按用户', value: 'user' }
          ]"
          clearable
          placeholder="请选择推送范围"
          class="w-160px"
        />
      </NFormItem>
      <NFormItem label="状态" path="status">
        <NSelect
          v-model:value="model.status"
          :options="[
            { label: '已发布', value: '1' },
            { label: '草稿', value: '2' }
          ]"
          clearable
          placeholder="请选择状态"
          class="w-160px"
        />
      </NFormItem>
      <NFormItem label="优先级" path="priority">
        <NSelect
          v-model:value="model.priority"
          :options="[
            { label: '低', value: 'low' },
            { label: '普通', value: 'normal' },
            { label: '高', value: 'high' },
            { label: '紧急', value: 'urgent' }
          ]"
          clearable
          placeholder="请选择优先级"
          class="w-160px"
        />
      </NFormItem>
      <NFormItem>
        <NSpace>
          <NButton type="primary" @click="handleSearch">
            <icon-ic-round-search class="text-20px"></icon-ic-round-search>
            {{ $t('common.search') }}
          </NButton>
          <NButton @click="handleReset">
            <icon-ic-round-refresh class="text-20px"></icon-ic-round-refresh>
            {{ $t('common.reset') }}
          </NButton>
        </NSpace>
      </NFormItem>
    </NForm>
  </NCard>
</template>
