export default {
  route: {
    scheduler: '定时任务',
    manage_scheduler: '任务管理',
    'manage_scheduler-log': '执行日志'
  },
  page: {
    manage: {
      scheduler: {
        title: '定时任务列表',
        taskName: '任务名称',
        taskKey: '任务标识',
        description: '任务描述',
        cronExpression: 'Cron 表达式',
        triggerType: '触发类型',
        triggerTypes: {
          cron: 'Cron 表达式',
          interval: '固定间隔',
          date: '单次执行'
        },
        status: '状态',
        statusEnabled: '已启用',
        statusDisabled: '已禁用',
        enable: '启用',
        disable: '禁用',
        lastRunAt: '上次执行',
        nextRunAt: '下次执行',
        lastStatus: '执行状态',
        lastStatuses: {
          success: '成功',
          failed: '失败',
          running: '运行中',
          timeout: '超时'
        },
        timeout: '超时(秒)',
        maxRetries: '最大重试',
        concurrentPolicy: '并发策略',
        concurrentPolicies: {
          skip: '跳过',
          replace: '替换',
          run: '允许并发'
        },
        manualTrigger: '手动执行',
        manualTriggerConfirm: '确认立即执行该任务？',
        manualTriggerSuccess: '任务已触发执行',
        cronPreview: '预览执行时间',
        nextRunTimes: '接下来 5 次执行时间',
        syncRegistry: '同步注册任务',
        syncRegistrySuccess: '同步完成',
        viewLogs: '执行日志',
        triggerParams: '触发参数',
        addTask: '新增任务',
        editTask: '编辑任务',
        isSystem: '系统任务',
        form: {
          taskName: '请输入任务名称',
          taskKey: '请输入任务标识',
          cronExpression: '请输入 Cron 表达式',
          triggerType: '请选择触发类型',
          status: '请选择状态',
          concurrentPolicy: '请选择并发策略',
          description: '请输入任务描述'
        }
      },
      schedulerLog: {
        title: '任务执行日志',
        taskName: '任务名称',
        status: '执行状态',
        startTime: '开始时间',
        endTime: '结束时间',
        duration: '耗时(ms)',
        triggeredBy: '触发方式',
        triggeredByValues: {
          scheduler: '自动',
          manual: '手动'
        },
        result: '执行结果',
        errorMessage: '错误信息',
        viewDetail: '详情',
        clear: '清理日志',
        clearConfirm: '确认清理30天前的执行日志？',
        detailTitle: '执行日志详情',
        form: {
          taskName: '请输入任务名称',
          status: '请选择执行状态',
          timeRange: '时间范围'
        }
      }
    }
  }
};
