<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { NBadge, NButton, NPopover, NList, NListItem, NEmpty, NDivider } from 'naive-ui';
import { useAuthStore } from '@/store/modules/auth';
import { fetchGetMyNoticeList, fetchGetUnreadCount, fetchMarkAllAsRead } from '@/service/api';
import { $t } from '@/locales';

const authStore = useAuthStore();

const unreadCount = ref(0);
const recentNotices = ref<Api.Notification.MyNotice[]>([]);
const showPopover = ref(false);
const loading = ref(false);

/** 获取未读数量 */
async function getUnreadCount() {
  if (!authStore.isLogin) return;
  const { data } = await fetchGetUnreadCount();
  if (data !== undefined) {
    unreadCount.value = data;
  }
}

/** 获取最近通知 */
async function getRecentNotices() {
  if (!authStore.isLogin) return;
  loading.value = true;
  const { data } = await fetchGetMyNoticeList({ page: 1, page_size: 10 });
  if (data?.records) {
    recentNotices.value = data.records;
  }
  loading.value = false;
}

/** 标记全部已读 */
async function handleMarkAllAsRead() {
  const { error } = await fetchMarkAllAsRead();
  if (!error) {
    unreadCount.value = 0;
    recentNotices.value = recentNotices.value.map(n => ({ ...n, is_read: true }));
    window.$message?.success($t('notification.markAllReadSuccess'));
  }
}

/** 处理 WebSocket 通知事件 */
function handleWsNotification(event: CustomEvent) {
  unreadCount.value += 1;
  // 如果弹窗打开，刷新列表
  if (showPopover.value) {
    getRecentNotices();
  }
}

/** 优先级标签映射 */
const priorityMap: Record<Api.Notification.NoticePriority, { label: string; type: 'default' | 'success' | 'warning' | 'error' }> = {
  low: { label: '低', type: 'default' },
  normal: { label: '普通', type: 'success' },
  high: { label: '高', type: 'warning' },
  urgent: { label: '紧急', type: 'error' }
};

onMounted(() => {
  getUnreadCount();
  window.addEventListener('ws:notification', handleWsNotification as EventListener);
});

onUnmounted(() => {
  window.removeEventListener('ws:notification', handleWsNotification as EventListener);
});

/** 打开弹窗时刷新 */
function onShowChange(show: boolean) {
  showPopover.value = show;
  if (show) {
    getRecentNotices();
  }
}
</script>

<template>
  <NPopover
    v-model:show="showPopover"
    trigger="click"
    placement="bottom"
    :width="360"
    @update:show="onShowChange"
  >
    <template #trigger>
      <div class="relative cursor-pointer px-8px hover:bg-[#f6f6f6] dark:hover:bg-[#333] rounded-full transition-colors">
        <NBadge :value="unreadCount" :max="99" :show="unreadCount > 0">
          <div class="i-material-symbols:notifications-outline text-20px" />
        </NBadge>
      </div>
    </template>
    <template #header>
      <div class="flex items-center justify-between px-12px py-8px">
        <span class="font-bold">{{ $t('notification.title') }}</span>
        <NButton v-if="unreadCount > 0" text size="small" @click="handleMarkAllAsRead">
          {{ $t('notification.markAllAsRead') }}
        </NButton>
      </div>
    </template>
    <div class="max-h-400px overflow-y-auto">
      <NList v-if="recentNotices.length > 0" hoverable clickable :show-divider="false">
        <NListItem v-for="notice in recentNotices" :key="notice.id">
          <div class="flex flex-col gap-4px">
            <div class="flex items-center justify-between">
              <span class="font-medium truncate flex-1" :class="{ 'text-gray': notice.is_read }">
                {{ notice.title }}
              </span>
              <span v-if="!notice.is_read" class="w-8px h-8px rounded-full bg-primary" />
            </div>
            <div class="text-12px text-gray flex items-center gap-8px">
              <span>{{ notice.sender_name }}</span>
              <span v-if="priorityMap[notice.priority]">
                <NBadge
                  :value="priorityMap[notice.priority].label"
                  :type="priorityMap[notice.priority].type"
                  size="small"
                />
              </span>
            </div>
          </div>
        </NListItem>
      </NList>
      <NEmpty v-else :description="$t('notification.noNotifications')" />
    </div>
    <template #footer>
      <NDivider class="!my-0" />
      <div class="px-12px py-8px text-center">
        <NButton text size="small" @click="showPopover = false">
          关闭
        </NButton>
      </div>
    </template>
  </NPopover>
</template>
