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
      {{ tenantStore.currentTenantName || '选择租户' }}
    </NButton>
  </NDropdown>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { NDropdown, NButton } from 'naive-ui';
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
