import { request } from '../request';

/** 获取系统实时指标 */
export function fetchGetSystemMetrics() {
  return request<Api.Monitor.SystemMetrics>({
    url: '/admin/sys/monitor/metrics',
    method: 'get'
  });
}

/** 获取API统计信息 */
export function fetchGetApiStats(params?: { minutes?: number }) {
  return request<Api.Monitor.ApiStats[]>({
    url: '/admin/sys/monitor/api-stats',
    method: 'get',
    params
  });
}
