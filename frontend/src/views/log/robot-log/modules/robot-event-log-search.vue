<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import dayjs from 'dayjs';
import { $t } from '@/locales';
import { NDatePicker, NSelect } from 'naive-ui';
import { fetchGetRobotList } from '@/service/api/robot';

defineOptions({
  name: 'RobotEventLogSearch'
});

interface Emits {
  (e: 'search'): void;
}

const model = defineModel<Api.SystemManage.RobotEventLogSearchParams>('model', { required: true });

const emit = defineEmits<Emits>();

const robotOptions = ref<{ label: string; value: number }[]>([]);

const eventTypeOptions = [
  { label: $t('page.log.robotEventLog.typeTask'), value: 'task' },
  { label: $t('page.log.robotEventLog.typeAlarm'), value: 'alarm' }
];

const eventStatusOptions = [
  { label: $t('page.log.robotEventLog.statusNormal'), value: 'normal' },
  { label: $t('page.log.robotEventLog.statusAbnormal'), value: 'abnormal' }
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

async function loadRobotOptions() {
  try {
    const { data } = await fetchGetRobotList({ page: 1, page_size: 999 });
    if (data?.records) {
      robotOptions.value = data.records.map((r: any) => ({ label: r.name, value: r.id }));
    }
  } catch {
    robotOptions.value = [];
  }
}

function handleSearch() {
  model.value.page = 1;
  emit('search');
}

onMounted(() => {
  loadRobotOptions();
});
</script>

<template>
  <div class="flex-y-center flex-wrap gap-12px">
    <NSelect
      v-model:value="model.robot_id as any"
      :options="robotOptions"
      :placeholder="$t('page.log.robotEventLog.form.robotName')"
      clearable
      filterable
      :style="{ width: '160px' }"
      @update:value="handleSearch"
    />
    <NSelect
      v-model:value="model.event_type as any"
      :options="eventTypeOptions"
      :placeholder="$t('page.log.robotEventLog.form.eventType')"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
    <NSelect
      v-model:value="model.event_status as any"
      :options="eventStatusOptions"
      :placeholder="$t('page.log.robotEventLog.form.eventStatus')"
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
