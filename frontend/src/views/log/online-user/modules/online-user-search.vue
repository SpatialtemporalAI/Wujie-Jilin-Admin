<script setup lang="ts">
import { useDebounceFn } from '@vueuse/core';
import { NInput } from 'naive-ui';
import { $t } from '@/locales';

defineOptions({
  name: 'OnlineUserSearch'
});

interface Emits {
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.SystemManage.OnlineUserSearchParams>('model', { required: true });

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
      v-model:value="model.username"
      :placeholder="$t('page.log.onlineUser.form.username')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NInput
      v-model:value="model.ip"
      :placeholder="$t('page.log.onlineUser.form.ip')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
  </div>
</template>

<style scoped></style>
