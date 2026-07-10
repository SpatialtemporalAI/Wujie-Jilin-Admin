<script setup lang="ts">
import { computed } from 'vue';
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
</script>

<template>
  <NCard :bordered="true" size="small">
    <template #header>视频监控</template>
    <div class="flex h-400px items-center justify-center rounded bg-gray-100">
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
      <video
        v-else
        ref="videoRef"
        class="h-full w-full rounded object-contain"
        autoplay
        playsinline
        muted
      />
    </div>
    <div v-if="connected" class="mt-8px text-center text-12px text-success">
      直播中
    </div>
  </NCard>
</template>

<style scoped></style>
