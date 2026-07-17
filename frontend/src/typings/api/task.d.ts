declare namespace Api {
  namespace Task {
    type CommonSearchParams = Pick<Common.PaginatingCommonParams, 'page' | 'page_size'>;

    /** task type */
    type TaskType = 'patrol' | 'broadcast' | 'instant';

    /** task execution status */
    type TaskStatus = 'idle' | 'running' | 'paused';

    /** patrol action */
    type TaskAction =
      | 'shake_hand'
      | 'high_five'
      | 'hug'
      | 'high_wave'
      | 'clap'
      | 'face_wave'
      | 'left_kiss'
      | 'hands_up'
      | 'x_ray'
      | 'right_hand_up'
      | 'reject'
      | 'right_kiss'
      | 'two_hand_kiss'
      | 'no';

    /** patrol point action item (supports multiple actions per point) */
    type TaskActionItem = {
      action: TaskAction;
      voice_text?: string | null;
    };

    /** patrol point */
    type TaskPoint = Common.CommonRecord<{
      task_id: number;
      sort_order: number;
      point_name: string | null;
      annotation_id: number | null;
      actions: TaskActionItem[];
    }>;

    /** robot brief info for task */
    type TaskRobot = {
      id: number;
      name: string;
      status: string | null;
      map_id?: number | null;
      map_name?: string | null;
    };

    /** task */
    type Task = Omit<Common.CommonRecord<object>, 'status'> & {
      name: string;
      map_id: number | null;
      map_name: string | null;
      task_type: TaskType;
      enabled: boolean;
      status: TaskStatus;
      broadcast_text: string | null;
      schedule_enabled: boolean;
      schedule_date: string | null;
      schedule_start_time: string | null;
      schedule_repeat_cycle: string | null;
      point_count: number;
      /** 活跃执行数（running/pending），后端 list 接口关联查询返回 */
      active_execution_count: number;
      points: TaskPoint[] | null;
      robots: TaskRobot[] | null;
    };

    /** task search params */
    type TaskSearchParams = CommonType.RecordNullable<
      Pick<Task, 'name' | 'task_type'> & { enabled: string | null; robot_id?: number; map_id?: number } & CommonSearchParams
    >;

    /** task list */
    type TaskList = Common.PaginatingQueryRecord<Task>;

    /** task create */
    type TaskCreate = {
      name: string;
      map_id?: number | null;
      task_type: TaskType;
      points?: {
        sort_order: number;
        point_name?: string | null;
        annotation_id?: number | null;
        actions: TaskActionItem[];
      }[];
      broadcast_text?: string | null;
      robot_ids: number[];
      schedule_enabled?: boolean;
      schedule_date?: string | null;
      schedule_start_time?: string | null;
      schedule_repeat_cycle?: string | null;
    };

    /** task update */
    type TaskUpdate = Partial<TaskCreate>;

    /** ==================== 任务执行记录（TaskExecutionRecord） ==================== */

    /** execution source */
    type TaskExecutionSource = 'platform_schedule' | 'voice_trigger' | 'manual';

    /** execution record status */
    type TaskExecutionRecordStatus = 'pending' | 'running' | 'paused' | 'completed' | 'cancelled' | 'failed';

    /** point progress status */
    type PointProgressStatus = {
      index: number;
      status: 'pending' | 'running' | 'completed' | 'failed';
      started_at?: string | null;
      finished_at?: string | null;
    };

    /** progress detail */
    type ProgressDetail = {
      total_points: number;
      completed_points: number;
      current_point_index: number;
      points_status: PointProgressStatus[];
    };

    /** action snapshot */
    type TaskActionSnapshot = {
      action: TaskAction;
      voice_text?: string | null;
    };

    /** point snapshot */
    type TaskPointSnapshot = {
      sort_order: number;
      point_name: string | null;
      annotation_id: number | null;
      actions: TaskActionSnapshot[];
    };

    /** task definition snapshot */
    type TaskDefinitionSnapshot = {
      task_type: TaskType;
      task_name: string | null;
      points: TaskPointSnapshot[];
      broadcast_text: string | null;
    };

    /** task execution record (new) */
    type TaskExecutionRecord = Omit<Common.CommonRecord<object>, 'status'> & {
      task_id: number | null;
      robot_id: number | null;
      robot_name: string | null;
      scene_id: number | null;
      scene_name: string | null;
      user_id: number | null;
      user_name: string | null;
      task_definition: TaskDefinitionSnapshot | null;
      progress: ProgressDetail | null;
      progress_per: number;
      status: TaskExecutionRecordStatus;
      source: TaskExecutionSource;
      error_msg: string | null;
      start_time: string | null;
      finish_time: string | null;
    };

    /** task execution record search params */
    type TaskExecutionRecordSearchParams = CommonType.RecordNullable<
      {
        status?: TaskExecutionRecordStatus;
        task_id?: number;
        robot_id?: number;
        scene_id?: number;
        user_id?: number;
        source?: TaskExecutionSource;
        start_time?: string;
        end_time?: string;
      } & CommonSearchParams
    >;

    /** task execution record list */
    type TaskExecutionRecordList = Common.PaginatingQueryRecord<TaskExecutionRecord>;

    /** task execution record detail (alias for now) */
    type TaskExecutionRecordDetail = TaskExecutionRecord;

    /** task execution record start input */
    type TaskExecutionRecordStartIn = {
      robot_ids: number[];
      source?: TaskExecutionSource;
    };

    /** 启动任务结果：多机器人逐个下发 gRPC 后的聚合（在线才下发，离线计入 failed） */
    type TaskStartResult = {
      /** 关联机器人总数 */
      total: number;
      /** 成功启动数量 */
      success_count: number;
      /** 失败数量（含离线 / gRPC 下发失败） */
      failed_count: number;
      /** 成功启动的机器人ID列表 */
      success_robot_ids: number[];
      /** 失败 / 离线的机器人ID列表 */
      failed_robot_ids: number[];
    };
  }
}
