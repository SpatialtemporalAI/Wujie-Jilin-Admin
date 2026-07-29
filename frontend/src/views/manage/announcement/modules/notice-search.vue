<script setup lang="ts">
import { useDebounceFn } from '@vueuse/core';
import { NInput, NSelect } from 'naive-ui';
import { enableStatusOptions } from '@/constants/business';
import { $t } from '@/locales';

defineOptions({
  name: 'NoticeSearch'
});

interface Emits {
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.Notification.NoticeSearchParams>('model', { required: true });

/** 通知类型选项 */
const noticeTypeOptions = [
  { label: $t('page.manage.announcement.type.announcement'), value: 'announcement' },
  { label: $t('page.manage.announcement.type.system'), value: 'system' },
  { label: $t('page.manage.announcement.type.operation'), value: 'operation' },
  { label: $t('page.manage.announcement.type.approval'), value: 'approval' }
];

/** 推送范围选项 */
const targetTypeOptions = [
  { label: $t('page.manage.announcement.targetType.all'), value: 'all' },
  { label: $t('page.manage.announcement.targetType.role'), value: 'role' },
  { label: $t('page.manage.announcement.targetType.user'), value: 'user' }
];

/** 优先级选项 */
const priorityOptions = [
  { label: $t('notification.priority.low'), value: 'low' },
  { label: $t('notification.priority.normal'), value: 'normal' },
  { label: $t('notification.priority.high'), value: 'high' },
  { label: $t('notification.priority.urgent'), value: 'urgent' }
];

function handleSearch() {
  model.value.page = 1;
  emit('search');
}

const debouncedSearch = useDebounceFn(() => {
  handleSearch();
}, 500);
</script>

<template>
  <div class="flex-y-center flex-wrap gap-12px">
    <NInput
      v-model:value="model.title"
      :placeholder="$t('page.manage.announcement.form.title')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NSelect
      v-model:value="model.type"
      :options="noticeTypeOptions"
      :placeholder="$t('page.manage.announcement.form.type')"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
    <NSelect
      v-model:value="model.target_type"
      :options="targetTypeOptions"
      :placeholder="$t('page.manage.announcement.form.targetType')"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
    <NSelect
      v-model:value="model.status"
      :options="enableStatusOptions"
      :placeholder="$t('page.manage.announcement.form.status')"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
    <NSelect
      v-model:value="model.priority"
      :options="priorityOptions"
      :placeholder="$t('page.manage.announcement.form.priority')"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
  </div>
</template>

<style scoped></style>
