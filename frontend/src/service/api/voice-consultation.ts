import { request } from '../request';

/** ==================== 语音问诊 API ==================== */

/** get voice consultation session list */
export function fetchGetVoiceConsultationSessionList(params?: Api.VoiceConsultation.SessionSearchParams) {
  return request<Api.VoiceConsultation.SessionList>({
    url: '/admin/voice-consultation/sessions/list',
    method: 'get',
    params
  });
}

/** get voice consultation stats */
export function fetchGetVoiceConsultationStats(params?: Api.VoiceConsultation.SessionSearchParams) {
  return request<Api.VoiceConsultation.Stats>({
    url: '/admin/voice-consultation/sessions/stats',
    method: 'get',
    params
  });
}

/** get voice consultation session detail */
export function fetchGetVoiceConsultationSession(sessionId: number) {
  return request<Api.VoiceConsultation.SessionDetail>({
    url: `/admin/voice-consultation/sessions/${sessionId}`,
    method: 'get'
  });
}
