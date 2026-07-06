<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { NBadge, NButton, NPopover, NList, NListItem, NEmpty, NTag, NSpin } from 'naive-ui';
import { useAuthStore } from '@/store/modules/auth';
import { fetchGetExportTaskList, fetchDownloadExportFile } from '@/service/api';
import { $t } from '@/locales';
import SvgIcon from '@/components/custom/svg-icon.vue';

const authStore = useAuthStore();

const tasks = ref<Api.Export.ExportTask[]>([]);
const showPopover = ref(false);
const loading = ref(false);
const downloadingId = ref<number | null>(null);

const POLL_INTERVAL = 3000;
const PAGE_SIZE = 20;

/** 进行中任务数（角标） */
const pendingCount = computed(() => {
  return tasks.value.filter(t => t.status === 'pending' || t.status === 'processing').length;
});

let pollTimer: ReturnType<typeof setTimeout> | null = null;

function clearTimer() {
  if (pollTimer) {
    clearTimeout(pollTimer);
    pollTimer = null;
  }
}

/** 拉取导出任务列表（显示 loading） */
async function getTaskList() {
  if (!authStore.isLogin) return;
  loading.value = true;
  const { data } = await fetchGetExportTaskList({ page: 1, page_size: PAGE_SIZE });
  if (data?.items) {
    tasks.value = data.items;
  }
  loading.value = false;
  schedulePoll();
}

/** 轮询刷新（不显示 loading） */
async function refreshList() {
  if (!authStore.isLogin) return;
  const { data } = await fetchGetExportTaskList({ page: 1, page_size: PAGE_SIZE });
  if (data?.items) {
    tasks.value = data.items;
  }
  schedulePoll();
}

/** 存在进行中任务则继续轮询，否则停止 */
function schedulePoll() {
  clearTimer();
  if (pendingCount.value > 0) {
    pollTimer = setTimeout(refreshList, POLL_INTERVAL);
  }
}

/** 状态 -> tag 类型与文案 */
function getStatusMeta(status: Api.Export.ExportTaskStatus) {
  switch (status) {
    case 'completed':
      return { type: 'success' as const, label: $t('exportCenter.statusCompleted') };
    case 'processing':
      return { type: 'info' as const, label: $t('exportCenter.statusProcessing') };
    case 'pending':
      return { type: 'warning' as const, label: $t('exportCenter.statusPending') };
    default:
      return { type: 'error' as const, label: $t('exportCenter.statusFailed') };
  }
}

/** 触发浏览器下载 */
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

/** 下载某任务文件 */
async function handleDownload(task: Api.Export.ExportTask) {
  if (downloadingId.value !== null) return;
  downloadingId.value = task.id;
  try {
    const blob = await fetchDownloadExportFile(task.id);
    triggerDownload(blob, `${task.task_name}_${task.id}.xlsx`);
  } catch (e) {
    console.error('下载导出文件失败:', e);
  } finally {
    downloadingId.value = null;
  }
}

/** 监听日志页提交事件，立即刷新 */
function onSubmitted() {
  getTaskList();
}

function onShowChange(show: boolean) {
  showPopover.value = show;
  if (show) {
    getTaskList();
  }
}

onMounted(() => {
  getTaskList();
  window.addEventListener('export:task-submitted', onSubmitted as EventListener);
});

onUnmounted(() => {
  clearTimer();
  window.removeEventListener('export:task-submitted', onSubmitted as EventListener);
});
</script>

<template>
  <NPopover
    v-model:show="showPopover"
    trigger="click"
    placement="bottom"
    :width="380"
    @update:show="onShowChange"
  >
    <template #trigger>
      <div class="relative cursor-pointer px-8px hover:bg-[#f6f6f6] dark:hover:bg-[#333] rounded-full transition-colors">
        <NBadge :value="pendingCount" :max="99" :show="pendingCount > 0">
          <SvgIcon icon="material-symbols:cloud-download-outline" class="text-20px" />
        </NBadge>
      </div>
    </template>
    <template #header>
      <div class="flex items-center justify-between px-12px py-8px">
        <span class="font-bold">{{ $t('exportCenter.title') }}</span>
        <NButton text size="small" :loading="loading" @click="getTaskList">
          {{ $t('exportCenter.refresh') }}
        </NButton>
      </div>
    </template>
    <div class="max-h-400px overflow-y-auto">
      <NSpin :show="loading">
        <NList v-if="tasks.length > 0" :show-divider="false">
          <NListItem v-for="task in tasks" :key="task.id">
            <div class="flex flex-col gap-4px">
              <div class="flex items-center justify-between gap-8px">
                <span class="font-medium truncate flex-1">{{ task.task_name }}</span>
                <NTag :type="getStatusMeta(task.status).type" size="small">
                  {{ getStatusMeta(task.status).label }}
                </NTag>
              </div>
              <div class="text-12px text-gray flex items-center gap-8px">
                <span v-if="task.total_rows != null">{{ task.total_rows }} {{ $t('exportCenter.rows') }}</span>
                <span v-if="task.finished_at">{{ task.finished_at }}</span>
              </div>
              <div v-if="task.status === 'failed' && task.error_message" class="text-12px text-error truncate">
                {{ task.error_message }}
              </div>
              <div v-if="task.status === 'completed'" class="flex justify-end">
                <NButton
                  size="small"
                  type="primary"
                  ghost
                  :loading="downloadingId === task.id"
                  @click="handleDownload(task)"
                >
                  {{ $t('exportCenter.download') }}
                </NButton>
              </div>
            </div>
          </NListItem>
        </NList>
        <NEmpty v-else :description="$t('exportCenter.noRecords')" />
      </NSpin>
    </div>
  </NPopover>
</template>
