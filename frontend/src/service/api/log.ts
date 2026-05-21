import { request } from '../request';

/** ==================== 登录日志 API ==================== */

/** get login log list */
export function fetchGetLoginLogList(params?: Api.SystemManage.LoginLogSearchParams) {
  return request<Api.SystemManage.LoginLogList>({
    url: '/admin/sys/login-log/list',
    method: 'get',
    params
  });
}

/** delete login log */
export function fetchDeleteLoginLog(logId: number) {
  return request<void>({
    url: `/admin/sys/login-log/${logId}`,
    method: 'delete'
  });
}

/** batch delete login logs */
export function fetchBatchDeleteLoginLog(logIds: number[]) {
  return request<void>({
    url: '/admin/sys/login-log/batch/delete',
    method: 'delete',
    data: logIds
  });
}

/** clear old login logs */
export function fetchClearLoginLog(days?: number) {
  return request<void>({
    url: '/admin/sys/login-log/clear',
    method: 'delete',
    params: { days }
  });
}

/** ==================== 操作日志 API ==================== */

/** get operation log list */
export function fetchGetOperationLogList(params?: Api.SystemManage.OperationLogSearchParams) {
  return request<Api.SystemManage.OperationLogList>({
    url: '/admin/sys/operation-log/list',
    method: 'get',
    params
  });
}

/** get operation log detail */
export function fetchGetOperationLogDetail(logId: number) {
  return request<Api.SystemManage.OperationLogDetail>({
    url: `/admin/sys/operation-log/${logId}`,
    method: 'get'
  });
}

/** delete operation log */
export function fetchDeleteOperationLog(logId: number) {
  return request<void>({
    url: `/admin/sys/operation-log/${logId}`,
    method: 'delete'
  });
}

/** batch delete operation logs */
export function fetchBatchDeleteOperationLog(logIds: number[]) {
  return request<void>({
    url: '/admin/sys/operation-log/batch/delete',
    method: 'delete',
    data: logIds
  });
}

/** clear old operation logs */
export function fetchClearOperationLog(days?: number) {
  return request<void>({
    url: '/admin/sys/operation-log/clear',
    method: 'delete',
    params: { days }
  });
}
