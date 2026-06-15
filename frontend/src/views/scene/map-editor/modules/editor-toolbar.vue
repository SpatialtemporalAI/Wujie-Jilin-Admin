<script setup lang="ts">
import type { DrawingMode, HistoryEntry } from '../composables/useMapEditor';

interface Props {
  drawingMode: DrawingMode;
  canUndo: boolean;
  canRedo: boolean;
  isDirty: boolean;
  saving: boolean;
  historyList: HistoryEntry[];
}

defineProps<Props>();

const emit = defineEmits<{
  (e: 'update:drawingMode', mode: DrawingMode): void;
  (e: 'undo'): void;
  (e: 'redo'): void;
  (e: 'save'): void;
  (e: 'export', format: 'png' | 'jpeg' | 'webp'): void;
  (e: 'jump-to-history', type: 'undo' | 'redo', index: number): void;
}>();

const drawingModes: { key: DrawingMode; label: string; icon: string }[] = [
  { key: 'select', label: '选择', icon: 'ic:round-near-me' },
  { key: 'point-nav', label: '导航点', icon: 'ic:round-location-on' },
  { key: 'point-recv', label: '接待点', icon: 'ic:round-place' },
  { key: 'path', label: '路径', icon: 'ic:round-trending-flat' },
  { key: 'rect-obstacle', label: '障碍物', icon: 'ic:round-crop-square' },
  { key: 'polygon-restricted', label: '禁区', icon: 'ic:round-pentagon' },
];

function formatTime(ts: number): string {
  if (!ts) return '';
  const d = new Date(ts);
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  const ss = String(d.getSeconds()).padStart(2, '0');
  return `${hh}:${mm}:${ss}`;
}

function handleJump(entry: HistoryEntry) {
  if (entry.type === 'current') return;
  emit('jump-to-history', entry.type, entry.index);
}
</script>

<template>
  <div class="flex items-center gap-8px border-b border-gray-200 bg-white px-12px py-8px">
    <NButtonGroup size="small">
      <NButton
        v-for="mode in drawingModes"
        :key="mode.key"
        :type="drawingMode === mode.key ? 'primary' : 'default'"
        @click="emit('update:drawingMode', mode.key)"
      >
        <template #icon>
          <component :is="`icon-${mode.icon}`" />
        </template>
        {{ mode.label }}
      </NButton>
    </NButtonGroup>

    <NDivider vertical />

    <NButtonGroup size="small">
      <NButton :disabled="!canUndo" @click="emit('undo')">
        <template #icon><icon-ic-round-undo /></template>
        撤销
      </NButton>
      <NButton :disabled="!canRedo" @click="emit('redo')">
        <template #icon><icon-ic-round-redo /></template>
        重做
      </NButton>
    </NButtonGroup>

    <NPopover trigger="click" placement="bottom-start" :width="320">
      <template #trigger>
        <NButton size="small" title="操作历史">
          <template #icon><icon-ic-round-history /></template>
          历史
        </NButton>
      </template>
      <div class="flex flex-col gap-2px" style="max-height: 360px; overflow-y: auto;">
        <div
          v-for="entry in historyList"
          :key="entry.key"
          class="flex cursor-pointer items-center gap-8px rounded px-8px py-6px text-sm hover:bg-gray-100"
          :class="entry.type === 'current' ? 'bg-blue-50 font-medium text-blue-600' : entry.type === 'redo' ? 'text-gray-400' : ''"
          @click="handleJump(entry)"
        >
          <span v-if="entry.type === 'current'" class="text-blue-500">●</span>
          <span v-else-if="entry.type === 'redo'" class="text-gray-300">○</span>
          <span v-else class="text-gray-400">○</span>
          <span class="flex-1">{{ entry.description }}</span>
          <span v-if="entry.timestamp" class="text-xs text-gray-400">{{ formatTime(entry.timestamp) }}</span>
        </div>
        <div v-if="historyList.length <= 1" class="px-8px py-12px text-center text-xs text-gray-400">
          暂无操作历史
        </div>
      </div>
    </NPopover>

    <NDivider vertical />

    <NButton type="primary" size="small" :loading="saving" @click="emit('save')">
      <template #icon><icon-ic-round-save /></template>
      保存
    </NButton>

    <NDropdown
      :options="[
        { label: 'PNG', key: 'png' },
        { label: 'JPG', key: 'jpeg' },
        { label: 'WebP', key: 'webp' },
      ]"
      @select="(key: string) => emit('export', key as any)"
    >
      <NButton size="small">
        <template #icon><icon-ic-round-download /></template>
        导出
      </NButton>
    </NDropdown>

    <div class="flex-1" />
    <div v-if="isDirty" class="text-xs text-orange-500">有未保存的更改</div>
  </div>
</template>
