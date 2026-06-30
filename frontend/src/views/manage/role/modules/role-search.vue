<script setup lang="ts">
import { useDebounceFn } from '@vueuse/core';
import { enableStatusOptions } from '@/constants/business';
import { $t } from '@/locales';

defineOptions({
  name: 'RoleSearch'
});

interface Emits {
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.SystemManage.RoleSearchParams>('model', { required: true });

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
      :placeholder="$t('page.manage.role.form.roleName')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NSelect
      v-model:value="model.status"
      :options="enableStatusOptions"
      :placeholder="$t('page.manage.role.form.roleStatus')"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
  </div>
</template>

<style scoped></style>
