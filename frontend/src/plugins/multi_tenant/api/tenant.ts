import { request } from '@/service/request';

/** 获取当前用户可用的租户列表 */
export function fetchGetMyTenants() {
  return request<{ id: number; name: string; code: string; status: string }[]>({
    url: '/admin/sys/tenant/all',
    method: 'get'
  });
}

/** 获取租户列表 */
export function fetchGetTenantList(params?: {
  page?: number;
  page_size?: number;
  name?: string;
  code?: string;
  status?: string;
}) {
  const filtered: Record<string, any> = {};
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== null && value !== undefined && value !== '') {
        if (key === 'status') {
          filtered[key] = value === '1' ? 'true' : 'false';
        } else {
          filtered[key] = value;
        }
      }
    }
  }
  return request({
    url: '/admin/sys/tenant/list',
    method: 'get',
    params: filtered
  });
}

/** 获取租户详情 */
export function fetchGetTenant(tenantId: number) {
  return request({
    url: `/admin/sys/tenant/${tenantId}`,
    method: 'get'
  });
}

/** 创建租户 */
export function fetchCreateTenant(data: {
  name: string;
  code: string;
  description?: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  max_users?: number;
}) {
  return request({
    url: '/admin/sys/tenant/add',
    method: 'post',
    data
  });
}

/** 更新租户 */
export function fetchUpdateTenant(
  tenantId: number,
  data: {
    name?: string;
    description?: string;
    contact_name?: string;
    contact_email?: string;
    contact_phone?: string;
    max_users?: number;
  }
) {
  return request({
    url: `/admin/sys/tenant/${tenantId}`,
    method: 'put',
    data
  });
}

/** 删除租户 */
export function fetchDeleteTenant(tenantId: number) {
  return request({
    url: `/admin/sys/tenant/${tenantId}`,
    method: 'delete'
  });
}

/** 更新租户状态 */
export function fetchUpdateTenantStatus(tenantId: number, status: boolean) {
  return request({
    url: `/admin/sys/tenant/${tenantId}/status`,
    method: 'put',
    params: { status }
  });
}

/** 获取租户用户列表 */
export function fetchGetTenantUsers(tenantId: number) {
  return request({
    url: `/admin/sys/tenant/${tenantId}/users`,
    method: 'get'
  });
}

/** 分配用户到租户 */
export function fetchAssignUserToTenant(
  tenantId: number,
  data: { user_id: number; role?: string }
) {
  return request({
    url: `/admin/sys/tenant/${tenantId}/users`,
    method: 'post',
    data
  });
}

/** 从租户移除用户 */
export function fetchRemoveUserFromTenant(tenantId: number, userId: number) {
  return request({
    url: `/admin/sys/tenant/${tenantId}/users/${userId}`,
    method: 'delete'
  });
}

/** 选择/切换租户 */
export function fetchSelectTenant(tenantId: number) {
  return request({
    url: '/admin/sys/auth/select-tenant',
    method: 'post',
    data: { tenant_id: tenantId }
  });
}
