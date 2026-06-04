export default {
  route: {
    scheduler: 'Scheduler',
    manage_scheduler: 'Task Management',
    'manage_scheduler-log': 'Execution Log'
  },
  page: {
    manage: {
      scheduler: {
        title: 'Scheduled Task List',
        taskName: 'Task Name',
        taskKey: 'Task Key',
        description: 'Description',
        cronExpression: 'Cron Expression',
        triggerType: 'Trigger Type',
        triggerTypes: {
          cron: 'Cron',
          interval: 'Interval',
          date: 'One-shot'
        },
        status: 'Status',
        statusEnabled: 'Enabled',
        statusDisabled: 'Disabled',
        enable: 'Enable',
        disable: 'Disable',
        lastRunAt: 'Last Run',
        nextRunAt: 'Next Run',
        lastStatus: 'Last Status',
        lastStatuses: {
          success: 'Success',
          failed: 'Failed',
          running: 'Running',
          timeout: 'Timeout'
        },
        timeout: 'Timeout(s)',
        maxRetries: 'Max Retries',
        concurrentPolicy: 'Concurrent Policy',
        concurrentPolicies: {
          skip: 'Skip',
          replace: 'Replace',
          run: 'Allow Concurrent'
        },
        manualTrigger: 'Run Now',
        manualTriggerConfirm: 'Execute this task immediately?',
        manualTriggerSuccess: 'Task triggered',
        cronPreview: 'Preview Schedule',
        nextRunTimes: 'Next 5 Run Times',
        syncRegistry: 'Sync Registry',
        syncRegistrySuccess: 'Sync completed',
        viewLogs: 'Logs',
        triggerParams: 'Trigger Params',
        addTask: 'Add Task',
        editTask: 'Edit Task',
        isSystem: 'System Task',
        form: {
          taskName: 'Enter task name',
          taskKey: 'Enter task key',
          cronExpression: 'Enter cron expression',
          triggerType: 'Select trigger type',
          status: 'Select status',
          concurrentPolicy: 'Select concurrent policy',
          description: 'Enter description'
        }
      },
      schedulerLog: {
        title: 'Task Execution Log',
        taskName: 'Task Name',
        status: 'Status',
        startTime: 'Start Time',
        endTime: 'End Time',
        duration: 'Duration(ms)',
        triggeredBy: 'Triggered By',
        triggeredByValues: {
          scheduler: 'Auto',
          manual: 'Manual'
        },
        result: 'Result',
        errorMessage: 'Error',
        viewDetail: 'Detail',
        clear: 'Clear Logs',
        clearConfirm: 'Clear execution logs older than 30 days?',
        detailTitle: 'Execution Log Detail',
        form: {
          taskName: 'Enter task name',
          status: 'Select status',
          timeRange: 'Time Range'
        }
      }
    }
  }
};
