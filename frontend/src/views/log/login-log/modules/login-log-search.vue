<script setup lang="ts">
import { computed } from 'vue';
import { useDebounceFn } from '@vueuse/core';
import { NDatePicker, NInput, NSelect } from 'naive-ui';
import dayjs from 'dayjs';
import { $t } from '@/locales';

defineOptions({
  name: 'LoginLogSearch'
});

interface Emits {
  (e: 'search'): void;
}

const model = defineModel<Api.SystemManage.LoginLogSearchParams>('model', { required: true });

const emit = defineEmits<Emits>();

const statusOptions: { label: string; value: boolean }[] = [
  { label: $t('page.log.loginLog.success'), value: true },
  { label: $t('page.log.loginLog.failed'), value: false }
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
      v-model:value="model.username"
      :placeholder="$t('page.log.loginLog.form.username')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NInput
      v-model:value="model.ip"
      :placeholder="$t('page.log.loginLog.form.ip')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NSelect
      v-model:value="model.status as any"
      :options="statusOptions as any"
      :placeholder="$t('page.log.loginLog.form.status')"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
    <NDatePicker
      v-model:value="timeRange"
      type="datetimerange"
      start-placeholder="开始时间"
      end-placeholder="结束时间"
      clearable
      :style="{ width: '280px' }"
      @update:value="handleSearch"
    />
  </div>
</template>
