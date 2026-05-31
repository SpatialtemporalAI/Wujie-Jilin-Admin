import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import { localStg } from '@/utils/storage';
import { fetchGetMyTenants, fetchSelectTenant } from '../api/tenant';

interface TenantInfo {
  id: number;
  name: string;
  code: string;
  status: string;
}

export const useTenantStore = defineStore('plugin-multi-tenant', () => {
  const currentTenantId = ref<number | null>(localStg.get('currentTenantId') as number | null);
  const currentTenantName = ref<string | null>(localStg.get('currentTenantName') as string | null);
  const availableTenants = ref<TenantInfo[]>([]);
  const loading = ref(false);

  const isMultiTenantActive = computed(() => availableTenants.value.length > 0);
  const currentTenant = computed(() =>
    availableTenants.value.find(t => t.id === currentTenantId.value) || null
  );

  function setCurrentTenant(id: number, name: string) {
    currentTenantId.value = id;
    currentTenantName.value = name;
    localStg.set('currentTenantId', id);
    localStg.set('currentTenantName', name);
  }

  async function loadTenants() {
    try {
      const { data, error } = await fetchGetMyTenants();
      if (!error && data) {
        availableTenants.value = data;
        // 如果只有一个租户，自动选择
        if (data.length === 1 && !currentTenantId.value) {
          setCurrentTenant(data[0].id, data[0].name);
        }
      }
    } catch {
      // 插件未安装或无权限时静默失败
    }
  }

  async function switchTenant(tenantId: number) {
    loading.value = true;
    try {
      const { data, error } = await fetchSelectTenant(tenantId);
      if (!error && data) {
        // 更新 token
        localStg.set('token', data.access_token);
        localStg.set('refreshToken', data.refresh_token);
        // 更新当前租户
        const tenant = availableTenants.value.find(t => t.id === tenantId);
        if (tenant) {
          setCurrentTenant(tenant.id, tenant.name);
        }
        // 刷新页面以重新加载路由和权限
        window.location.reload();
        return true;
      }
      return false;
    } catch {
      return false;
    } finally {
      loading.value = false;
    }
  }

  function clearTenant() {
    currentTenantId.value = null;
    currentTenantName.value = null;
    availableTenants.value = [];
    localStg.remove('currentTenantId');
    localStg.remove('currentTenantName');
  }

  return {
    currentTenantId,
    currentTenantName,
    availableTenants,
    loading,
    isMultiTenantActive,
    currentTenant,
    setCurrentTenant,
    loadTenants,
    switchTenant,
    clearTenant
  };
});
