import { enableStatusToBoolean } from '@/utils/status';
import { request } from '../request';

/** ==================== 任务管理 API ==================== */

/** get task list */
export function fetchGetTaskList(params?: Api.Task.TaskSearchParams) {
  return request<Api.Task.TaskList>({
    url: '/admin/task/manage/list',
    method: 'get',
    params: {
      ...params,
      enabled: params?.enabled ? enableStatusToBoolean(params.enabled) : undefined
    }
  });
}

/** get task by id */
export function fetchGetTask(id: number) {
  return request<Api.Task.Task>({
    url: `/admin/task/manage/${id}`,
    method: 'get'
  });
}

/** create task */
export function fetchCreateTask(data: Api.Task.TaskCreate) {
  return request<Api.Task.Task>({
    url: '/admin/task/manage/add',
    method: 'post',
    data
  });
}

/** update task */
export function fetchUpdateTask(id: number, data: Api.Task.TaskUpdate) {
  return request<Api.Task.Task>({
    url: `/admin/task/manage/${id}`,
    method: 'put',
    data
  });
}

/** delete task */
export function fetchDeleteTask(id: number) {
  return request<void>({
    url: `/admin/task/manage/${id}`,
    method: 'delete'
  });
}

/** toggle task enabled */
export function fetchToggleTaskEnabled(id: number, enabled: boolean) {
  return request<Api.Task.Task>({
    url: `/admin/task/manage/${id}/toggle`,
    method: 'put',
    data: { enabled }
  });
}

/** get preset performance action options（八段锦） */
export function fetchGetPerformanceActions() {
  return request<Api.Task.PerformanceActionOption[]>({
    url: '/admin/task/manage/performance/actions',
    method: 'get'
  });
}

/** get performance music options（预设 + 当前用户上传，上传仅自己可见） */
export function fetchGetPerformanceMusic() {
  return request<Api.Task.PerformanceMusicOption[]>({
    url: '/admin/task/manage/performance/music',
    method: 'get'
  });
}

/** upload performance music（mp3/wav ≤20MB，超过4分钟自动截取前4分钟） */
export function fetchUploadPerformanceMusic(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return request<Api.Task.PerformanceMusicUploadResult>({
    url: '/admin/task/manage/performance/music/upload',
    method: 'post',
    data: formData
  });
}

/** delete uploaded performance music（仅自己上传的；被任务引用的不可删） */
export function fetchDeletePerformanceMusic(fileId: number) {
  return request<void>({
    url: `/admin/task/manage/performance/music/${fileId}`,
    method: 'delete'
  });
}

/** ==================== 任务执行记录 API（新版，对应 task_execution_record 表） ==================== */

/** start task execution (new record table) */
export function fetchStartExecutionRecord(taskId: number, payload: Api.Task.TaskExecutionRecordStartIn) {
  return request<Api.Task.TaskStartResult>({
    url: `/admin/task/execution-record/${taskId}/start`,
    method: 'post',
    data: payload
  });
}

/** start or resume task execution
 * 若任务有 paused 记录则恢复，否则创建新执行记录
 */
export function fetchStartOrResumeExecution(taskId: number, payload: Api.Task.TaskExecutionRecordStartIn) {
  return request<Api.Task.TaskStartResult>({
    url: `/admin/task/execution-record/start-or-resume/${taskId}`,
    method: 'post',
    data: payload
  });
}

/** pause execution record */
export function fetchPauseExecutionRecord(recordId: number) {
  return request<Api.Task.TaskExecutionRecord>({
    url: `/admin/task/execution-record/${recordId}/pause`,
    method: 'post'
  });
}

/** pause all running/pending executions of a task */
export function fetchPauseExecutionByTask(taskId: number) {
  return request<void>({
    url: `/admin/task/execution-record/pause-by-task/${taskId}`,
    method: 'post'
  });
}

/** resume execution record */
export function fetchResumeExecutionRecord(recordId: number) {
  return request<Api.Task.TaskExecutionRecord>({
    url: `/admin/task/execution-record/${recordId}/resume`,
    method: 'post'
  });
}

/** stop execution record */
export function fetchStopExecutionRecord(recordId: number) {
  return request<Api.Task.TaskExecutionRecord>({
    url: `/admin/task/execution-record/${recordId}/stop`,
    method: 'post'
  });
}

/** get active execution records */
export function fetchGetActiveExecutionRecords(params?: Api.Task.TaskExecutionRecordSearchParams) {
  return request<Api.Task.TaskExecutionRecordList>({
    url: '/admin/task/execution-record/active',
    method: 'get',
    params
  });
}

/** get execution record history */
export function fetchGetExecutionRecordHistory(params?: Api.Task.TaskExecutionRecordSearchParams) {
  return request<Api.Task.TaskExecutionRecordList>({
    url: '/admin/task/execution-record/history',
    method: 'get',
    params
  });
}

/** get execution record detail */
export function fetchGetExecutionRecordDetail(recordId: number) {
  return request<Api.Task.TaskExecutionRecordDetail>({
    url: `/admin/task/execution-record/detail/${recordId}`,
    method: 'get'
  });
}
