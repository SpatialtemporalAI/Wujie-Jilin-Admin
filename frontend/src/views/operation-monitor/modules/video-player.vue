<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useLiveKitVideo } from '../composables/useLiveKitVideo';

interface Props {
  robotId: number;
  serialNumber: string;
  status: Api.Robot.RobotStatusEnum;
}

const props = defineProps<Props>();

const isOnline = computed(() => props.status === 'online');

const { videoRef, loading, connected, error } = useLiveKitVideo({
  robotId: props.robotId,
  serialNumber: props.serialNumber,
  status: props.status
});

const containerRef = ref<HTMLDivElement | null>(null);
const isFullscreen = ref(false);

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
});

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', updateFullscreenState);
  if (document.fullscreenElement === containerRef.value) {
    document.exitFullscreen().catch(() => {});
  }
});
</script>

<template>
  <NCard :bordered="true" size="small">
    <template #header>视频监控</template>
    <div
      ref="containerRef"
      class="relative flex h-400px items-center justify-center rounded bg-gray-100"
    >
      <video
        ref="videoRef"
        class="absolute inset-0 h-full w-full rounded object-contain"
        :class="{ 'opacity-0': loading || error || !isOnline }"
        autoplay
        playsinline
        muted
      />
      <NSpin v-if="loading" :show="loading" description="正在连接视频..." />
      <NEmpty
        v-else-if="!isOnline"
        description="暂无视频内容"
      >
        <template #icon>
          <icon-ic-round-videocam-off class="text-48px text-gray-300" />
        </template>
      </NEmpty>
      <NEmpty
        v-else-if="error"
        :description="error"
      >
        <template #icon>
          <icon-ic-round-videocam-off class="text-48px text-gray-300" />
        </template>
      </NEmpty>
      <NButton
        v-if="connected"
        class="absolute right-8px top-8px z-10"
        size="tiny"
        quaternary
        type="primary"
        @click="toggleFullscreen"
      >
        <template #icon>
          <icon-gridicons-fullscreen v-if="!isFullscreen" />
          <icon-gridicons-fullscreen-exit v-else />
        </template>
      </NButton>
    </div>
    <div v-if="connected" class="mt-8px text-center text-12px text-success">
      直播中
    </div>
  </NCard>
</template>

<style scoped></style>
