<script setup lang="ts">
import { ref, computed } from 'vue';

interface Props {
  sceneList: Api.Scene.SceneMap[];
  selectedMapId: number | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'select', mapId: number): void;
  (e: 'add'): void;
  (e: 'delete', mapId: number): void;
}>();

const searchText = ref('');

const filteredList = computed(() => {
  if (!searchText.value) return props.sceneList;
  return props.sceneList.filter(m => m.name.includes(searchText.value));
});
</script>

<template>
  <div class="flex h-full flex-col border-r border-gray-200 bg-white">
    <div class="border-b border-gray-200 p-12px">
      <div class="mb-8px flex items-center justify-between">
        <span class="text-sm font-medium">场景列表</span>
        <NButton size="tiny" type="primary" @click="emit('add')">
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
        @click="emit('select', map.id)"
      >
        <div class="min-w-0 flex-1">
          <div class="truncate">{{ map.name }}</div>
          <div class="text-xs text-gray-400">
            {{ map.width && map.height ? `${map.width}×${map.height}` : '未设置尺寸' }}
          </div>
        </div>
        <NPopconfirm @positive-click.stop="emit('delete', map.id)">
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
</template>
