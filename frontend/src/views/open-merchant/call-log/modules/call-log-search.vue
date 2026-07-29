<script setup lang="ts">
import { computed } from 'vue';
import { useDebounceFn } from '@vueuse/core';
import { NDatePicker, NInput, NSelect } from 'naive-ui';
import dayjs from 'dayjs';
import { $t } from '@/locales';

defineOptions({
  name: 'CallLogSearch'
});

interface Emits {
  (e: 'search'): void;
}

const model = defineModel<Api.Merchant.CallLogSearchParams>('model', { required: true });

const emit = defineEmits<Emits>();

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

const successOptions = [
  { label: $t('page.manage.callLog.successTrue'), value: 1 },
  { label: $t('page.manage.callLog.successFalse'), value: 0 }
];

// NSelect 取值为 string|number，这里用 1/0 与后端 bool 互转
const successValue = computed<number | null>({
  get() {
    return model.value.success == null ? null : model.value.success ? 1 : 0;
  },
  set(val: number | null) {
    model.value.success = val == null ? null : val === 1;
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
      v-model:value="model.action"
      :placeholder="$t('page.manage.callLog.form.action')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NInput
      v-model:value="model.api_key"
      :placeholder="$t('page.manage.callLog.form.apiKey')"
      clearable
      :style="{ width: '180px' }"
      @update:value="debouncedSearch"
    />
    <NSelect
      v-model:value="successValue"
      :options="successOptions"
      :placeholder="$t('page.manage.callLog.success')"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
    <NDatePicker
      v-model:value="timeRange"
      type="datetimerange"
      :start-placeholder="$t('page.manage.callLog.form.startTime')"
      :end-placeholder="$t('page.manage.callLog.form.endTime')"
      clearable
      :style="{ width: '280px' }"
      @update:value="handleSearch"
    />
  </div>
</template>
