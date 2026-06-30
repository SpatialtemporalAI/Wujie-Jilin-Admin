<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useDebounceFn } from '@vueuse/core';
import { fetchGetRobotList, fetchGetSceneMapList } from '@/service/api';

defineOptions({ name: 'TaskSearch' });

interface Emits {
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.Task.TaskSearchParams>('model', { required: true });

const taskTypeOptions = [
  { label: '巡逻', value: 'patrol' },
  { label: '播报', value: 'broadcast' }
];

const enabledOptions = [
  { label: '启用', value: '1' },
  { label: '禁用', value: '2' }
];

const mapOptions = ref<{ label: string; value: number }[]>([]);
const robotOptions = ref<{ label: string; value: number; map_id: number | null }[]>([]);

const filteredRobotOptions = computed(() => {
  if (!model.value.map_id) return robotOptions.value;
  return robotOptions.value.filter(robot => robot.map_id === model.value.map_id);
});

async function loadOptions() {
  const [mapResult, robotResult] = await Promise.all([
    fetchGetSceneMapList({ page: 1, page_size: 999, name: null, group_id: undefined, status: null }),
    fetchGetRobotList({ page: 1, page_size: 999, name: null, serial_number: null, status: null, model_id: undefined })
  ]);
  if (!mapResult.error && mapResult.data) {
    mapOptions.value = (mapResult.data.records || []).map(map => ({ label: map.name, value: map.id }));
  }
  if (!robotResult.error && robotResult.data) {
    robotOptions.value = (robotResult.data.records || []).map(robot => ({
      label: `${robot.name}`,
      value: robot.id,
      map_id: robot.map_id ?? null
    }));
  }
}

function handleMapChange() {
  if (model.value.robot_id) {
    const robot = robotOptions.value.find(item => item.value === model.value.robot_id);
    if (robot?.map_id !== model.value.map_id) {
      model.value.robot_id = null;
    }
  }
  handleSearch();
}

function handleSearch() {
  model.value.page = 1;
  emit('search');
}

const debouncedSearch = useDebounceFn(() => {
  handleSearch();
}, 500);

onMounted(() => {
  loadOptions();
});
</script>

<template>
  <div class="flex-y-center flex-wrap gap-12px">
    <NInput
      v-model:value="model.name"
      placeholder="任务名称"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NSelect
      v-model:value="model.task_type"
      :options="taskTypeOptions"
      placeholder="任务类型"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
    <NSelect
      v-model:value="model.enabled"
      :options="enabledOptions"
      placeholder="启用状态"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
    <NSelect
      v-model:value="model.map_id"
      :options="mapOptions"
      placeholder="场景地图"
      filterable
      clearable
      :style="{ width: '160px' }"
      @update:value="handleMapChange"
    />
    <NSelect
      v-model:value="model.robot_id"
      :options="filteredRobotOptions"
      placeholder="机器人"
      filterable
      clearable
      :style="{ width: '160px' }"
      @update:value="handleSearch"
    />
  </div>
</template>

<style scoped></style>
