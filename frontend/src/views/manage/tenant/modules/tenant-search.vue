<script setup lang="ts">
import { ref } from 'vue';
import { NInput, NSelect } from 'naive-ui';

interface Emits {
  (e: 'search'): void;
}

interface Props {
  model: {
    page: number;
    page_size: number;
    name: string | null;
    code: string | null;
    status: string | null;
  };
}

defineProps<Props>();
const emit = defineEmits<Emits>();

const statusOptions = [
  { label: '全部', value: null },
  { label: '启用', value: '1' },
  { label: '禁用', value: '2' }
];
</script>

<template>
  <NCard :bordered="false" size="small">
    <NForm :model="model" label-placement="left" :label-width="60" inline>
      <NFormItem label="名称">
        <NInput v-model:value="model.name" placeholder="租户名称" clearable class="w-160px" />
      </NFormItem>
      <NFormItem label="编码">
        <NInput v-model:value="model.code" placeholder="租户编码" clearable class="w-160px" />
      </NFormItem>
      <NFormItem label="状态">
        <NSelect v-model:value="model.status" :options="statusOptions" placeholder="全部" clearable class="w-100px" />
      </NFormItem>
      <NFormItem>
        <NButton type="primary" @click="emit('search')">
          <template #icon><icon-ic-round-search /></template>
          搜索
        </NButton>
      </NFormItem>
    </NForm>
  </NCard>
</template>
