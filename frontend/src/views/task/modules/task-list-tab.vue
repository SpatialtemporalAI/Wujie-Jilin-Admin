<script setup lang="tsx">
import { reactive, ref, watch } from 'vue';
import { NButton, NDataTable, NPopconfirm, NTag, useMessage } from 'naive-ui';
import {
  fetchGetTaskList,
  fetchDeleteTask,
  fetchToggleTaskEnabled,
  fetchStartExecutionRecord,
  fetchGetActiveExecutionRecords,
  fetchPauseExecutionRecord
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import { enableStatusToBoolean } from '@/utils/status';
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
  broadcast: '播报'
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

/** 活跃执行记录映射：task_id -> 该任务下的活跃执行记录列表 */
const activeExecByTaskId = ref(new Map<number, Api.Task.TaskExecutionRecord[]>());
const actionLoading = ref(false);

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

/** 获取该任务下可暂停的执行记录（running 状态） */
function getPausableRecords(taskId: number): Api.Task.TaskExecutionRecord[] {
  const records = activeExecByTaskId.value.get(taskId) || [];
  return records.filter(r => r.status === 'running' || r.status === 'pending');
}

const {
  columns,
  columnChecks,
  data,
  getData,
  getDataByPage,
  loading,
  mobilePagination
} = useNaivePaginatedTable({
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
      render: row => <NTag size="small" type={row.task_type === 'patrol' ? 'info' : 'success'}>{taskTypeLabel[row.task_type] || row.task_type}</NTag>
    },
    {
      key: 'point_count',
      title: '点位数量',
      align: 'center',
      width: 90,
      render: row => row.task_type === 'patrol' ? <span>{row.point_count}</span> : <span>-</span>
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
      render: row => <NTag size="small" type={row.enabled ? 'success' : 'default'}>{row.enabled ? '启用' : '禁用'}</NTag>
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
      width: 320,
      fixed: 'right',
      render: row => {
        const pausableRecords = getPausableRecords(row.id);
        const canPause = pausableRecords.length > 0 && hasAuth('task:execution:control');
        const canStart = !canPause && row.enabled && hasAuth('task:execution:start');
        return (
          <div class="flex-center gap-8px">
            {canStart && (
              <NButton
                type="success"
                ghost
                size="small"
                loading={actionLoading.value}
                onClick={() => handleStart(row)}
              >
                启动
              </NButton>
            )}
            {canPause && (
              <NButton
                type="warning"
                ghost
                size="small"
                loading={actionLoading.value}
                onClick={() => handlePauseTask(row.id)}
              >
                暂停
              </NButton>
            )}
            {hasAuth('task:edit') && (
              <NButton type="primary" ghost size="small" onClick={() => handleEdit(row.id)}>
                {$t('common.edit')}
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
                  trigger: () => <NButton type="error" ghost size="small">{$t('common.delete')}</NButton>
                }}
              </NPopconfirm>
            )}
          </div>
        );
      }
    }
  ]
});

const {
  drawerVisible,
  operateType,
  editingData,
  handleAdd,
  handleEdit,
  checkedRowKeys,
  onDeleted
} = useTableOperate(data, 'id', getData);

/** 加载当前页面所有任务对应的活跃执行记录（running/paused） */
async function loadActiveExecutions() {
  if (!data.value || data.value.length === 0) {
    activeExecByTaskId.value = new Map();
    return;
  }
  const taskIds = data.value.map(t => t.id);
  const { data: result, error } = await fetchGetActiveExecutionRecords({
    page: 1,
    page_size: 999,
    status: null,
    task_id: null,
    robot_id: null,
    scene_id: null,
    user_id: null,
    source: null,
    start_time: null,
    end_time: null
  });
  if (!error && result) {
    const records = result.records || [];
    const map = new Map<number, Api.Task.TaskExecutionRecord[]>();
    for (const rec of records) {
      if (rec.task_id === null || rec.task_id === undefined) continue;
      if (!taskIds.includes(rec.task_id)) continue;
      const list = map.get(rec.task_id) || [];
      list.push(rec);
      map.set(rec.task_id, list);
    }
    activeExecByTaskId.value = map;
  }
}

// 任务列表数据变化时，同步刷新活跃执行映射
watch(data, () => {
  loadActiveExecutions();
}, { flush: 'post' });

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
  actionLoading.value = true;
  try {
    const robotIds = row.robots?.map((r: Api.Task.TaskRobot) => r.id) || [];
    const { error } = await fetchStartExecutionRecord(row.id, { robot_ids: robotIds, source: 'manual' });
    if (!error) {
      message.success('任务已启动');
      await loadActiveExecutions();
    }
  } catch (error) {
    console.error('启动任务失败:', error);
  } finally {
    actionLoading.value = false;
  }
}

/** 暂停该任务下所有 running/pending 的执行记录 */
async function handlePauseTask(taskId: number) {
  const records = getPausableRecords(taskId);
  if (records.length === 0) return;
  actionLoading.value = true;
  try {
    const results = await Promise.all(
      records.map(r => fetchPauseExecutionRecord(r.id))
    );
    const failed = results.filter(r => r.error).length;
    if (failed === 0) {
      message.success(`已暂停 ${records.length} 条执行`);
    } else {
      message.warning(`${records.length - failed} 条已暂停，${failed} 条失败`);
    }
    await loadActiveExecutions();
  } catch (error) {
    console.error('暂停任务失败:', error);
  } finally {
    actionLoading.value = false;
  }
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-12px overflow-hidden lt-sm:overflow-auto">
    <TaskSearch v-model:model="searchParams" @search="getDataByPage" @reset="getDataByPage" />
    <div>
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
      :scroll-x="1200"
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
