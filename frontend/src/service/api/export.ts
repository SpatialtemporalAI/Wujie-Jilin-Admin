import axios from 'axios';
import { localStg } from '@/utils/storage';
import { getServiceBaseURL } from '@/utils/service';
import { request } from '../request';

const isHttpProxy = import.meta.env.DEV && import.meta.env.VITE_HTTP_PROXY === 'Y';
const { baseURL } = getServiceBaseURL(import.meta.env, isHttpProxy);

function getAuthHeader() {
  const token = localStg.get('token');
  return token || '';
}

/** 提交异步导出任务 */
export function fetchSubmitExportTask(data: Api.Export.ExportTaskSubmit) {
  return request<Api.Export.ExportTask>({
    url: '/admin/sys/export/task',
    method: 'post',
    data
  });
}

/** 获取当前用户的导出任务列表 */
export function fetchGetExportTaskList(params: { page: number; page_size: number; status?: string | null }) {
  return request<Api.Export.ExportTaskList>({
    url: '/admin/sys/export/task/list',
    method: 'get',
    params
  });
}

/** 查询导出任务状态 */
export function fetchGetExportTaskStatus(taskId: number) {
  return request<Api.Export.ExportTask>({
    url: `/admin/sys/export/task/${taskId}`,
    method: 'get'
  });
}

/** 下载导出文件（返回 Blob，走原生 axios，不经 request 封装） */
export async function fetchDownloadExportFile(taskId: number): Promise<Blob> {
  const response = await axios.get(`${baseURL}/admin/sys/export/task/${taskId}/download`, {
    responseType: 'blob',
    headers: { Authorization: getAuthHeader() }
  });
  return response.data;
}
