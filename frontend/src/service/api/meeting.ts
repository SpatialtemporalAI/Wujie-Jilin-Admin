import { request } from '../request';

/** ==================== 声纹注册 ==================== */

/** 声纹页机器人列表 */
export function fetchGetVoiceprintRobots() {
  return request<Api.Meeting.VoiceprintRobot[]>({
    url: '/admin/meeting/voiceprint/robots',
    method: 'get'
  });
}

/** 声纹页概览（会议模式 + 已注册数量） */
export function fetchGetVoiceprintOverview(robotId: number) {
  return request<Api.Meeting.VoiceprintOverview>({
    url: '/admin/meeting/voiceprint/overview',
    method: 'get',
    params: { robot_id: robotId }
  });
}

/** 声纹注册记录列表 */
export function fetchGetVoiceprintList(params: Api.Meeting.VoiceprintSearchParams) {
  return request<Api.Meeting.VoiceprintList>({
    url: '/admin/meeting/voiceprint/list',
    method: 'get',
    params
  });
}

/** 上传录音并注册声纹 */
export function fetchRegisterVoiceprint(payload: Api.Meeting.VoiceprintRegisterPayload) {
  const formData = new FormData();
  formData.append('robot_id', String(payload.robot_id));
  formData.append('role_name', payload.role_name);
  formData.append('role_type', payload.role_type);
  formData.append('method', payload.method);
  formData.append('transcript_hint', payload.transcript_hint || '');
  formData.append('audio', payload.audio);
  return request<Api.Meeting.VoiceprintRecord>({
    url: '/admin/meeting/voiceprint/register',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

/** 删除声纹 */
export function fetchDeleteVoiceprint(recordId: number) {
  return request<void>({
    url: `/admin/meeting/voiceprint/${recordId}`,
    method: 'delete'
  });
}

/** 切换会议模式 */
export function fetchUpdateMeetingMode(payload: Api.Meeting.MeetingModePayload) {
  return request<Api.Meeting.MeetingModeStatus>({
    url: '/admin/meeting/voiceprint/meeting-mode',
    method: 'put',
    data: payload
  });
}

/** ==================== 会议纪要 ==================== */

/** 会议纪要列表 */
export function fetchGetMinuteList(params: Api.Meeting.MinuteSearchParams) {
  return request<Api.Meeting.MinuteList>({
    url: '/admin/meeting/minutes/list',
    method: 'get',
    params
  });
}

/** 回收站列表 */
export function fetchGetMinuteTrash(params: Api.Meeting.MinuteSearchParams) {
  return request<Api.Meeting.MinuteList>({
    url: '/admin/meeting/minutes/trash',
    method: 'get',
    params
  });
}

/** 会议纪要详情 */
export function fetchGetMinuteDetail(minuteId: number) {
  return request<Api.Meeting.MinuteDetail>({
    url: `/admin/meeting/minutes/${minuteId}`,
    method: 'get'
  });
}

/** 改派逐字稿发言人 */
export function fetchUpdateSegmentSpeaker(segmentId: number, speakerId: number) {
  return request<void>({
    url: `/admin/meeting/minutes/segments/${segmentId}/speaker`,
    method: 'put',
    data: { speaker_id: speakerId }
  });
}

/** 导出会议纪要 */
export function fetchExportMinute(minuteId: number, format: 'md' | 'txt' = 'md') {
  return request<Api.Meeting.MinuteExportData>({
    url: `/admin/meeting/minutes/${minuteId}/export`,
    method: 'get',
    params: { format }
  });
}

/** 删除会议纪要（移入回收站） */
export function fetchDeleteMinute(minuteId: number) {
  return request<void>({
    url: `/admin/meeting/minutes/${minuteId}`,
    method: 'delete'
  });
}

/** 恢复会议纪要 */
export function fetchRestoreMinute(minuteId: number) {
  return request<void>({
    url: `/admin/meeting/minutes/${minuteId}/restore`,
    method: 'post'
  });
}

/** 彻底删除会议纪要 */
export function fetchPurgeMinute(minuteId: number) {
  return request<void>({
    url: `/admin/meeting/minutes/${minuteId}/purge`,
    method: 'delete'
  });
}

/** 清空回收站 */
export function fetchClearMinuteTrash() {
  return request<{ purged_count: number }>({
    url: '/admin/meeting/minutes/trash/clear',
    method: 'delete'
  });
}
