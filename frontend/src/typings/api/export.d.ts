declare namespace Api {
  /**
   * namespace Export
   *
   * backend api module: "数据导出"
   */
  namespace Export {
    /** 导出任务状态 */
    type ExportTaskStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'expired';

    /** 导出任务 */
    interface ExportTask {
      id: number;
      task_name: string;
      module_key: string;
      template_id: number | null;
      status: ExportTaskStatus;
      total_rows: number | null;
      file_size: number | null;
      error_message: string | null;
      created_at: string | null;
      started_at: string | null;
      finished_at: string | null;
    }

    /** 导出任务列表响应（后端返回 items，非 records） */
    interface ExportTaskList {
      items: ExportTask[];
      total: number;
      page: number;
      page_size: number;
    }

    /** 提交导出任务请求 */
    interface ExportTaskSubmit {
      module_key: string;
      query_params: Record<string, any>;
    }
  }
}
