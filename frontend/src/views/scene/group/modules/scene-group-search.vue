<script setup lang="ts">
import { useDebounceFn } from '@vueuse/core';

defineOptions({
  name: 'SceneGroupSearch'
});

interface Emits {
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.Scene.SceneGroupSearchParams>('model', { required: true });

function handleSearch() {
  model.value.page = 1;
  emit('search');
}

const debouncedSearch = useDebounceFn(() => {
  handleSearch();
}, 500);
</script>

<template>
  <div class="flex-y-center flex-wrap gap-12px">
    <NInput
      v-model:value="model.name"
      placeholder="分组名称"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
  </div>
</template>

<style scoped></style>
