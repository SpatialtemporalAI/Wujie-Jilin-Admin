<script setup lang="tsx">
import { reactive, ref, watch } from 'vue';
import { NButton, NDataTable, NPopconfirm, NTag, useMessage } from 'naive-ui';
import { defaultTransform, useNaivePaginatedTable } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import { fetchGetTaskLogList, fetchBatchDeleteTaskLog, fetchClearTaskLog } from '@/service/api';
import TaskLogDrawer from './task-log-drawer.vue';

defineOptions({ name: 'TaskExecutionLog' });

interface Props {
  taskId: number | null;
}

const props = defineProps<Props>();

const message = useMessage();
const { hasAuth } = useAuth();

const searchParams: Api.Scheduler.TaskLogSearchParams = reactive({
  page: 1,
  page_size: 10,
  task_id: null,
  task_key: null,
  status: null,
  start_time: null,
  end_time: null
});

const logDetailVisible = ref(false);
const detailLogId = ref<number | null>(null);

watch(
  () => props.taskId,
  id => {
    searchParams.task_id = id;
    getData();
  },
  { immediate: true }
);

const statusMap: Record<string, { type: NaiveUI.ThemeColor; label: string }> = {
  running: { type: 'info', label: $t('page.manage.scheduler.lastStatuses.running') },
  success: { type: 'success', label: $t('page.manage.scheduler.lastStatuses.success') },
  failed: { type: 'error', label: $t('page.manage.scheduler.lastStatuses.failed') },
  timeout: { type: 'warning', label: $t('page.manage.scheduler.lastStatuses.timeout') }
};

const {
  columns,
  columnChecks,
  data,
  getData,
  loading,
  mobilePagination
} = useNaivePaginatedTable({
  api: () => fetchGetTaskLogList(searchParams),
  transform: response => defaultTransform(response),
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
      key: 'task_name',
      title: $t('page.manage.scheduler.taskName'),
      align: 'center',
      minWidth: 120,
      ellipsis: { tooltip: true }
    },
    {
      key: 'status',
      title: $t('page.manage.schedulerLog.status'),
      align: 'center',
      width: 80,
      render: row => {
        const s = statusMap[row.status];
        return <NTag type={s?.type || 'default'} size="small">{s?.label || row.status}</NTag>;
      }
    },
    {
      key: 'start_time',
      title: $t('page.manage.schedulerLog.startTime'),
      align: 'center',
      width: 160
    },
    {
      key: 'end_time',
      title: $t('page.manage.schedulerLog.endTime'),
      align: 'center',
      width: 160
    },
    {
      key: 'duration_ms',
      title: $t('page.manage.schedulerLog.duration'),
      align: 'center',
      width: 100,
      render: row => row.duration_ms != null ? `${row.duration_ms.toFixed(0)} ms` : '-'
    },
    {
      key: 'triggered_by',
      title: $t('page.manage.schedulerLog.triggeredBy'),
      align: 'center',
      width: 80,
      render: row => {
        const isManual = row.triggered_by === 'manual';
        return <NTag type={isManual ? 'warning' : 'info'} size="small">
          {isManual ? $t('page.manage.schedulerLog.triggeredByValues.manual') : $t('page.manage.schedulerLog.triggeredByValues.scheduler')}
        </NTag>;
      }
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 80,
      render: row => {
        return (
          <NButton type="primary" text size="small" onClick={() => handleViewDetail(row.id)}>
            {$t('page.manage.schedulerLog.viewDetail')}
          </NButton>
        );
      }
    }
  ]
});

function handleViewDetail(logId: number) {
  detailLogId.value = logId;
  logDetailVisible.value = true;
}

async function handleBatchDelete() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const ids = (data.value as any[]).filter((row: any) => row._checked).map((row: any) => row.id);
  if (ids.length === 0) return;
  const { error } = await fetchBatchDeleteTaskLog(ids);
  if (!error) {
    window.$message?.success($t('common.deleteSuccess'));
    getData();
  }
}

async function handleClear() {
  const { error } = await fetchClearTaskLog(30);
  if (!error) {
    window.$message?.success($t('common.deleteSuccess'));
    getData();
  }
}
</script>

<template>
  <div class="flex-col-stretch gap-8px">
    <NSpace justify="end">
      <NPopconfirm v-if="hasAuth('sys:scheduler:log:delete')" @positive-click="handleClear">
        {{ $t('page.manage.schedulerLog.clearConfirm') }}
        <template #trigger>
          <NButton type="warning" ghost size="small" :disabled="loading">
            {{ $t('page.manage.schedulerLog.clear') }}
          </NButton>
        </template>
      </NPopconfirm>
      <NButton size="small" @click="getData">
        <template #icon>
          <icon-ic-round-refresh class="text-icon" />
        </template>
        {{ $t('common.refresh') }}
      </NButton>
    </NSpace>
    <NDataTable
      :columns="columns"
      :data="data"
      size="small"
      :scroll-x="900"
      :loading="loading"
      remote
      :row-key="(row: Api.Scheduler.TaskLog) => row.id"
      :pagination="mobilePagination"
    />
    <TaskLogDrawer
      v-model:visible="logDetailVisible"
      :log-id="detailLogId"
    />
  </div>
</template>
