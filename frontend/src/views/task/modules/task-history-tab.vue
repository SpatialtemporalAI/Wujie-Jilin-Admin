<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NDataTable, NTag } from 'naive-ui';
import { fetchGetExecutionRecordHistory } from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable } from '@/hooks/common/table';
import { $t } from '@/locales';
import TaskHistorySearch from './task-history-search.vue';
import TaskDetailDrawer from './task-detail-drawer.vue';

defineOptions({ name: 'TaskHistoryTab' });

const appStore = useAppStore();

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

const statusColorMap: Record<string, NaiveUI.ThemeColor> = {
  completed: 'success',
  failed: 'error',
  cancelled: 'default'
};

const statusLabelMap: Record<string, string> = {
  completed: '已完成',
  failed: '已失败',
  cancelled: '已取消'
};

const taskTypeLabel: Record<string, string> = {
  patrol: '巡逻',
  broadcast: '播报'
};

/** 详情抽屉 */
const detailDrawerVisible = ref(false);
const detailExecId = ref<number | null>(null);

function handleViewDetail(row: Api.Task.TaskExecutionRecord) {
  detailExecId.value = row.id;
  detailDrawerVisible.value = true;
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
  api: () => fetchGetExecutionRecordHistory(searchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    searchParams.page = params.page;
    searchParams.page_size = params.pageSize;
  },
  columns: () => [
    {
      key: 'index',
      title: $t('common.index'),
      align: 'center',
      width: 64,
      render: (_, index) => index + 1
    },
    {
      key: 'task_name',
      title: '任务名称',
      align: 'center',
      minWidth: 140,
      ellipsis: { tooltip: true },
      render: (row: Api.Task.TaskExecutionRecord) => (
        <span>{row.task_definition?.task_name || '-'}</span>
      )
    },
    // {
    //   key: 'task_id',
    //   title: '任务ID',
    //   align: 'center',
    //   width: 120,
    //   render: (row: Api.Task.TaskExecutionRecord) => (
    //     <span>{row.task_id === null || row.task_id === undefined ? '-' : row.task_id}</span>
    //   )
    // },
    {
      key: 'task_type',
      title: '任务类型',
      align: 'center',
      width: 100,
      render: (row: Api.Task.TaskExecutionRecord) => {
        const taskType = row.task_definition?.task_type;
        return (
          <NTag size="small" type={taskType === 'patrol' ? 'info' : 'success'}>
            {taskTypeLabel[taskType as string] || taskType || '-'}
          </NTag>
        );
      }
    },
    {
      key: 'status',
      title: '执行状态',
      align: 'center',
      width: 100,
      render: (row: Api.Task.TaskExecutionRecord) => (
        <NTag size="small" type={statusColorMap[row.status] || 'default'}>
          {statusLabelMap[row.status] || row.status}
        </NTag>
      )
    },
    {
      key: 'robot_name',
      title: '执行机器人',
      align: 'center',
      width: 120,
      render: (row: Api.Task.TaskExecutionRecord) => <span>{row.robot_name || '-'}</span>
    },
    {
      key: 'scene_name',
      title: '场景地图',
      align: 'center',
      width: 140,
      render: (row: Api.Task.TaskExecutionRecord) => <span>{row.scene_name || '-'}</span>
    },
    {
      key: 'start_time',
      title: '开始时间',
      align: 'center',
      width: 170,
      render: (row: Api.Task.TaskExecutionRecord) => <span>{row.start_time || '-'}</span>
    },
    {
      key: 'finish_time',
      title: '结束时间',
      align: 'center',
      width: 170,
      render: (row: Api.Task.TaskExecutionRecord) => <span>{row.finish_time || '-'}</span>
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 100,
      fixed: 'right',
      render: (row: Api.Task.TaskExecutionRecord) => (
        <NButton type="primary" ghost size="small" onClick={() => handleViewDetail(row)}>
          查看详情
        </NButton>
      )
    }
  ]
});
</script>

<template>
  <div class="h-full flex-col-stretch gap-12px overflow-hidden lt-sm:overflow-auto">
    <TaskHistorySearch v-model:model="searchParams" @search="getDataByPage" @reset="getDataByPage" />
    <div>
      <TableHeaderOperation v-model:columns="columnChecks" :loading="loading" :show-add="false" :show-delete="false"
        @refresh="getData" />
    </div>
    <NDataTable :columns="columns" :data="data" size="small" :flex-height="!appStore.isMobile" :scroll-x="1320"
      :loading="loading" remote :row-key="(row: Api.Task.TaskExecutionRecord) => row.id" :pagination="mobilePagination"
      class="sm:flex-1-hidden" />
    <TaskDetailDrawer v-model:visible="detailDrawerVisible" :exec-id="detailExecId" />
  </div>
</template>

<style scoped></style>
