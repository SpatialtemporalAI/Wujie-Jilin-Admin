<template>
  <NDropdown
    v-if="tenantStore.isMultiTenantActive"
    trigger="click"
    :options="tenantOptions"
    :value="tenantStore.currentTenantId"
    @select="handleSelect"
  >
    <NButton quaternary size="small" :loading="tenantStore.loading">
      <template #icon>
        <icon-ic-outline-business />
      </template>
      {{ tenantStore.currentTenantName || $t('page.manage.tenant.selectTenant') }}
    </NButton>
  </NDropdown>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { NDropdown, NButton } from 'naive-ui';
import { $t } from '@/locales';
import { useTenantStore } from '../store/tenant';

const tenantStore = useTenantStore();

const tenantOptions = computed(() =>
  tenantStore.availableTenants.map(t => ({
    label: t.name,
    key: t.id
  }))
);

async function handleSelect(key: number) {
  await tenantStore.switchTenant(key);
}

onMounted(() => {
  tenantStore.loadTenants();
});
</script>
