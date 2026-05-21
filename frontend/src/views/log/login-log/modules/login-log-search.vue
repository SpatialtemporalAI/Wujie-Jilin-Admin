<script setup lang="ts">
import { NDatePicker, NInput, NSelect } from 'naive-ui';

defineOptions({
  name: 'LoginLogSearch'
});

interface Emits {
  (e: 'search'): void;
}

const model = defineModel<Api.SystemManage.LoginLogSearchParams>('model', { required: true });

const emit = defineEmits<Emits>();

const statusOptions = [
  { label: '全部', value: null },
  { label: '成功', value: true },
  { label: '失败', value: false }
];

function handleReset() {
  model.value.username = null;
  model.value.ip = null;
  model.value.status = null;
  model.value.start_time = null;
  model.value.end_time = null;
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <div class="flex flex-wrap items-center gap-12px">
      <NInput
        v-model:value="model.username"
        :placeholder="$t('page.log.loginLog.form.username')"
        clearable
        class="w-160px"
      />
      <NInput
        v-model:value="model.ip"
        :placeholder="$t('page.log.loginLog.form.ip')"
        clearable
        class="w-160px"
      />
      <NSelect
        v-model:value="model.status"
        :options="statusOptions"
        :placeholder="$t('page.log.loginLog.form.status')"
        clearable
        class="w-120px"
      />
      <NDatePicker
        v-model:value="model.start_time"
        type="datetime"
        :placeholder="$t('page.log.loginLog.form.startTime')"
        clearable
        class="w-200px"
        @update:value="(val: number | null) => { model.start_time = val ? new Date(val).toISOString() : null }"
      />
      <NDatePicker
        v-model:value="model.end_time"
        type="datetime"
        :placeholder="$t('page.log.loginLog.form.endTime')"
        clearable
        class="w-200px"
        @update:value="(val: number | null) => { model.end_time = val ? new Date(val).toISOString() : null }"
      />
      <NButton type="primary" ghost size="small" @click="emit('search')">
        {{ $t('common.search') }}
      </NButton>
      <NButton size="small" @click="handleReset">
        {{ $t('common.reset') }}
      </NButton>
    </div>
  </NCard>
</template>

<script lang="ts">
import { NButton, NCard } from 'naive-ui';
</script>
