<script setup lang="ts">
import { computed, onMounted, ref, toRaw } from 'vue';
import { jsonClone } from '@sa/utils';
import { fetchGetRobotList, fetchGetSceneMapList } from '@/service/api';
import { $t } from '@/locales';

defineOptions({ name: 'TaskHistorySearch' });

interface Emits {
  (e: 'search'): void;
  (e: 'reset'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.Task.TaskExecutionSearchParams>('model', { required: true });

const defaultModel = jsonClone(toRaw(model.value));

const statusOptions = [
  { label: '已完成', value: 'completed' },
  { label: '已失败', value: 'failed' },
  { label: '已取消', value: 'cancelled' }
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
      label: `${robot.name}（${robot.serial_number}）`,
      value: robot.id,
      map_id: robot.map_id ?? null
    }));
  }
}

function resetModel() {
  Object.assign(model.value, defaultModel);
  emit('reset');
}

function handleMapChange() {
  if (model.value.robot_id) {
    const robot = robotOptions.value.find(item => item.value === model.value.robot_id);
    if (robot?.map_id !== model.value.map_id) {
      model.value.robot_id = null;
    }
  }
}

function search() {
  emit('search');
}

onMounted(() => {
  loadOptions();
});
</script>

<template>
  <NCollapse :default-expanded-names="['task-history-search']">
    <NCollapseItem :title="$t('common.search')" name="task-history-search">
      <NForm :model="model" label-placement="left" :label-width="80">
        <NGrid responsive="screen" item-responsive>
          <NFormItemGi span="24 s:12 m:6" label="任务名称" path="task_name" class="pr-24px">
            <NInput v-model:value="model.task_name" placeholder="请输入任务名称" clearable />
          </NFormItemGi>
          <NFormItemGi span="24 s:12 m:6" label="执行状态" path="status" class="pr-24px">
            <NSelect v-model:value="model.status" :options="statusOptions" placeholder="请选择状态" clearable />
          </NFormItemGi>
          <NFormItemGi span="24 s:12 m:6" label="场景地图" path="map_id" class="pr-24px">
            <NSelect
              v-model:value="model.map_id"
              :options="mapOptions"
              placeholder="请选择场景地图"
              filterable
              clearable
              @update:value="handleMapChange"
            />
          </NFormItemGi>
          <NFormItemGi span="24 s:12 m:6" label="机器人" path="robot_id" class="pr-24px">
            <NSelect v-model:value="model.robot_id" :options="filteredRobotOptions" placeholder="请选择机器人" filterable clearable />
          </NFormItemGi>
          <NFormItemGi span="24 m:6" class="pr-24px">
            <NSpace class="w-full" justify="end">
              <NButton @click="resetModel">
                <template #icon>
                  <icon-ic-round-refresh class="text-icon" />
                </template>
                {{ $t('common.reset') }}
              </NButton>
              <NButton type="primary" ghost @click="search">
                <template #icon>
                  <icon-ic-round-search class="text-icon" />
                </template>
                {{ $t('common.search') }}
              </NButton>
            </NSpace>
          </NFormItemGi>
        </NGrid>
      </NForm>
    </NCollapseItem>
  </NCollapse>
</template>

<style scoped></style>
