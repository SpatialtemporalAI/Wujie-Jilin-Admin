<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NCard, NDataTable, NPopconfirm, NTag, useMessage } from 'naive-ui';
import {
  fetchBatchDeleteRobotEventLog,
  fetchClearRobotEventLog,
  fetchDeleteRobotEventLog,
  fetchGetRobotEventLogList
} from '@/service/api/log';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { useExportSubmit } from '@/hooks/business/export-task';
import { $t } from '@/locales';
import RobotEventLogSearch from './modules/robot-event-log-search.vue';
import EventContentModal from './modules/event-content-modal.vue';

const appStore = useAppStore();
const message = useMessage();
const { hasAuth } = useAuth();
const { submitting, submitExport } = useExportSubmit();

const eventContentModalVisible = ref(false);
const eventContentModalContent = ref('');

function openEventContentModal(content: string | null | undefined) {
  eventContentModalContent.value = content || '';
  eventContentModalVisible.value = true;
}

const searchParams: Api.SystemManage.RobotEventLogSearchParams = reactive({
  page: 1,
  page_size: 10,
  robot_id: null,
  event_status: null,
  start_time: null,
  end_time: null
});

const {
  columns,
  columnChecks,
  data,
  getData,
  getDataByPage,
  loading,
  mobilePagination
} = useNaivePaginatedTable({
  api: () => fetchGetRobotEventLogList(searchParams),
  transform: response => {
    return defaultTransform(response);
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
      key: 'robot_name',
      title: $t('page.log.robotEventLog.robotName'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'event_status',
      title: $t('page.log.robotEventLog.eventStatus'),
      align: 'center',
      width: 120,
      render: row => {
        const statusMap: Record<string, { type: 'error' | 'warning' | 'info'; label: string }> = {
          abnormal: { type: 'error', label: $t('page.log.robotEventLog.statusCritical') },
          warning: { type: 'warning', label: $t('page.log.robotEventLog.statusWarning') },
          normal: { type: 'info', label: $t('page.log.robotEventLog.statusInfo') }
        };
        const config = statusMap[row.event_status] || { type: 'default' as const, label: row.event_status };
        return <NTag type={config.type}>{config.label}</NTag>;
      }
    },
    {
      key: 'event_content',
      title: $t('page.log.robotEventLog.eventContent'),
      align: 'left',
      minWidth: 200,
      render: row => (
        <div
          class="w-full cursor-pointer"
          style={{
            overflow: 'hidden',
            whiteSpace: 'nowrap',
            textOverflow: 'ellipsis',
            userSelect: 'none'
          }}
          onClick={() => openEventContentModal(row.event_content)}
        >
          {showContentMsg(row.event_content)}
        </div>
      )
    },
    {
      key: 'created_at',
      title: '创建时间',
      align: 'center',
      minWidth: 160
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 80,
      render: row => {
        if (!hasAuth('robot:event-log:delete')) return null;
        return (
          <NPopconfirm onPositiveClick={() => handleDelete(row.id)}>
            {{
              default: () => $t('common.confirmDelete'),
              trigger: () => (
                <NButton type="error" text size="small">
                  {$t('common.delete')}
                </NButton>
              )
            }}
          </NPopconfirm>
        );
      }
    }
  ]
});
const showContentMsg = (content: string | null | undefined) => {
  if (!content) return '';
  const obj = JSON.parse(content);
  if (obj.message) {
    return obj.message;
  }
  return content
}

const { checkedRowKeys, onBatchDeleted, onDeleted } = useTableOperate(data, 'id', getData);

async function handleDelete(id: number) {
  try {
    await fetchDeleteRobotEventLog(id);
    onDeleted();
  } catch (error) {
    console.error('删除机器人事件日志失败:', error);
  }
}

async function handleBatchDelete() {
  if (checkedRowKeys.value.length === 0) {
    message.warning($t('common.selectAtLeastOne'));
    return;
  }
  try {
    await fetchBatchDeleteRobotEventLog(checkedRowKeys.value.map(Number));
    onBatchDeleted();
  } catch (error) {
    message.error($t('common.deleteFailed'));
  }
}

async function handleClear() {
  try {
    await fetchClearRobotEventLog(30);
    message.success($t('common.deleteSuccess'));
    getData();
  } catch (error) {
    message.error($t('common.deleteFailed'));
  }
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-12px overflow-hidden lt-sm:overflow-auto">
    <div class="flex-y-center justify-between gap-12px">
      <RobotEventLogSearch v-model:model="searchParams" @search="getDataByPage" />
      <TableHeaderOperation v-model:columns="columnChecks" :disabled-delete="checkedRowKeys.length === 0"
        :loading="loading" :show-add="false" delete-auth="robot:event-log:delete" @delete="handleBatchDelete"
        @refresh="getData">
        <template #prefix>
          <NPopconfirm v-if="hasAuth('robot:event-log:delete')" @positive-click="handleClear">
            {{ $t('page.log.robotEventLog.clearConfirm') }}
            <template #trigger>
              <NButton type="warning" ghost size="small" :disabled="loading">
                {{ $t('page.log.robotEventLog.clear') }}
              </NButton>
            </template>
          </NPopconfirm>
          <NButton type="primary" ghost size="small" :loading="submitting" :disabled="loading"
            @click="submitExport('robot_event_log', searchParams)">
            {{ $t('common.export') }}
          </NButton>
        </template>
      </TableHeaderOperation>
    </div>
    <NCard :bordered="false" size="small" class="flex-1-hidden card-wrapper">
      <NDataTable v-model:checked-row-keys="checkedRowKeys" :columns="columns" :data="data" size="small"
        :flex-height="!appStore.isMobile" :scroll-x="1000" :loading="loading" remote :row-key="row => row.id"
        :pagination="mobilePagination" class="sm:h-full" />
    </NCard>
    <EventContentModal v-model:visible="eventContentModalVisible" :content="eventContentModalContent" />
  </div>
</template>
