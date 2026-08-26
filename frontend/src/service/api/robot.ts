import { enableStatusToBoolean } from '@/utils/status';
import { request } from '../request';

/** ==================== 机器人型号管理 API ==================== */

/** get robot model list */
export function fetchGetRobotModelList(params?: Api.Robot.RobotModelSearchParams) {
  return request<Api.Robot.RobotModelList>({
    url: '/admin/robot/model/list',
    method: 'get',
    params
  });
}

/** get all robot models (for dropdown) */
export function fetchGetAllRobotModels() {
  return request<Api.Robot.AllRobotModel[]>({
    url: '/admin/robot/model/all',
    method: 'get'
  });
}

/** get robot model by id */
export function fetchGetRobotModel(id: number) {
  return request<Api.Robot.RobotModel>({
    url: `/admin/robot/model/${id}`,
    method: 'get'
  });
}

/** create robot model */
export function fetchCreateRobotModel(data: Api.Robot.RobotModelCreate) {
  return request<Api.Robot.RobotModel>({
    url: '/admin/robot/model/add',
    method: 'post',
    data: {
      ...data,
      status: enableStatusToBoolean(data.status)
    }
  });
}

/** update robot model */
export function fetchUpdateRobotModel(id: number, data: Api.Robot.RobotModelUpdate) {
  return request<Api.Robot.RobotModel>({
    url: `/admin/robot/model/${id}`,
    method: 'put',
    data: {
      ...data,
      ...(data.status !== undefined ? { status: enableStatusToBoolean(data.status) } : {})
    }
  });
}

/** delete robot model */
export function fetchDeleteRobotModel(id: number) {
  return request<void>({
    url: `/admin/robot/model/${id}`,
    method: 'delete'
  });
}

/** ==================== 机器人管理 API ==================== */

/** get robot list */
export function fetchGetRobotList(params?: Api.Robot.RobotSearchParams) {
  return request<Api.Robot.RobotList>({
    url: '/admin/robot/manage/list',
    method: 'get',
    params
  });
}

/** get all robots (for dropdown) */
export function fetchGetAllRobots() {
  return request<Api.Robot.AllRobot[]>({
    url: '/admin/robot/manage/all',
    method: 'get'
  });
}

/** get robot by id */
export function fetchGetRobot(id: number) {
  return request<Api.Robot.Robot>({
    url: `/admin/robot/manage/${id}`,
    method: 'get'
  });
}

/** create robot */
export function fetchCreateRobot(data: Api.Robot.RobotCreate) {
  return request<Api.Robot.Robot>({
    url: '/admin/robot/manage/add',
    method: 'post',
    data
  });
}

/** update robot */
export function fetchUpdateRobot(id: number, data: Api.Robot.RobotUpdate) {
  return request<Api.Robot.Robot>({
    url: `/admin/robot/manage/${id}`,
    method: 'put',
    data
  });
}

/** delete robot */
export function fetchDeleteRobot(id: number) {
  return request<void>({
    url: `/admin/robot/manage/${id}`,
    method: 'delete'
  });
}

/** 查询机器人服务器自启动状态（面板：已启动/启动中/启动失败/未配置/未知） */
export function fetchGetRobotSlotStatus(id: number) {
  return request<Api.Robot.SlotStatusData>({
    url: `/admin/robot/manage/${id}/slot-status`,
    method: 'get'
  });
}

/** 重启机器人服务器自启动（面板按序补齐 zenoh -> middleware） */
export function fetchRestartRobotSlot(id: number) {
  return request<Api.Robot.SlotStatusData>({
    url: `/admin/robot/manage/${id}/slot-restart`,
    method: 'post'
  });
}

/** update robot grpc config (agent + middleware + ros) */
export function fetchUpdateRobotGrpcConfig(id: number, data: Api.Robot.RobotGrpcConfig) {
  return request<Api.Robot.Robot>({
    url: `/admin/robot/manage/${id}/grpc-config`,
    method: 'put',
    data: { grpc_config: data }
  });
}

/** update robot map binding (scene map editor only — uses scene:map-editor:edit permission) */
export function fetchUpdateRobotMapBinding(id: number, data: { map_id: number | null }) {
  return request<Api.Robot.Robot>({
    url: `/admin/robot/manage/${id}/bind-map`,
    method: 'put',
    data
  });
}

/** start/stop video monitoring on a robot's middleware via gRPC (enabled=true 启动 / false 停止) */
export function fetchSetVideoMonitoring(robotId: number, enabled: boolean) {
  return request<void>({
    url: `/admin/robot/config/video-monitoring/${robotId}`,
    method: 'post',
    data: { enabled } satisfies Api.Robot.VideoMonitoringControl
  });
}

/** open robot video monitoring and get LiveKit connection ticket */
export function fetchOpenVideoMonitoring(robotId: number) {
  return request<Api.Robot.VideoMonitoringTicket>({
    url: `/admin/robot/config/video-monitoring/${robotId}`,
    method: 'post',
    data: { enabled: true } satisfies Api.Robot.VideoMonitoringControl
  });
}

/** close robot video monitoring for the given viewer session */
export function fetchCloseVideoMonitoring(robotId: number, viewerId: string) {
  return request<void>({
    url: `/admin/robot/config/video-monitoring/${robotId}`,
    method: 'post',
    data: { enabled: false, viewer_id: viewerId } satisfies Api.Robot.VideoMonitoringControl
  });
}

/** refresh viewer heartbeat TTL */
export function fetchVideoMonitoringHeartbeat(robotId: number, viewerId: string) {
  return request<void>({
    url: `/admin/robot/config/video-monitoring/${robotId}/heartbeat`,
    method: 'post',
    data: { viewer_id: viewerId } satisfies Api.Robot.VideoMonitoringHeartbeat
  });
}

/** ==================== 机器人状态记录 API (只读) ==================== */

/** get robot status records */
export function fetchGetRobotStatusRecords(robotId: number, params?: Api.Robot.CommonSearchParams) {
  return request<Api.Robot.RobotStatusRecordList>({
    url: `/admin/robot/manage/${robotId}/status/list`,
    method: 'get',
    params
  });
}

/** get latest robot status record */
export function fetchGetLatestRobotStatus(robotId: number) {
  return request<Api.Robot.RobotStatusRecord>({
    url: `/admin/robot/manage/${robotId}/status/latest`,
    method: 'get'
  });
}

/** get robot real-time locations bound to a map (for map editor canvas) */
export function fetchGetMapRobotLocations(mapId: number) {
  return request<Api.Robot.RobotLocationItem[]>({
    url: `/admin/robot/manage/map/${mapId}/robot-locations`,
    method: 'get'
  });
}
