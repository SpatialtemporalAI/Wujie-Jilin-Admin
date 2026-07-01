<script setup lang="ts">
import { useDebounceFn } from '@vueuse/core';
import { enableStatusOptions } from '@/constants/business';
import { $t } from '@/locales';

defineOptions({ name: 'TaskSearch' });

interface Emits {
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.Scheduler.ScheduledTaskSearchParams>('model', { required: true });

const triggerTypeOptions = [
  { label: $t('page.manage.scheduler.triggerTypes.cron'), value: 'cron' },
  { label: $t('page.manage.scheduler.triggerTypes.interval'), value: 'interval' },
  { label: $t('page.manage.scheduler.triggerTypes.date'), value: 'date' }
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
      v-model:value="model.name"
      :placeholder="$t('page.manage.scheduler.form.taskName')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NInput
      v-model:value="model.task_key"
      :placeholder="$t('page.manage.scheduler.form.taskKey')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NSelect
      v-model:value="model.status"
      :options="enableStatusOptions"
      :placeholder="$t('page.manage.scheduler.form.status')"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
    <NSelect
      v-model:value="model.trigger_type"
      :options="triggerTypeOptions"
      :placeholder="$t('page.manage.scheduler.form.triggerType')"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
  </div>
</template>

<style scoped></style>
