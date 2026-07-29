<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { NDatePicker, NSelect } from 'naive-ui';
import dayjs from 'dayjs';
import { fetchGetAllRobots } from '@/service/api/robot';
import { $t } from '@/locales';

defineOptions({
  name: 'RobotEventLogSearch'
});

interface Emits {
  (e: 'search'): void;
}

const model = defineModel<Api.SystemManage.RobotEventLogSearchParams>('model', { required: true });

const emit = defineEmits<Emits>();

const robotOptions = ref<{ label: string; value: number }[]>([]);

const eventStatusOptions = [
  { label: $t('page.log.robotEventLog.statusCritical'), value: 'critical' },
  { label: $t('page.log.robotEventLog.statusWarning'), value: 'warning' },
  { label: $t('page.log.robotEventLog.statusInfo'), value: 'info' }
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
    const { data } = await fetchGetAllRobots();
    if (data) {
      robotOptions.value = data.map(r => ({ label: r.name, value: r.id }));
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
