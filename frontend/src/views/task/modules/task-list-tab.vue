<script setup lang="tsx">
import { onActivated, onDeactivated, onMounted, onUnmounted, reactive, ref } from 'vue';
import { NButton, NDataTable, NPopconfirm, NTag, useMessage } from 'naive-ui';
import {
  fetchDeleteTask,
  fetchGetTaskList,
  fetchPauseExecutionByTask,
  fetchStartOrResumeExecution,
  fetchToggleTaskEnabled
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { enableStatusToBoolean } from '@/utils/status';
import { jsonClone } from '@sa/utils';
import { $t } from '@/locales';
import TaskSearch from './task-search.vue';
import TaskOperateDrawer from './task-operate-drawer.vue';

const appStore = useAppStore();
const message = useMessage();
const { hasAuth } = useAuth();

const searchParams: Api.Task.TaskSearchParams = reactive({
  page: 1,
  page_size: 10,
  name: null,
  task_type: null,
  enabled: null,
  robot_id: null,
  map_id: null
});

const taskTypeLabel: Record<string, string> = {
  patrol: '巡逻',
  broadcast: '播报',
  instant: '即时'
};

const taskTypeTagType: Record<string, import('naive-ui').TagProps['type']> = {
  patrol: 'info',
  broadcast: 'success',
  instant: 'warning'
};

const scheduleCycleLabel: Record<string, string> = {
  none: '不重复',
  mon: '周一',
  tue: '周二',
  wed: '周三',
  thu: '周四',
  fri: '周五',
  sat: '周六',
  sun: '周日'
};

const startingTaskId = ref<number | null>(null);
const pausingTaskId = ref<number | null>(null);

let pollTimer: ReturnType<typeof setInterval> | null = null;
const POLL_INTERVAL_MS = 15_000;

function startPolling() {
  stopPolling();
  pollTimer = setInterval(getData, POLL_INTERVAL_MS);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

function formatSchedule(row: Api.Task.Task): string {
  if (!row.schedule_enabled) return '未配置';
  const parts: string[] = [];
  if (row.schedule_date) parts.push(row.schedule_date);
  if (row.schedule_start_time) parts.push(row.schedule_start_time);
  if (row.schedule_repeat_cycle) {
    const labels = row.schedule_repeat_cycle
      .split(',')
      .filter(v => v && v !== 'none')
      .map(v => scheduleCycleLabel[v] || v);
    if (labels.length > 0) parts.push(labels.join('、'));
  }
  return parts.length > 0 ? parts.join(' ') : '已启用';
}

const { columns, columnChecks, data, getData, getDataByPage, loading, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetTaskList(searchParams),
  transform: response => {
    const result = defaultTransform(response);
    result.data = result.data.map((task: Api.Task.Task & { enabled: boolean | string }) => ({
      ...task,
      enabled: enableStatusToBoolean(task.enabled)
    }));
    return result;
  },
  onPaginationParamsChange: params => {
    searchParams.page = params.page;
    searchParams.page_size = params.pageSize;
  },
  columns: () => [
    {
      type: 'selection',
      align: 'center',
      width: 48
    },
    {
      key: 'index',
      title: $t('common.index'),
      align: 'center',
      width: 64,
      render: (_, index) => index + 1
    },
    {
      key: 'name',
      title: '任务名称',
      align: 'center',
      minWidth: 140,
      ellipsis: { tooltip: true }
    },
    {
      key: 'task_type',
      title: '任务类型',
      align: 'center',
      width: 100,
      render: row => (
        <NTag size="small" type={taskTypeTagType[row.task_type] || 'default'}>
          {taskTypeLabel[row.task_type] || row.task_type}
        </NTag>
      )
    },
    {
      key: 'point_count',
      title: '点位数量',
      align: 'center',
      width: 90,
      render: row => (row.task_type === 'patrol' ? <span>{row.point_count}</span> : <span>-</span>)
    },
    {
      key: 'schedule',
      title: '定时配置',
      align: 'center',
      minWidth: 160,
      render: row => <span>{formatSchedule(row)}</span>
    },
    {
      key: 'enabled',
      title: '启用状态',
      align: 'center',
      width: 100,
      render: row => (
        <NTag size="small" type={row.enabled ? 'success' : 'default'}>
          {row.enabled ? '启用' : '禁用'}
        </NTag>
      )
    },
    {
      key: 'scene',
      title: '场景地图',
      align: 'center',
      width: 140,
      render: row => <span>{row.map_name || '-'}</span>
    },
    {
      key: 'robots',
      title: '绑定机器人',
      align: 'center',
      width: 120,
      render: row => {
        if (!row.robots || row.robots.length === 0) return <span>-</span>;
        return <span>{row.robots.map((r: Api.Task.TaskRobot) => r.name).join(', ')}</span>;
      }
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 380,
      fixed: 'right',
      render: row => {
        const pausableCount = row.active_execution_count || 0;
        const canPause = pausableCount > 0 && hasAuth('task:execution:control');
        const canStart = row.enabled && hasAuth('task:execution:start') && !canPause;
        return (
          <div class="flex-center gap-8px">
            {canStart && (
              <NButton
                type="success"
                ghost
                size="small"
                loading={startingTaskId.value === row.id}
                disabled={startingTaskId.value !== null || pausingTaskId.value !== null}
                onClick={() => handleStart(row)}
              >
                {startingTaskId.value === row.id ? '启动中' : '立即启动'}
              </NButton>
            )}
            {canPause && (
              <NButton
                type="warning"
                ghost
                size="small"
                loading={pausingTaskId.value === row.id}
                disabled={startingTaskId.value !== null || pausingTaskId.value !== null}
                onClick={() => handlePauseTask(row.id)}
              >
                {pausingTaskId.value === row.id ? '暂停中' : '暂停'}
              </NButton>
            )}
            {hasAuth('task:edit') && (
              <NButton type="primary" ghost size="small" onClick={() => handleEdit(row.id)}>
                {$t('common.edit')}
              </NButton>
            )}
            {hasAuth('task:add') && (
              <NButton size="small" ghost onClick={() => handleCopy(row.id)}>
                复制
              </NButton>
            )}
            {hasAuth('task:edit') && (
              <NButton size="small" ghost onClick={() => handleToggleEnabled(row)}>
                {row.enabled ? '禁用' : '启用'}
              </NButton>
            )}
            {hasAuth('task:delete') && (
              <NPopconfirm onPositiveClick={() => handleDelete(row.id)}>
                {{
                  default: () => $t('common.confirmDelete'),
                  trigger: () => (
                    <NButton type="error" ghost size="small">
                      {$t('common.delete')}
                    </NButton>
                  )
                }}
              </NPopconfirm>
            )}
          </div>
        );
      }
    }
  ]
});

const { drawerVisible, openDrawer, operateType, editingData, handleAdd, handleEdit, checkedRowKeys, onDeleted } =
  useTableOperate<Api.Task.Task, 'copy'>(data, 'id', getData);

/** 复制任务：以源任务数据预填弹窗，提交时因 operateType !== 'edit' 自动命中新增接口 */
function handleCopy(id: number) {
  operateType.value = 'copy';
  const findItem = data.value.find(item => item.id === id) || null;
  editingData.value = jsonClone(findItem);
  openDrawer();
}

async function handleDelete(id: number) {
  try {
    await fetchDeleteTask(id);
    onDeleted();
  } catch (error) {
    console.error('删除任务失败:', error);
  }
}

async function handleToggleEnabled(row: Api.Task.Task) {
  const enabled = !row.enabled;
  const { error } = await fetchToggleTaskEnabled(row.id, enabled);
  if (!error) {
    row.enabled = enabled;
    message.success(enabled ? '已启用' : '已禁用');
    await getDataByPage();
  }
}

async function handleStart(row: Api.Task.Task) {
  if (!row.enabled) {
    message.warning('请先启用任务');
    return;
  }
  if (startingTaskId.value !== null || pausingTaskId.value !== null) return;

  startingTaskId.value = row.id;
  try {
    const robotIds = row.robots?.map((r: Api.Task.TaskRobot) => r.id) || [];
    const { data, error } = await fetchStartOrResumeExecution(row.id, { robot_ids: robotIds, source: 'manual' });
    if (!error) {
      // 多机器人逐个下发：成功 N 台，失败时附带失败数（失败明细由后端返回的 robot_id 列表体现）
      const successCount = data?.success_count ?? 0;
      const failedCount = data?.failed_count ?? 0;
      if (failedCount > 0) {
        message.warning(`任务已启动，成功 ${successCount} 台，失败 ${failedCount} 台`);
      } else {
        message.success(`任务已启动，成功 ${successCount} 台`);
      }
      await getData();
    }
  } catch (error) {
    console.error('启动任务失败:', error);
  } finally {
    startingTaskId.value = null;
  }
}

async function handlePauseTask(taskId: number) {
  if (startingTaskId.value !== null || pausingTaskId.value !== null) return;

  pausingTaskId.value = taskId;
  try {
    const { error } = await fetchPauseExecutionByTask(taskId);
    if (!error) {
      message.success('已暂停');
      await getData();
    }
  } catch (error) {
    console.error('暂停任务失败:', error);
  } finally {
    pausingTaskId.value = null;
  }
}

onMounted(startPolling);
onActivated(startPolling);
onDeactivated(stopPolling);
onUnmounted(stopPolling);
</script>

<template>
  <div class="h-full flex-col-stretch gap-12px overflow-hidden lt-sm:overflow-auto">
    <div class="flex-y-center justify-between gap-12px">
      <TaskSearch v-model:model="searchParams" @search="getDataByPage" />
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :disabled-delete="checkedRowKeys.length === 0"
        :loading="loading"
        add-auth="task:add"
        :show-delete="false"
        @add="handleAdd"
        @refresh="getData"
      />
    </div>
    <NDataTable
      v-model:checked-row-keys="checkedRowKeys"
      :columns="columns"
      :data="data"
      size="small"
      :flex-height="!appStore.isMobile"
      :scroll-x="1360"
      :loading="loading"
      remote
      :row-key="(row: Api.Task.Task) => row.id"
      :pagination="mobilePagination"
      class="sm:flex-1-hidden"
    />
    <TaskOperateDrawer
      v-model:visible="drawerVisible"
      :operate-type="operateType"
      :row-data="editingData"
      @submitted="getDataByPage"
    />
  </div>
</template>

<style scoped></style>
