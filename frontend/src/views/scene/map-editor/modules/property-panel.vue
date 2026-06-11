<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { NProgress, NTag } from 'naive-ui';
import type { SelectedElement } from '../composables/useMapEditor';
import { fetchGetRobotList } from '@/service/api';

interface Props {
  editorData: Api.Scene.EditorMapData | null;
  selectedElement: SelectedElement | null;
  resolution: number;
  sceneList: Api.Scene.SceneMap[];
  selectedMapId: number | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'update-element', data: { type: string; id: number; updates: Record<string, any> }): void;
  (e: 'remove-element', type: 'annotation' | 'path' | 'object', id: number): void;
  (e: 'select-scene', mapId: number): void;
  (e: 'add-scene'): void;
  (e: 'delete-scene', mapId: number): void;
}>();

const activeTab = ref('overview');
const searchText = ref('');
const robotList = ref<Api.Robot.Robot[]>([]);
const robotLoading = ref(false);

const statusColorMap: Record<Api.Robot.RobotStatusEnum, 'success' | 'warning' | 'default'> = {
  online: 'success',
  offline: 'warning',
  inactive: 'default'
};

const statusLabelMap: Record<Api.Robot.RobotStatusEnum, string> = {
  online: '在线',
  offline: '离线',
  inactive: '未激活'
};

const robotOverview = computed(() => {
  const total = robotList.value.length;
  const online = robotList.value.filter(robot => robot.status === 'online').length;
  const offline = robotList.value.filter(robot => robot.status === 'offline').length;
  const inactive = robotList.value.filter(robot => robot.status === 'inactive').length;

  return { total, online, offline, inactive };
});

const filteredList = computed(() => {
  if (!searchText.value) return props.sceneList;
  return props.sceneList.filter(m => m.name.includes(searchText.value));
});

const selectedAnnotation = computed(() => {
  if (!props.editorData || !props.selectedElement || props.selectedElement.type !== 'annotation') return null;
  return props.editorData.annotations.find(a => a.id === props.selectedElement!.id) || null;
});

const selectedPath = computed(() => {
  if (!props.editorData || !props.selectedElement || props.selectedElement.type !== 'path') return null;
  return props.editorData.paths.find(p => p.id === props.selectedElement!.id) || null;
});

const selectedObject = computed(() => {
  if (!props.editorData || !props.selectedElement || props.selectedElement.type !== 'object') return null;
  return props.editorData.objects.find(o => o.id === props.selectedElement!.id) || null;
});

const annotationStartName = computed(() => {
  if (!selectedPath.value || !props.editorData) return '';
  const ann = props.editorData.annotations.find(a => a.id === selectedPath.value!.start_annotation_id);
  return ann?.name || '';
});

const annotationEndName = computed(() => {
  if (!selectedPath.value || !props.editorData) return '';
  const ann = props.editorData.annotations.find(a => a.id === selectedPath.value!.end_annotation_id);
  return ann?.name || '';
});

const pointTypeOptions = [
  { label: '导航点', value: 'navigation' },
  { label: '接待点', value: 'reception' },
];

function updateAnnotation(field: string, value: any) {
  if (!selectedAnnotation.value) return;
  emit('update-element', { type: 'annotation', id: selectedAnnotation.value.id, updates: { [field]: value } });
}

function pixelToMeter(px: number): number {
  return Math.round(px * props.resolution * 100) / 100;
}

function getBatteryColor(threshold?: number | null): string {
  if (threshold === null || threshold === undefined) return '#909399';
  if (threshold <= 10) return '#18a058';
  if (threshold <= 30) return '#f0a020';
  return '#d03050';
}

async function loadRobotList() {
  robotLoading.value = true;
  try {
    const { data, error } = await fetchGetRobotList({ page: 1, page_size: 200, name: null, serial_number: null, status: null, model_id: undefined });
    if (!error && data) {
      robotList.value = data.records;
    } else {
      robotList.value = [];
    }
  } catch {
    robotList.value = [];
  } finally {
    robotLoading.value = false;
  }
}

onMounted(() => {
  loadRobotList();
});
</script>

