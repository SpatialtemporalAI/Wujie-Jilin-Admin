<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { fetchGetAllRobots, fetchGetSceneMapList } from '@/service/api';

defineOptions({ name: 'TaskHistorySearch' });

interface Emits {
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.Task.TaskExecutionRecordSearchParams>('model', { required: true });

const props = defineProps<{
  statusOptions?: { label: string; value: string }[];
}>();

const defaultStatusOptions = [
  { label: '已完成', value: 'completed' },
  { label: '已失败', value: 'failed' },
  { label: '已取消', value: 'cancelled' }
];

const statusOptions = computed(() => props.statusOptions ?? defaultStatusOptions);

const mapOptions = ref<{ label: string; value: number }[]>([]);
const robotOptions = ref<{ label: string; value: number; map_id: number | null }[]>([]);

const filteredRobotOptions = computed(() => {
  if (!model.value.scene_id) return robotOptions.value;
  return robotOptions.value.filter(robot => robot.map_id === model.value.scene_id);
});

async function loadOptions() {
  const [mapResult, robotResult] = await Promise.all([
    fetchGetSceneMapList({ page: 1, page_size: 999, name: null, group_id: undefined, status: null }),
    fetchGetAllRobots()
  ]);
  if (!mapResult.error && mapResult.data) {
    mapOptions.value = (mapResult.data.records || []).map(map => ({ label: map.name, value: map.id }));
  }
  if (!robotResult.error && robotResult.data) {
    robotOptions.value = (robotResult.data || []).map(robot => ({
      label: `${robot.name}`,
      value: robot.id,
      map_id: robot.map_id ?? null
    }));
  }
}

function handleMapChange() {
  if (model.value.robot_id) {
    const robot = robotOptions.value.find(item => item.value === model.value.robot_id);
    if (robot?.map_id !== model.value.scene_id) {
      model.value.robot_id = null;
    }
  }
  handleSearch();
}

function handleSearch() {
  model.value.page = 1;
  emit('search');
}

onMounted(() => {
  loadOptions();
});
</script>

<template>
  <div class="flex-y-center flex-wrap gap-12px">
    <NSelect
      v-model:value="model.status"
      :options="statusOptions"
      placeholder="执行状态"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
    <NSelect
      v-model:value="model.scene_id"
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
