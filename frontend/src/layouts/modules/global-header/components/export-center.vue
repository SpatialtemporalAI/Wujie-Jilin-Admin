<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { NBadge, NButton, NPopover, NTooltip, NList, NListItem, NEmpty, NTag, NSpin } from 'naive-ui';
import { useAuthStore } from '@/store/modules/auth';
import { fetchGetExportTaskList, fetchDownloadExportFile } from '@/service/api';
import { $t } from '@/locales';
import SvgIcon from '@/components/custom/svg-icon.vue';

const authStore = useAuthStore();
const router = useRouter();

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
    case 'expired':
      return { type: 'error' as const, label: $t('exportCenter.statusExpired') };
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

/** 跳转到完整导出任务列表页 */
function goAllTasks() {
  showPopover.value = false;
  router.push({ name: 'log_export-task' });
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
      <NTooltip trigger="hover" placement="bottom">
        <template #trigger>
          <div class="relative cursor-pointer px-8px hover:bg-[#f6f6f6] dark:hover:bg-[#333] rounded-full transition-colors">
            <NBadge :value="pendingCount" :max="99" :show="pendingCount > 0">
              <SvgIcon icon="material-symbols:cloud-download-outline" class="text-20px" />
            </NBadge>
          </div>
        </template>
        {{ $t('exportCenter.title') }}
      </NTooltip>
    </template>
    <template #header>
      <div class="flex items-center justify-between px-12px py-8px">
        <span class="font-bold">{{ $t('exportCenter.title') }}</span>
        <div class="flex items-center gap-12px">
          <NButton text size="small" type="primary" @click="goAllTasks">
            {{ $t('exportCenter.viewAll') }}
          </NButton>
          <NButton text size="small" :loading="loading" @click="getTaskList">
            {{ $t('exportCenter.refresh') }}
          </NButton>
        </div>
      </div>
    </template>
    <div class="max-h-400px overflow-y-auto">
      <NSpin :show="loading">
        <NList v-if="tasks.length > 0" :show-divider="false">
          <NListItem v-for="task in tasks" :key="task.id">
            <div class="flex flex-col gap-4px">
              <div class="flex items-center justify-between gap-8px">
                <div class="flex min-w-0 flex-1 items-center gap-8px">
                  <span class="truncate font-medium">{{ task.task_name }}</span>
                  <NTag :type="getStatusMeta(task.status).type" size="small" class="flex-shrink-0">
                    {{ getStatusMeta(task.status).label }}
                  </NTag>
                </div>
                <NButton
                  v-if="task.status === 'completed'"
                  text
                  size="small"
                  type="primary"
                  :loading="downloadingId === task.id"
                  class="flex-shrink-0"
                  @click="handleDownload(task)"
                >
                  <template #icon>
                    <SvgIcon icon="material-symbols:download" class="text-16px" />
                  </template>
                </NButton>
              </div>
              <div class="flex items-center gap-8px text-12px text-gray">
                <span v-if="task.total_rows != null">{{ task.total_rows }} {{ $t('exportCenter.rows') }}</span>
                <span v-if="task.finished_at">{{ task.finished_at }}</span>
              </div>
              <div v-if="task.status === 'failed' && task.error_message" class="truncate text-12px text-error">
                {{ task.error_message }}
              </div>
            </div>
          </NListItem>
        </NList>
        <NEmpty v-else :description="$t('exportCenter.noRecords')" />
      </NSpin>
    </div>
  </NPopover>
</template>
