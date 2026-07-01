<script setup lang="ts">
import { computed } from 'vue';
import dayjs from 'dayjs';
import { useDebounceFn } from '@vueuse/core';
import { $t } from '@/locales';

defineOptions({ name: 'TaskLogSearch' });

interface Emits {
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.Scheduler.TaskLogSearchParams>('model', { required: true });

const statusOptions = [
  { label: $t('page.manage.scheduler.lastStatuses.success'), value: 'success' },
  { label: $t('page.manage.scheduler.lastStatuses.failed'), value: 'failed' },
  { label: $t('page.manage.scheduler.lastStatuses.running'), value: 'running' },
  { label: $t('page.manage.scheduler.lastStatuses.timeout'), value: 'timeout' }
];

const timeRange = computed<[number, number] | null>({
  get() {
    const start = model.value.start_time ? dayjs(model.value.start_time).valueOf() : null;
    const end = model.value.end_time ? dayjs(model.value.end_time).valueOf() : null;
    return start && end ? [start, end] : null;
  },
  set(val: [number, number] | null) {
    if (val) {
      model.value.start_time = dayjs(val[0]).format();
      model.value.end_time = dayjs(val[1]).format();
    } else {
      model.value.start_time = undefined;
      model.value.end_time = undefined;
    }
  }
});

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
      v-model:value="model.task_name"
      :placeholder="$t('page.manage.schedulerLog.form.taskName')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NSelect
      v-model:value="model.status"
      :options="statusOptions"
      :placeholder="$t('page.manage.schedulerLog.form.status')"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
    <NDatePicker
      v-model:value="timeRange"
      start-placeholder="开始时间"
      end-placeholder="结束时间"
      type="datetimerange"
      clearable
      :style="{ width: '340px' }"
      @update:value="handleSearch"
    />
  </div>
</template>

<style scoped></style>
