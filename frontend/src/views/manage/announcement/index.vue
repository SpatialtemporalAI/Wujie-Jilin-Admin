<script setup lang="tsx">
import { reactive } from 'vue';
import { NButton, NPopconfirm, NTag, NSpace } from 'naive-ui';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import { booleanToEnableStatus } from '@/utils/status';
import {
  fetchGetNoticeList,
  fetchDeleteNotice,
  fetchBatchDeleteNotice,
  fetchPublishNotice
} from '@/service/api';
import NoticeOperateDrawer from './modules/notice-operate-drawer.vue';
import NoticeSearch from './modules/notice-search.vue';

const appStore = useAppStore();
const { hasAuth } = useAuth();

const searchParams: Api.Notification.NoticeSearchParams = reactive({
  page: 1,
  page_size: 10,
  title: null,
  type: null,
  target_type: null,
  status: null,
  priority: null
});

const priorityMap: Record<Api.Notification.NoticePriority, { label: string; type: 'default' | 'success' | 'warning' | 'error' }> = {
  low: { label: '低', type: 'default' },
  normal: { label: '普通', type: 'success' },
  high: { label: '高', type: 'warning' },
  urgent: { label: '紧急', type: 'error' }
};

const typeMap: Record<Api.Notification.NoticeType, string> = {
  announcement: '公告',
  system: '系统',
  operation: '操作提醒',
  approval: '审批通知'
};

const targetTypeMap: Record<Api.Notification.NoticeTargetType, string> = {
  all: '全员',
  role: '按角色',
  user: '按用户'
};

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetNoticeList(searchParams),
  transform: response => {
    const result = defaultTransform(response);
    result.data = result.data.map((notice: any) => ({
      ...notice,
      status: booleanToEnableStatus(notice.status)
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
      width: 64,
      align: 'center',
      render: (_, index) => index + 1
    },
    {
      key: 'title',
      title: '标题',
      align: 'center',
      minWidth: 180,
      ellipsis: {
        tooltip: true
      }
    },
    {
      key: 'type',
      title: '类型',
      align: 'center',
      width: 100,
      render: (row: Api.Notification.Notice) => {
        return <span>{ typeMap[row.type] || row.type }</span>;
      }
    },
    {
      key: 'target_type',
      title: '推送范围',
      align: 'center',
      width: 100,
      render: (row: Api.Notification.Notice) => {
        return <span>{ targetTypeMap[row.target_type] || row.target_type }</span>;
      }
    },
    {
      key: 'priority',
      title: '优先级',
      align: 'center',
      width: 90,
      render: (row: Api.Notification.Notice) => {
        const pm = priorityMap[row.priority];
        if (!pm) return null;
        return <NTag type={pm.type} size="small">{pm.label}</NTag>;
      }
    },
    {
      key: 'status',
      title: $t('common.status'),
      align: 'center',
      width: 80,
      render: (row: Api.Notification.Notice) => {
        if (row.status === null) {
          return null;
        }
        const tagMap: Record<Api.Common.EnableStatus, NaiveUI.ThemeColor> = {
          '1': 'success',
          '2': 'warning'
        };
        const label = row.status === '1' ? '已发布' : '草稿';
        return <NTag type={tagMap[row.status]}>{label}</NTag>;
      }
    },
    {
      key: 'sender_name',
      title: '发送人',
      align: 'center',
      width: 100
    },
    {
      key: 'published_at',
      title: '发布时间',
      align: 'center',
      width: 160,
      render: (row: Api.Notification.Notice) => {
        return <span>{ row.published_at || '-' }</span>;
      }
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 200,
      fixed: 'right',
      render: (row: Api.Notification.Notice) => {
        const isDraft = row.status === '2';
        return (
          <div class="flex flex-wrap justify-center gap-8px">
            {hasAuth('sys:notice:edit') && isDraft && (
              <NButton type="primary" text size="small" onClick={() => edit(row.id)}>
                { $t('common.edit') }
              </NButton>
            )}
            {hasAuth('sys:notice:publish') && isDraft && (
              <NButton type="warning" text size="small" onClick={() => handlePublish(row.id)}>
                发布
              </NButton>
            )}
            {hasAuth('sys:notice:delete') && (
              <NPopconfirm onPositiveClick={() => handleDelete(row.id)}>
                {{
                  default: () => $t('common.confirmDelete'),
                  trigger: () => (
                    <NButton type="error" text size="small">
                      { $t('common.delete') }
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

const { drawerVisible, operateType, editingData, handleAdd, handleEdit, checkedRowKeys, onBatchDeleted, onDeleted } =
  useTableOperate(data, 'id', getData);

async function handleBatchDelete() {
  if (checkedRowKeys.value.length === 0) {
    window.$message?.warning($t('common.pleaseSelect'));
    return;
  }
  const { error } = await fetchBatchDeleteNotice(checkedRowKeys.value);
  if (!error) {
    window.$message?.success($t('common.deleteSuccess'));
    onBatchDeleted();
  }
}

async function handleDelete(id: number) {
  const { error } = await fetchDeleteNotice(id);
  if (!error) {
    window.$message?.success($t('common.deleteSuccess'));
    onDeleted();
  }
}

async function handlePublish(id: number) {
  const { error } = await fetchPublishNotice(id);
  if (!error) {
    window.$message?.success('发布成功');
    getData();
  }
}

function edit(id: number) {
  handleEdit(id);
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <NoticeSearch v-model:model="searchParams" @search="getDataByPage" />
    <NCard :title="$t('page.manage.announcement.title')" :bordered="false" size="small" class="card-wrapper sm:flex-1-hidden">
      <template #header-extra>
        <TableHeaderOperation
          v-model:columns="columnChecks"
          :disabled-delete="checkedRowKeys.length === 0"
          :loading="loading"
          add-auth="sys:notice:add"
          delete-auth="sys:notice:delete"
          @add="handleAdd"
          @delete="handleBatchDelete"
          @refresh="getData"
        />
      </template>
      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        :columns="columns"
        :data="data"
        size="small"
        :flex-height="!appStore.isMobile"
        :scroll-x="1100"
        :loading="loading"
        remote
        :row-key="row => row.id"
        :pagination="mobilePagination"
        class="sm:h-full"
      />
      <NoticeOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
