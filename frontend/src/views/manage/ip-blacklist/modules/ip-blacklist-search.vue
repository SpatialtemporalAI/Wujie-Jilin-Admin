<script setup lang="ts">
import { NInput, NSelect } from 'naive-ui';
import { useDebounceFn } from '@vueuse/core';
import { $t } from '@/locales';

defineOptions({
  name: 'IpBlacklistSearch'
});

interface Emits {
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.SystemManage.IpBlacklistSearchParams>('model', { required: true });

const typeOptions = [
  { label: $t('page.manage.ipBlacklist.typePermanent'), value: 'permanent' },
  { label: $t('page.manage.ipBlacklist.typeTemporary'), value: 'temporary' }
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
      v-model:value="model.ip"
      :placeholder="$t('page.manage.ipBlacklist.form.ip')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NSelect
      v-model:value="model.type"
      :options="typeOptions"
      :placeholder="$t('page.manage.ipBlacklist.form.type')"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
  </div>
</template>

<style scoped></style>
