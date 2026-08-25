import { request } from '../request';

/** ==================== 机器人参数配置 API ==================== */

/**
 * 触发实时 gRPC 下发（语音保存/测试、速度、电量）的接口单请求超时。
 * 对齐后端 settings.GRPC.TIMEOUT_SECONDS=30s：避免前端先于后端 RPC 超时。
 */
const ROBOT_CONFIG_GRPC_TIMEOUT_MS = 30 * 1000;

/** 获取语音合成配置 */
export function fetchGetVoiceConfig(robotId: number) {
  return request<Api.RobotConfig.VoiceConfig>({
    url: '/admin/robot/config/voice',
    method: 'get',
    params: { robot_id: robotId }
  });
}

/** 保存语音合成配置 */
export function fetchSaveVoiceConfig(data: Api.RobotConfig.VoiceConfig) {
  return request<Api.RobotConfig.VoiceConfig>({
    url: '/admin/robot/config/voice',
    method: 'post',
    timeout: ROBOT_CONFIG_GRPC_TIMEOUT_MS,
    data
  });
}

/** 测试唤醒词 */
export function fetchTestWakeWord(data: Api.RobotConfig.TestWakeWordRequest) {
  return request<void>({
    url: '/admin/robot/config/voice/test-wake-word',
    method: 'post',
    timeout: ROBOT_CONFIG_GRPC_TIMEOUT_MS,
    data
  });
}

/** 测试TTS语音合成 */
export function fetchTestTTS(data: Api.RobotConfig.TestTTSRequest) {
  return request<void>({
    url: '/admin/robot/config/voice/test-tts',
    method: 'post',
    timeout: ROBOT_CONFIG_GRPC_TIMEOUT_MS,
    data
  });
}

/** 上传人脸识别人像 */
export function fetchUploadFacePhoto(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return request<Api.FileManage.FileInfo>({
    url: '/admin/robot/config/face/upload',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  });
}

/** 获取人脸识别TTS配置列表 */
export function fetchGetFaceRecognitionList(params?: Api.RobotConfig.CommonSearchParams) {
  return request<Api.RobotConfig.FaceRecognitionList>({
    url: '/admin/robot/config/face',
    method: 'get',
    params
  });
}

/** 创建人脸识别TTS配置 */
export function fetchCreateFaceRecognition(data: Api.RobotConfig.FaceRecognitionCreate) {
  return request<Api.RobotConfig.FaceRecognition>({
    url: '/admin/robot/config/face',
    method: 'post',
    data
  });
}

/** 更新人脸识别TTS配置 */
export function fetchUpdateFaceRecognition(id: number, data: Api.RobotConfig.FaceRecognitionCreate) {
  return request<Api.RobotConfig.FaceRecognition>({
    url: `/admin/robot/config/face/${id}`,
    method: 'put',
    data
  });
}

/** 删除人脸识别TTS配置 */
export function fetchDeleteFaceRecognition(id: number) {
  return request<Api.RobotConfig.ConfigUpdateResponse>({
    url: `/admin/robot/config/face/${id}`,
    method: 'delete'
  });
}

/** ==================== 行走速度 / 电量阈值配置 ==================== */

/** 更新机器人行走速度等级 */
export function fetchUpdateSpeedLevel(robotId: number, speedLevel: string | null) {
  return request<Api.RobotConfig.ConfigUpdateResponse>({
    url: `/admin/robot/config/speed-level/${robotId}`,
    method: 'put',
    timeout: ROBOT_CONFIG_GRPC_TIMEOUT_MS,
    data: { speed_level: speedLevel }
  });
}

/** 更新机器人电量报警阈值 */
export function fetchUpdateBatteryThreshold(robotId: number, batteryThreshold: number) {
  return request<Api.RobotConfig.ConfigUpdateResponse>({
    url: `/admin/robot/config/battery-threshold/${robotId}`,
    method: 'put',
    timeout: ROBOT_CONFIG_GRPC_TIMEOUT_MS,
    data: { battery_threshold: batteryThreshold }
  });
}

/** 更新机器人打招呼模式（wave-招手 / no_wave-无招手） */
export function fetchUpdateGreetingMode(robotId: number, greetingMode: 'wave' | 'no_wave') {
  return request<Api.RobotConfig.ConfigUpdateResponse>({
    url: `/admin/robot/config/greeting-mode/${robotId}`,
    method: 'put',
    timeout: ROBOT_CONFIG_GRPC_TIMEOUT_MS,
    data: { greeting_mode: greetingMode }
  });
}
