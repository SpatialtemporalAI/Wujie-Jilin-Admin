<script setup lang="ts">
import { NDatePicker, NInput } from 'naive-ui';

defineOptions({
  name: 'OperationLogSearch'
});

interface Emits {
  (e: 'search'): void;
}

const model = defineModel<Api.SystemManage.OperationLogSearchParams>('model', { required: true });

const emit = defineEmits<Emits>();

function handleReset() {
  model.value.username = null;
  model.value.module = null;
  model.value.action = null;
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
        :placeholder="$t('page.log.operationLog.form.username')"
        clearable
        class="w-160px"
      />
      <NInput
        v-model:value="model.module"
        :placeholder="$t('page.log.operationLog.form.module')"
        clearable
        class="w-160px"
      />
      <NInput
        v-model:value="model.action"
        :placeholder="$t('page.log.operationLog.form.action')"
        clearable
        class="w-160px"
      />
      <NDatePicker
        v-model:value="model.start_time"
        type="datetime"
        :placeholder="$t('page.log.operationLog.form.startTime')"
        clearable
        class="w-200px"
        @update:value="(val: number | null) => { model.start_time = val ? new Date(val).toISOString() : null }"
      />
      <NDatePicker
        v-model:value="model.end_time"
        type="datetime"
        :placeholder="$t('page.log.operationLog.form.endTime')"
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
