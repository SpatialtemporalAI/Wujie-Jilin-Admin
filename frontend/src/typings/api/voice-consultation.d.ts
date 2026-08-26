declare namespace Api {
  /**
   * namespace VoiceConsultation
   *
   * 语音问诊（数据由外部应用直连数据库写入，本系统仅查询展示）
   */
  namespace VoiceConsultation {
    type CommonSearchParams = Pick<Common.PaginatingCommonParams, 'page' | 'page_size'>;

    /** 触发方式 */
    type TriggerMethod = 'wake_word' | 'face_recognition';

    /** 会话状态 */
    type SessionStatus = 'in_progress' | 'completed' | 'interrupted';

    /** 意图类型 */
    type IntentType =
      | 'indoor_navigation'
      | 'triage_qa'
      | 'medical_guide'
      | 'health_check_notice'
      | 'insurance_guide'
      | 'admission_notice'
      | 'medication_consult'
      | 'general_chat';

    /** 语音问诊会话记录（status 为业务枚举，覆盖 CommonRecord 的通用 status） */
    type SessionRecord = Omit<Common.CommonRecord, 'status'> & {
      /** robot id */
      robot_id: number;
      /** robot name */
      robot_name: string | null;
      /** 交互发生时间 */
      occurred_at: string | null;
      /** 触发方式 */
      trigger_method: TriggerMethod;
      /** 会话轮次数 */
      turn_count: number;
      /** 提问摘要 */
      question_summary: string | null;
      /** 会话时长（秒） */
      duration_seconds: number | null;
      /** 状态 */
      status: SessionStatus;
      /** 意图类型 */
      intent_type: IntentType | string;
    };

    /** 会话搜索参数 */
    type SessionSearchParams = CommonType.RecordNullable<
      Pick<SessionRecord, 'robot_id' | 'trigger_method' | 'status' | 'intent_type'> &
        CommonSearchParams & {
          /** 关键词，模糊匹配提问摘要 */
          keyword: string | null;
          /** 开始时间 */
          start_time: string | undefined;
          /** 结束时间 */
          end_time: string | undefined;
        }
    >;

    /** 会话列表 */
    type SessionList = Common.PaginatingQueryRecord<SessionRecord>;

    /** 轮次明细 */
    type TurnDetail = {
      id: number;
      turn_no: number;
      question: string | null;
      answer: string | null;
      intent_type: IntentType | string | null;
      duration_seconds: number | null;
      occurred_at: string | null;
    };

    /** 会话详情（含轮次明细） */
    type SessionDetail = SessionRecord & {
      /** 轮次明细，按轮次序号排序 */
      turns: TurnDetail[];
    };

    /** 分布统计项 */
    type DistributionItem = {
      type: string;
      count: number;
    };

    /** 统计响应（卡片统计不随筛选，平均时长为当日口径；分布图表随筛选） */
    type Stats = {
      /** 全量总交互数（不随筛选） */
      total: number;
      /** 总量较截止上周日累计的百分比变化 */
      total_delta_pct: number | null;
      /** 今日交互数（不随筛选） */
      today_count: number;
      /** 今日较昨日百分比变化 */
      today_delta_pct: number | null;
      /** 当日平均会话时长（秒，不随筛选） */
      avg_duration: number | null;
      /** 当日均值较昨日均值的百分比变化 */
      avg_duration_delta_pct: number | null;
      /** 意图分布（随筛选），8 项含零值 */
      intent_distribution: DistributionItem[];
      /** 触发方式分布（随筛选），2 项含零值 */
      trigger_distribution: DistributionItem[];
    };
  }
}
