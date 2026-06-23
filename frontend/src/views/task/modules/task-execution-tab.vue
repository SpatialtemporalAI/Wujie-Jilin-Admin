<script setup lang="tsx">
import { reactive, onMounted, onUnmounted, ref } from 'vue';
import { NButton, NDataTable, NProgress, NTag, useMessage } from 'naive-ui';
import {
  fetchGetActiveExecutionRecords,
  fetchPauseExecutionRecord,
  fetchResumeExecutionRecord,
  fetchStopExecutionRecord
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { $t } from '@/locales';
import TaskHistorySearch from './task-history-search.vue';

defineOptions({ name: 'TaskExecutionTab' });

const appStore = useAppStore();
const message = useMessage();

const loading = ref(false);
const data = ref<Api.Task.TaskExecutionRecord[]>([]);
const searchParams: Api.Task.TaskExecutionRecordSearchParams = reactive({
  page: 1,
  page_size: 10,
  status: null,
  robot_id: null,
  scene_id: null,
  user_id: null,
  source: null,
  start_time: null,
  end_time: null
});
const page = ref(1);
const pageSize = ref(10);
const total = ref(0);

const statusColorMap: Record<string, NaiveUI.ThemeColor> = {
  running: 'success',
  paused: 'warning',
  pending: 'info'
};

const statusLabelMap: Record<string, string> = {
  running: '执行中',
  paused: '已暂停',
  pending: '等待中'
};

const sourceLabelMap: Record<string, string> = {
  platform_schedule: '平台定时',
  voice_trigger: '语音触发',
  manual: '手动'
};

const columns = [
  {
    key: 'task_name',
    title: '任务名称',
    align: 'center' as const,
    minWidth: 140,
    ellipsis: { tooltip: true },
    render: (row: Api.Task.TaskExecutionRecord) => (
      <span>{row.task_definition?.task_name || '-'}</span>
    )
  },
  {
    key: 'task_type',
    title: '任务类型',
    align: 'center' as const,
    width: 100,
    render: (row: Api.Task.TaskExecutionRecord) => {
      const taskType = row.task_definition?.task_type;
      return (
        <NTag size="small" type={taskType === 'patrol' ? 'info' : 'success'}>
          {taskType === 'patrol' ? '巡逻' : taskType === 'broadcast' ? '播报' : '-'}
        </NTag>
      );
    }
  },
  {
    key: 'robot_name',
    title: '执行机器人',
    align: 'center' as const,
    width: 120,
    render: (row: Api.Task.TaskExecutionRecord) => <span>{row.robot_name || '-'}</span>
  },
  {
    key: 'scene_name',
    title: '场景地图',
    align: 'center' as const,
    width: 140,
    render: (row: Api.Task.TaskExecutionRecord) => <span>{row.scene_name || '-'}</span>
  },
  {
    key: 'source',
    title: '触发源',
    align: 'center' as const,
    width: 100,
    render: (row: Api.Task.TaskExecutionRecord) => (
      <span>{sourceLabelMap[row.source] || row.source}</span>
    )
  },
  {
    key: 'progress_per',
    title: '进度',
    align: 'center' as const,
    width: 160,
    render: (row: Api.Task.TaskExecutionRecord) => (
      <NProgress type="line" percentage={row.progress_per} indicator-placement="inside" />
    )
  },
  {
    key: 'status',
    title: '状态',
    align: 'center' as const,
    width: 100,
    render: (row: Api.Task.TaskExecutionRecord) => (
      <NTag size="small" type={statusColorMap[row.status] || 'default'}>
        {statusLabelMap[row.status] || row.status}
      </NTag>
    )
  },
  {
    key: 'start_time',
    title: '开始时间',
    align: 'center' as const,
    width: 170,
    render: (row: Api.Task.TaskExecutionRecord) => <span>{row.start_time || '-'}</span>
  },
  {
    key: 'operate',
    title: $t('common.operate'),
    align: 'center' as const,
    width: 180,
    fixed: 'right' as const,
    render: (row: Api.Task.TaskExecutionRecord) => (
      <div class="flex-center gap-8px">
        {row.status === 'running' && (
          <NButton type="warning" ghost size="small" onClick={() => handlePause(row.id)}>暂停</NButton>
        )}
        {row.status === 'paused' && (
          <NButton type="success" ghost size="small" onClick={() => handleResume(row.id)}>恢复</NButton>
        )}
        {(row.status === 'running' || row.status === 'paused') && (
          <NButton type="error" ghost size="small" onClick={() => handleStop(row.id)}>停止</NButton>
        )}
      </div>
    )
  }
];

let pollTimer: ReturnType<typeof setInterval> | null = null;

async function getData() {
  loading.value = true;
  try {
    const { data: result, error } = await fetchGetActiveExecutionRecords({
      ...searchParams,
      page: page.value,
      page_size: pageSize.value
    });
    if (!error && result) {
      data.value = result.records || [];
      total.value = result.total || 0;
    }
  } finally {
    loading.value = false;
  }
}

async function handlePause(recordId: number) {
  const { error } = await fetchPauseExecutionRecord(recordId);
  if (!error) {
    message.success('任务已暂停');
    getData();
  }
}

async function handleResume(recordId: number) {
  const { error } = await fetchResumeExecutionRecord(recordId);
  if (!error) {
    message.success('任务已恢复');
    getData();
  }
}

async function handleStop(recordId: number) {
  const { error } = await fetchStopExecutionRecord(recordId);
  if (!error) {
    message.success('任务已停止');
    getData();
  }
}

function handlePageChange(p: number) {
  page.value = p;
  getData();
}

function handlePageSizeChange(ps: number) {
  pageSize.value = ps;
  page.value = 1;
  getData();
}

function handleSearch() {
  page.value = 1;
  getData();
}

onMounted(() => {
  getData();
  pollTimer = setInterval(getData, 5000);
});

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-12px overflow-hidden lt-sm:overflow-auto">
    <TaskHistorySearch v-model:model="searchParams" @search="handleSearch" @reset="handleSearch" />
    <NDataTable
      :columns="columns"
      :data="data"
      size="small"
      :flex-height="!appStore.isMobile"
      :scroll-x="1200"
      :loading="loading"
      remote
      :row-key="(row: Api.Task.TaskExecutionRecord) => row.id"
      :pagination="{
        page: page,
        pageSize: pageSize,
        itemCount: total,
        showSizePicker: true,
        pageSizes: [10, 20, 50],
        onChange: handlePageChange,
        onUpdatePageSize: handlePageSizeChange
      }"
      class="sm:flex-1-hidden"
    />
  </div>
</template>

<style scoped></style>
