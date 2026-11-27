declare namespace Api {
  /**
   * Namespace Api.Meeting
   *
   * 会议管理：声纹注册 / 会议纪要 / 蓝牙设备连接
   */
  namespace Meeting {
    type CommonSearchParams = Pick<Common.PaginatingCommonParams, 'page' | 'page_size'>;

    /** ==================== 声纹注册 ==================== */

    type VoiceprintRobot = {
      id: number;
      name: string;
      serial_number: string;
      model_name: string | null;
      robot_status: 'online' | 'offline' | 'inactive';
      meeting_mode: boolean;
      registered_count: number;
    };

    type VoiceprintStatus = 'success' | 'processing' | 'failed';

    type VoiceprintRecord = {
      id: number;
      robot_id: number;
      robot_name: string | null;
      role_name: string;
      role_type: string;
      method: string;
      status: VoiceprintStatus;
      voiceprint_id: string | null;
      transcript: string | null;
      score: number | null;
      clarity: number | null;
      match_score: number | null;
      noise_level: string | null;
      sample_url: string | null;
      error_msg: string | null;
      created_at: string;
    };

    type VoiceprintSearchParams = CommonType.RecordNullable<
      Pick<VoiceprintRecord, 'robot_id' | 'status'> & {
        keyword?: string;
      } & CommonSearchParams
    >;

    type VoiceprintList = Common.PaginatingQueryRecord<VoiceprintRecord>;

    type VoiceprintOverview = {
      meeting_mode: boolean;
      registered_count: number;
    };

    type VoiceprintRegisterPayload = {
      robot_id: number;
      role_name: string;
      role_type: string;
      method: string;
      transcript_hint?: string;
      audio: File;
    };

    type MeetingModePayload = {
      robot_id: number;
      enabled: boolean;
    };

    type MeetingModeStatus = {
      meeting_mode: boolean;
      registered_count: number;
    };

    /** ==================== 会议纪要 ==================== */

    type MinuteSpeaker = {
      id: number;
      speaker_key: string;
      name: string;
      role: string | null;
      color: string | null;
      match_score: number | null;
      voiceprint_id: string | null;
      sort: number;
    };

    type MinuteSegment = {
      id: number;
      seq: number;
      speaker_id: number | null;
      speaker_key: string | null;
      timecode: string | null;
      start_seconds: number | null;
      text: string;
      confidence: number | null;
      need_confirm: boolean;
      audio_url: string | null;
    };

    type MinuteListItem = {
      id: number;
      meeting_no: string;
      title: string;
      robot_id: number;
      robot_name: string | null;
      robot_model_name: string | null;
      started_at: string;
      duration_seconds: number;
      overview: string | null;
      conclusions: string[] | null;
      risks: string[] | null;
      summary_generated_at: string | null;
      speaker_count: number;
      segment_count: number;
      audio_url: string | null;
      deleted_at: string | null;
      created_at: string;
      speakers: MinuteSpeaker[];
    };

    type MinuteDetail = MinuteListItem & {
      segments: MinuteSegment[];
    };

    type MinuteSearchParams = CommonType.RecordNullable<
      Pick<MinuteListItem, 'robot_id'> & {
        keyword?: string;
        time_range?: 'all' | 'today' | '7' | '30';
        sort?: 'asc' | 'desc';
      } & CommonSearchParams
    >;

    type MinuteList = Common.PaginatingQueryRecord<MinuteListItem>;

    type MinuteExportData = {
      filename: string;
      content: string;
      mime_type: string;
    };
  }
}
