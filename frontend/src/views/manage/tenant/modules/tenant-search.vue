<script setup lang="ts">
import { NInput, NSelect } from 'naive-ui';
import { $t } from '@/locales';

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
  { label: $t('page.manage.common.status.enable'), value: '1' },
  { label: $t('page.manage.common.status.disable'), value: '2' }
];
</script>

<template>
  <NCard :bordered="false" size="small">
    <NForm :model="model" label-placement="left" :label-width="60" inline>
      <NFormItem :label="$t('page.manage.tenant.search.name')">
        <NInput v-model:value="model.name" :placeholder="$t('page.manage.tenant.search.namePlaceholder')" clearable class="w-160px" />
      </NFormItem>
      <NFormItem :label="$t('page.manage.tenant.search.code')">
        <NInput v-model:value="model.code" :placeholder="$t('page.manage.tenant.search.codePlaceholder')" clearable class="w-160px" />
      </NFormItem>
      <NFormItem :label="$t('common.status')">
        <NSelect v-model:value="model.status" :options="statusOptions" clearable class="w-100px" />
      </NFormItem>
      <NFormItem>
        <NButton type="primary" @click="emit('search')">
          <template #icon><icon-ic-round-search /></template>
          {{ $t('common.search') }}
        </NButton>
      </NFormItem>
    </NForm>
  </NCard>
</template>
