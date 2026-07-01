<script setup lang="ts">
import { computed } from 'vue';
import dayjs from 'dayjs';
import { useDebounceFn } from '@vueuse/core';
import { $t } from '@/locales';
import { NDatePicker, NInput } from 'naive-ui';

defineOptions({
  name: 'OperationLogSearch'
});

interface Emits {
  (e: 'search'): void;
}

const model = defineModel<Api.SystemManage.OperationLogSearchParams>('model', { required: true });

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
      :placeholder="$t('page.log.operationLog.form.username')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NInput
      v-model:value="model.module"
      :placeholder="$t('page.log.operationLog.form.module')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NInput
      v-model:value="model.action"
      :placeholder="$t('page.log.operationLog.form.action')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
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
