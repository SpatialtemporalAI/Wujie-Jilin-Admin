declare namespace Api.RobotConfig {
  type CommonSearchParams = Pick<Common.PaginatingCommonParams, 'page' | 'page_size'>;

  /** gRPC 推送状态：synced=已同步 / pending_retry=待重试 / disabled=未启用 */
  type GrpcStatus = 'synced' | 'pending_retry' | 'disabled';

  interface VoiceConfig {
    id?: number;
    robot_id: number;
    wake_word_enabled: boolean;
    wake_word: string;
    tts_voice: string;
    tts_speed: number;
    tts_volume: number;
    created_at?: string;
    updated_at?: string | null;
    grpc_status?: GrpcStatus;
  }

  interface FaceRecognition {
    id: number;
    person_name: string;
    photo_url: string;
    broadcast_text: string;
    /** 阿里云人脸库实体ID（= 本地记录 id 的字符串） */
    entity_id?: string;
    /** 阿里云人脸图片ID */
    face_id?: string;
    created_at: string;
    updated_at: string | null;
    grpc_status?: GrpcStatus;
  }

  interface FaceRecognitionCreate {
    person_name: string;
    photo_url: string;
    broadcast_text: string;
  }

  interface FaceRecognitionList {
    records: FaceRecognition[];
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  }

  interface TestWakeWordRequest {
    robot_id: number;
    text: string;
  }

  interface TestTTSRequest {
    robot_id: number;
    voice: string;
    speed: number;
    volume: number;
    text: string;
  }

  /** 通用配置更新响应（speed/battery/delete face 等不返回完整 ORM 的场景） */
  interface ConfigUpdateResponse {
    grpc_status?: GrpcStatus;
  }
}
