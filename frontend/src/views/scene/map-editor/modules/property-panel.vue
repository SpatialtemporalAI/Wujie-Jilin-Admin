<script setup lang="ts">
import { computed } from 'vue';
import type { SelectedElement } from '../composables/useMapEditor';

interface Props {
  editorData: Api.Scene.EditorMapData | null;
  selectedElement: SelectedElement | null;
  resolution: number;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'update-element', data: { type: string; id: number; updates: Record<string, any> }): void;
  (e: 'remove-element', type: 'annotation' | 'path' | 'object', id: number): void;
}>();

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
</script>

<template>
  <div class="flex h-full flex-col border-l border-gray-200 bg-white">
    <div class="border-b border-gray-200 px-12px py-10px">
      <span class="text-sm font-medium">属性面板</span>
    </div>

    <div class="flex-1 overflow-auto p-12px">
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
  </div>
</template>
