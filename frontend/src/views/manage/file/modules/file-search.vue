<script setup lang="ts">
import { NInput, NSelect } from 'naive-ui';
import { useDebounceFn } from '@vueuse/core';
import { $t } from '@/locales';

defineOptions({
  name: 'FileSearch'
});

interface Emits {
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.FileManage.FileSearchParams>('model', { required: true });

const storagePlatformOptions = [
  { label: $t('page.manage.file.platform.local'), value: 'local' },
  { label: $t('page.manage.file.platform.oss'), value: 'oss' }
];

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
      v-model:value="model.original_name"
      :placeholder="$t('page.manage.file.form.fileName')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NInput
      v-model:value="model.extension"
      :placeholder="$t('page.manage.file.form.fileExtension')"
      clearable
      :style="{ width: '140px' }"
      @update:value="debouncedSearch"
    />
    <NSelect
      v-model:value="model.storage_platform"
      :options="storagePlatformOptions"
      :placeholder="$t('page.manage.file.form.storagePlatform')"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
  </div>
</template>

<style scoped></style>
