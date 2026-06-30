<script setup lang="ts">
import { useDebounceFn } from '@vueuse/core';
import { enableStatusOptions } from '@/constants/business';
import { $t } from '@/locales';

defineOptions({
  name: 'UserSearch'
});

interface Emits {
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.SystemManage.UserSearchParams>('model', { required: true });

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
      :placeholder="$t('page.manage.user.form.userName')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NInput
      v-model:value="model.nickname"
      :placeholder="$t('page.manage.user.form.nickName')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NInput
      v-model:value="model.phone"
      :placeholder="$t('page.manage.user.form.userPhone')"
      clearable
      :style="{ width: '160px' }"
      @update:value="debouncedSearch"
    />
    <NInput
      v-model:value="model.email"
      :placeholder="$t('page.manage.user.form.userEmail')"
      clearable
      :style="{ width: '200px' }"
      @update:value="debouncedSearch"
    />
    <NSelect
      v-model:value="model.status"
      :options="enableStatusOptions"
      :placeholder="$t('page.manage.user.form.userStatus')"
      clearable
      :style="{ width: '140px' }"
      @update:value="handleSearch"
    />
  </div>
</template>

<style scoped></style>
