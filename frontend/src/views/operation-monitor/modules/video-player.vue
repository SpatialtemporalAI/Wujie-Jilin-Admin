<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useLiveKitVideo, type UseLiveKitVideoOptions } from '../composables/useLiveKitVideo';

interface Props extends UseLiveKitVideoOptions {}

const props = defineProps<Props>();

const isOnline = computed(() => props.status === 'online');

const { videoRef, loading, connected, error, resolution, frameRate } = useLiveKitVideo(props);

const containerRef = ref<HTMLDivElement | null>(null);
const isFullscreen = ref(false);
const currentTime = ref(formatClock());
let clockTimer: ReturnType<typeof setInterval> | null = null;

function pad(n: number) {
  return String(n).padStart(2, '0');
}

function formatClock(date = new Date()) {
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

function updateFullscreenState() {
  isFullscreen.value = !!document.fullscreenElement;
}

async function toggleFullscreen() {
  if (!containerRef.value) return;

  try {
    if (!document.fullscreenElement) {
      await containerRef.value.requestFullscreen();
    } else {
      await document.exitFullscreen();
    }
  } catch (err) {
    console.error('切换全屏失败', err);
  }
}

onMounted(() => {
  document.addEventListener('fullscreenchange', updateFullscreenState);
  clockTimer = setInterval(() => {
    currentTime.value = formatClock();
  }, 1000);
});

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', updateFullscreenState);
  if (clockTimer) {
    clearInterval(clockTimer);
    clockTimer = null;
  }
  if (document.fullscreenElement === containerRef.value) {
    document.exitFullscreen().catch(() => {});
  }
});
</script>

<template>
  <NCard :bordered="true" size="small">
    <div
      ref="containerRef"
      class="relative flex h-400px items-center justify-start overflow-hidden rounded"
    >
      <div class="relative h-full max-w-full">
        <video
          ref="videoRef"
          class="h-full w-auto max-w-full rounded object-contain"
          style="object-position: left center"
          :class="{ 'opacity-0': loading || error || !isOnline }"
          autoplay
          playsinline
          muted
        />
        <div
          v-if="connected"
          class="absolute inset-x-0 top-0 z-10 flex items-center justify-between gap-8px bg-black/40 px-8px py-4px text-12px text-white"
        >
          <span class="font-mono">{{ currentTime }}</span>
          <div class="flex items-center gap-8px">
            <span v-if="resolution" class="font-mono">{{ resolution }}</span>
            <span v-if="frameRate" class="font-mono">{{ frameRate }} fps</span>
            <button
              type="button"
              class="flex h-20px w-20px cursor-pointer items-center justify-center rounded text-16px text-white opacity-80 transition hover:opacity-100"
              :title="isFullscreen ? '退出全屏' : '全屏'"
              @click="toggleFullscreen"
            >
              <icon-gridicons-fullscreen v-if="!isFullscreen" />
              <icon-gridicons-fullscreen-exit v-else />
            </button>
          </div>
        </div>
      </div>
      <div v-if="loading || !isOnline || error" class="absolute inset-0 flex items-center justify-center">
        <NSpin v-if="loading" :show="loading" description="正在连接视频..." />
        <NEmpty v-else-if="!isOnline" description="暂无视频内容">
          <template #icon>
            <icon-ic-round-videocam-off class="text-48px text-gray-300" />
          </template>
        </NEmpty>
        <NEmpty v-else-if="error" :description="error">
          <template #icon>
            <icon-ic-round-videocam-off class="text-48px text-gray-300" />
          </template>
        </NEmpty>
      </div>
    </div>
  </NCard>
</template>

<style scoped></style>
