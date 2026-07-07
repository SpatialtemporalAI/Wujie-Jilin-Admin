<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NCard, NDataTable, NSelect, NTag, useMessage } from 'naive-ui';
import { fetchDownloadExportFile, fetchGetExportTaskList } from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { useNaivePaginatedTable } from '@/hooks/common/table';
import { $t } from '@/locales';
import SvgIcon from '@/components/custom/svg-icon.vue';

const appStore = useAppStore();
const message = useMessage();

interface ExportTaskSearchParams {
  page: number;
  page_size: number;
  status: string | null;
}

const searchParams = reactive<ExportTaskSearchParams>({
  page: 1,
  page_size: 10,
  status: null
});

const statusOptions = [
  { label: $t('exportCenter.statusPending'), value: 'pending' },
  { label: $t('exportCenter.statusProcessing'), value: 'processing' },
  { label: $t('exportCenter.statusCompleted'), value: 'completed' },
  { label: $t('exportCenter.statusFailed'), value: 'failed' },
  { label: $t('exportCenter.statusExpired'), value: 'expired' }
];

/** 状态 -> tag 类型与文案 */
function getStatusMeta(status: Api.Export.ExportTaskStatus) {
  switch (status) {
    case 'completed':
      return { type: 'success' as const, label: $t('exportCenter.statusCompleted') };
    case 'processing':
      return { type: 'info' as const, label: $t('exportCenter.statusProcessing') };
    case 'pending':
      return { type: 'warning' as const, label: $t('exportCenter.statusPending') };
    case 'expired':
      return { type: 'error' as const, label: $t('exportCenter.statusExpired') };
    default:
      return { type: 'error' as const, label: $t('exportCenter.statusFailed') };
  }
}

function formatFileSize(bytes: number | null): string {
  if (bytes == null) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

const downloadingId = ref<number | null>(null);

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

async function handleDownload(row: Api.Export.ExportTask) {
  if (downloadingId.value !== null) return;
  downloadingId.value = row.id;
  try {
    const blob = await fetchDownloadExportFile(row.id);
    triggerDownload(blob, `${row.task_name}_${row.id}.xlsx`);
  } catch (e) {
    message.error($t('page.log.exportTask.downloadFailed'));
  } finally {
    downloadingId.value = null;
  }
}

const { columns, columnChecks, data, getData, loading, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetExportTaskList(searchParams),
  transform: response => {
    // 导出接口返回 items（非项目通用的 records），这里做一次适配
    const { data: respData, error } = response;
    if (!error && respData) {
      return {
        data: respData.items,
        pageNum: respData.page,
        pageSize: respData.page_size,
        total: respData.total,
        totalPages: respData.page_size ? Math.ceil(respData.total / respData.page_size) : 1
      };
    }
    return { data: [], pageNum: 1, pageSize: 10, total: 0, totalPages: 1 };
  },
  onPaginationParamsChange: params => {
    searchParams.page = params.page ?? 1;
    searchParams.page_size = params.pageSize ?? 10;
  },
  columns: () => [
    {
      key: 'task_name',
      title: $t('page.log.exportTask.taskName'),
      minWidth: 180,
      ellipsis: { tooltip: true }
    },
    {
      key: 'module_key',
      title: $t('page.log.exportTask.module'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'status',
      title: $t('page.log.exportTask.status'),
      align: 'center',
      minWidth: 100,
      render: row => {
        const meta = getStatusMeta(row.status);
        return <NTag type={meta.type} size="small">{meta.label}</NTag>;
      }
    },
    {
      key: 'total_rows',
      title: $t('page.log.exportTask.totalRows'),
      align: 'center',
      minWidth: 100,
      render: row => (row.total_rows != null ? row.total_rows : '-')
    },
    {
      key: 'file_size',
      title: $t('page.log.exportTask.fileSize'),
      align: 'center',
      minWidth: 110,
      render: row => formatFileSize(row.file_size)
    },
    {
      key: 'created_at',
      title: $t('page.log.exportTask.createdAt'),
      align: 'center',
      minWidth: 160
    },
    {
      key: 'finished_at',
      title: $t('page.log.exportTask.finishedAt'),
      align: 'center',
      minWidth: 160
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 90,
      fixed: 'right',
      render: row => {
        if (row.status !== 'completed') return <span class="text-gray">-</span>;
        return (
          <NButton
            text
            size="small"
            type="primary"
            loading={downloadingId.value === row.id}
            onClick={() => handleDownload(row)}
          >
            <SvgIcon icon="material-symbols:download" class="text-16px" />
          </NButton>
        );
      }
    }
  ]
});

function onStatusChange(val: string | number | null) {
  searchParams.status = (val as string | null) ?? null;
  searchParams.page = 1;
  getData();
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <NCard :bordered="false" size="small" class="flex-1-hidden card-wrapper">
      <template #header>
        <div class="flex-y-center justify-between gap-12px">
          <NSelect
            :value="searchParams.status"
            :options="statusOptions"
            clearable
            :placeholder="$t('page.log.exportTask.form.status')"
            :style="{ width: '180px' }"
            @update:value="onStatusChange"
          />
          <TableHeaderOperation
            v-model:columns="columnChecks"
            :loading="loading"
            :show-add="false"
            :show-delete="false"
            @refresh="getData"
          />
        </div>
      </template>
      <NDataTable
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
    </NCard>
  </div>
</template>
