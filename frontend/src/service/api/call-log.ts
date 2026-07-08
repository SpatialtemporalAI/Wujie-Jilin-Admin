import { request } from '../request';

/** ==================== 商户调用日志 API ==================== */

/** get merchant call log list */
export function fetchGetMerchantCallLogList(params?: Api.Merchant.CallLogSearchParams) {
  return request<Api.Merchant.CallLogList>({
    url: '/merchant/call-log/list',
    method: 'get',
    params
  });
}

/** get merchant call log detail */
export function fetchGetMerchantCallLog(logId: number) {
  return request<Api.Merchant.CallLogDetail>({
    url: `/merchant/call-log/${logId}`,
    method: 'get'
  });
}

/** delete merchant call log */
export function fetchDeleteMerchantCallLog(logId: number) {
  return request<void>({
    url: `/merchant/call-log/${logId}`,
    method: 'delete'
  });
}

/** batch delete merchant call logs */
export function fetchBatchDeleteMerchantCallLog(logIds: number[]) {
  return request<void>({
    url: '/merchant/call-log/batch/delete',
    method: 'delete',
    data: logIds
  });
}

/** clear old merchant call logs */
export function fetchClearMerchantCallLog(days?: number) {
  return request<void>({
    url: '/merchant/call-log/clear',
    method: 'delete',
    params: { days }
  });
}
