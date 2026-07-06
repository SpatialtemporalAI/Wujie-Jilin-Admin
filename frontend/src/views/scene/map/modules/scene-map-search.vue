<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useDebounceFn } from '@vueuse/core';
import { fetchGetAllSceneGroups } from '@/service/api';

defineOptions({
  name: 'SceneMapSearch'
});

interface Emits {
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.Scene.SceneMapSearchParams>('model', { required: true });

/** 分组选项 */
const groupOptions = ref<{ label: string; value: number }[]>([]);

async function loadGroupOptions() {
  const { data } = await fetchGetAllSceneGroups();
  if (data) {
    groupOptions.value = data.map(item => ({
      label: item.name,
      value: item.id
    }));
  }
}

function handleSearch() {
  model.value.page = 1;
  emit('search');
}

const debouncedSearch = useDebounceFn(() => {
  handleSearch();
}, 500);

onMounted(() => {
  loadGroupOptions();
});
</script>

<template>
  <div class="flex-y-center flex-wrap gap-12px">
    <NInput
      v-model:value="model.name"
      placeholder="地图名称"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NSelect
      v-model:value="model.group_id"
      :options="groupOptions"
      placeholder="所属分组"
      clearable
      :style="{ width: '160px' }"
      @update:value="handleSearch"
    />
  </div>
</template>

<style scoped></style>
