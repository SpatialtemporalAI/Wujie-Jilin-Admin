import { request } from '../request';
import { enableStatusToBoolean } from '@/utils/status';

/** get merchant list */
export function fetchGetMerchantList(params?: Api.Merchant.MerchantSearchParams) {
  return request<Api.Merchant.MerchantList>({
    url: '/admin/merchant/list',
    method: 'get',
    params
  });
}

/** get merchant detail (with bound robot ids) */
export function fetchGetMerchant(id: number) {
  return request<Api.Merchant.MerchantDetail>({
    url: `/admin/merchant/${id}`,
    method: 'get'
  });
}

/** create merchant (returns api_secret one-time) */
export function fetchCreateMerchant(data: Api.Merchant.MerchantCreate) {
  return request<Api.Merchant.ApiCredentials>({
    url: '/admin/merchant/add',
    method: 'post',
    data: {
      name: data.name,
      code: data.code,
      contact_name: data.contact_name,
      contact_phone: data.contact_phone,
      contact_email: data.contact_email,
      status: enableStatusToBoolean(data.status),
      remark: data.remark,
      robot_ids: data.robot_ids || []
    }
  });
}

/** update merchant */
export function fetchUpdateMerchant(id: number, data: Api.Merchant.MerchantUpdate) {
  return request<Api.Merchant.MerchantDetail>({
    url: `/admin/merchant/${id}`,
    method: 'put',
    data: {
      name: data.name,
      code: data.code,
      contact_name: data.contact_name,
      contact_phone: data.contact_phone,
      contact_email: data.contact_email,
      remark: data.remark,
      status: data.status ? enableStatusToBoolean(data.status) : undefined,
      robot_ids: data.robot_ids
    }
  });
}

/** delete merchant */
export function fetchDeleteMerchant(id: number) {
  return request<void>({
    url: `/admin/merchant/${id}`,
    method: 'delete'
  });
}

/** toggle merchant status */
export function fetchToggleMerchant(id: number, status: Api.Common.EnableStatus) {
  return request<Api.Merchant.MerchantDetail>({
    url: `/admin/merchant/${id}/toggle`,
    method: 'put',
    data: { status: enableStatusToBoolean(status) }
  });
}

/** reset merchant api key (returns new api_secret one-time) */
export function fetchResetMerchantApiKey(id: number) {
  return request<Api.Merchant.ApiCredentials>({
    url: `/admin/merchant/${id}/reset-api-key`,
    method: 'post'
  });
}

/** bind merchant robots (full replace) */
export function fetchBindMerchantRobots(id: number, robotIds: number[]) {
  return request<Api.Merchant.MerchantDetail>({
    url: `/admin/merchant/${id}/robots`,
    method: 'put',
    data: { robot_ids: robotIds }
  });
}
