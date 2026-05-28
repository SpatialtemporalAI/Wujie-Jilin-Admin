declare namespace Api {
  /**
   * namespace Monitor
   *
   * backend api module: "monitor"
   */
  namespace Monitor {
    /** 内存信息 */
    type MemoryInfo = {
      total: number;
      used: number;
      free: number;
      percent: number;
    };

    /** 磁盘信息 */
    type DiskInfo = {
      total: number;
      used: number;
      free: number;
      percent: number;
    };

    /** 系统指标 */
    type SystemMetrics = {
      cpu_percent: number;
      memory: MemoryInfo;
      disk: DiskInfo;
      boot_time: string;
      process_count: number;
      python_version: string;
    };

    /** API统计 */
    type ApiStats = {
      timestamp: string;
      avg_elapsed_ms: number;
      request_count: number;
      error_count: number;
      error_rate: number;
    };
  }
}