<template>
  <div class="flex h-full min-h-0 flex-col border-l border-gray-200 bg-white">
    <NTabs
      v-model:value="activeTab"
      type="line"
      size="small"
      class="property-panel-tabs h-full min-h-0 flex flex-col"
      pane-wrapper-class="min-h-0 flex-1 overflow-auto"
      pane-class="h-full"
    >
      <NTabPane name="overview" tab="机器人总览">
        <div class="h-full overflow-auto p-12px">
          <NSpin :show="robotLoading">
            <div class="grid grid-cols-2 gap-8px">
              <NCard size="small" embedded>
                <NStatistic label="机器人总数" :value="robotOverview.total" />
              </NCard>
              <NCard size="small" embedded>
                <NStatistic label="在线" :value="robotOverview.online" />
              </NCard>
              <NCard size="small" embedded>
                <NStatistic label="离线" :value="robotOverview.offline" />
              </NCard>
              <NCard size="small" embedded>
                <NStatistic label="未激活" :value="robotOverview.inactive" />
              </NCard>
            </div>

            <div class="mt-12px flex items-center justify-between">
              <span class="text-sm font-medium">机器人列表</span>
              <NButton size="tiny" quaternary :loading="robotLoading" @click="loadRobotList">
                <template #icon><icon-ic-round-refresh /></template>
                刷新
              </NButton>
            </div>

            <div class="mt-8px space-y-8px">
              <NCard v-for="robot in robotList" :key="robot.id" size="small" embedded>
                <div class="flex items-start justify-between gap-8px">
                  <div class="min-w-0 flex-1">
                    <div class="truncate text-sm font-medium">{{ robot.name }}</div>
                    <div class="mt-4px truncate text-xs text-gray-400">{{ robot.model_name || '-' }} / {{ robot.serial_number }}</div>
                  </div>
                  <NTag :type="statusColorMap[robot.status]" size="small">
                    {{ statusLabelMap[robot.status] }}
                  </NTag>
                </div>
                <div class="mt-10px grid grid-cols-2 gap-8px text-xs text-gray-500">
                  <div>速度档位：{{ robot.speed_level || '-' }}</div>
                  <div>报警阈值：{{ robot.battery_threshold ?? '-' }}%</div>
                </div>
                <NProgress
                  class="mt-8px"
                  type="line"
                  :percentage="robot.battery_threshold ?? 0"
                  :color="getBatteryColor(robot.battery_threshold)"
                  indicator-placement="inside"
                />
              </NCard>
              <NEmpty v-if="!robotLoading && robotList.length === 0" description="暂无机器人" class="mt-20px" />
            </div>
          </NSpin>
        </div>
      </NTabPane>

      <NTabPane name="scenes" tab="场景列表">
        <div class="flex h-full flex-col">
          <div class="border-b border-gray-200 p-12px">
            <div class="mb-8px flex items-center justify-between">
              <NButton size="tiny" type="primary" @click="emit('add-scene')">
                <template #icon><icon-ic-round-plus /></template>
                新增
              </NButton>
            </div>
            <NInput v-model:value="searchText" placeholder="搜索场景" size="small" clearable>
              <template #prefix><icon-ic-round-search /></template>
            </NInput>
          </div>

          <div class="flex-1 overflow-auto p-8px">
            <div
              v-for="map in filteredList"
              :key="map.id"
              class="group flex cursor-pointer items-center justify-between rounded-md px-8px py-6px text-sm transition-colors"
              :class="map.id === selectedMapId ? 'bg-blue-50 text-blue-600' : 'hover:bg-gray-50'"
              @click="emit('select-scene', map.id)"
            >
              <div class="min-w-0 flex-1">
                <div class="truncate">{{ map.name }}</div>
                <div class="text-xs text-gray-400">
                  {{ map.width && map.height ? `${map.width}×${map.height}` : '未设置尺寸' }}
                </div>
              </div>
              <NPopconfirm @positive-click.stop="emit('delete-scene', map.id)">
                <template #trigger>
                  <NButton
                    quaternary
                    size="tiny"
                    type="error"
                    class="opacity-0 group-hover:opacity-100"
                    @click.stop
                  >
                    <template #icon><icon-ic-round-delete-outline /></template>
                  </NButton>
                </template>
                确认删除此场景？所有点位、路径、障碍物数据将一并删除。
              </NPopconfirm>
            </div>
            <NEmpty v-if="filteredList.length === 0" description="暂无场景" class="mt-20px" />
          </div>
        </div>
      </NTabPane>

      <NTabPane name="properties" tab="属性面板">
        <div class="p-12px">
          <!-- No selection: map info -->
          <template v-if="!selectedElement && editorData">
            <NDescriptions label-placement="left" bordered size="small" :column="1">
              <NDescriptionsItem label="地图名称">{{ editorData.map.name }}</NDescriptionsItem>
              <NDescriptionsItem label="分辨率">{{ editorData.map.resolution }} m/px</NDescriptionsItem>
              <NDescriptionsItem label="尺寸">
                {{ editorData.map.width && editorData.map.height ? `${editorData.map.width} × ${editorData.map.height} px` : '-' }}
              </NDescriptionsItem>
              <NDescriptionsItem label="点位数">{{ editorData.annotations.length }}</NDescriptionsItem>
              <NDescriptionsItem label="路径数">{{ editorData.paths.length }}</NDescriptionsItem>
              <NDescriptionsItem label="物体数">{{ editorData.objects.length }}</NDescriptionsItem>
            </NDescriptions>
          </template>

          <!-- Annotation selected -->
          <template v-if="selectedAnnotation">
            <NForm label-placement="left" label-width="60" size="small">
              <NFormItem label="名称">
                <NInput :value="selectedAnnotation.name" @update:value="v => updateAnnotation('name', v)" />
              </NFormItem>
              <NFormItem label="类型">
                <NSelect :value="selectedAnnotation.type" :options="pointTypeOptions" @update:value="v => updateAnnotation('type', v)" />
              </NFormItem>
              <NFormItem label="X (m)">
                <NInputNumber :value="pixelToMeter(selectedAnnotation.x)" :step="0.1" disabled size="small" class="w-full" />
              </NFormItem>
              <NFormItem label="Y (m)">
                <NInputNumber :value="pixelToMeter(selectedAnnotation.y)" :step="0.1" disabled size="small" class="w-full" />
              </NFormItem>
              <NFormItem label="角度">
                <NSlider :value="selectedAnnotation.angle" :min="0" :max="360" :step="1" @update:value="v => updateAnnotation('angle', v)" />
              </NFormItem>
            </NForm>
            <NButton type="error" size="small" block @click="emit('remove-element', 'annotation', selectedAnnotation.id)">删除此点位</NButton>
          </template>

          <!-- Path selected -->
          <template v-if="selectedPath">
            <NDescriptions label-placement="left" bordered size="small" :column="1">
              <NDescriptionsItem label="名称">{{ selectedPath.name || '-' }}</NDescriptionsItem>
              <NDescriptionsItem label="起点">{{ annotationStartName }}</NDescriptionsItem>
              <NDescriptionsItem label="终点">{{ annotationEndName }}</NDescriptionsItem>
            </NDescriptions>
            <NButton type="error" size="small" block class="mt-12px" @click="emit('remove-element', 'path', selectedPath.id)">删除此路径</NButton>
          </template>

          <!-- Object selected -->
          <template v-if="selectedObject">
            <NForm label-placement="left" label-width="60" size="small">
              <NFormItem label="类型">
                <NInput :value="selectedObject.type" disabled />
              </NFormItem>
              <NFormItem label="X (m)">
                <NInputNumber :value="pixelToMeter(selectedObject.x)" disabled size="small" class="w-full" />
              </NFormItem>
              <NFormItem label="Y (m)">
                <NInputNumber :value="pixelToMeter(selectedObject.y)" disabled size="small" class="w-full" />
              </NFormItem>
              <NFormItem v-if="!selectedObject.points" label="宽度">
                <NInputNumber :value="selectedObject.width" disabled size="small" class="w-full" />
              </NFormItem>
              <NFormItem v-if="!selectedObject.points" label="高度">
                <NInputNumber :value="selectedObject.height" disabled size="small" class="w-full" />
              </NFormItem>
            </NForm>
            <NButton type="error" size="small" block @click="emit('remove-element', 'object', selectedObject.id)">删除此物体</NButton>
          </template>

          <NEmpty v-if="!editorData" description="请先选择一个场景" class="mt-20px" />
        </div>
      </NTabPane>
    </NTabs>
  </div>
</template>

<style scoped>
.property-panel-tabs :deep(.n-tabs-nav) {
  padding: 0 12px;
}
</style>
