<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  robotList: Api.Robot.Robot[];
  selectedRobot: Api.Robot.Robot | null;
  statusRecord: Api.Robot.RobotStatusRecord | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'select', id: number): void;
}>();

const statusColorMap: Record<string, { color: string; label: string }> = {
  online: { color: '#18a058', label: '在线' },
  offline: { color: '#f0a020', label: '离线' },
  inactive: { color: '#999', label: '未激活' }
};

function getBatteryColor(battery: number): string {
  if (battery >= 60) return '#18a058';
  if (battery >= 30) return '#f0a020';
  return '#d03050';
}

function getSignalLabel(signal: number): { text: string; color: string } {
  if (signal >= 70) return { text: '优秀', color: '#18a058' };
  if (signal >= 40) return { text: '良好', color: '#f0a020' };
  return { text: '弱', color: '#d03050' };
}

function getSpeedLabel(speed: number): { text: string; color: string } {
  if (speed > 0) return { text: '移动中', color: '#2080f0' };
  return { text: '静止', color: '#d03050' };
}

function getBatteryLabel(battery: number): { text: string; color: string } {
  if (battery >= 80) return { text: '充足', color: '#18a058' };
  if (battery >= 50) return { text: '良好', color: '#2080f0' };
  if (battery >= 30) return { text: '一般', color: '#f0a020' };
  if (battery >= 10) return { text: '偏低', color: '#f0a020' };
  return { text: '极低', color: '#d03050' };
}

const robotOptions = computed(() =>
  props.robotList.map(r => ({
    label: `${r.name}（${r.serial_number}）`,
    value: r.id
  }))
);
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <div class="flex items-center justify-between">
      <NSpace align="center" :size="16">
        <div class="flex items-center gap-8px">
          <img src="@/assets/imgs/monitor-title.png" class="h-60px w-60px object-contain" />
          <NSelect
            :value="selectedRobot?.id ?? null"
            :options="robotOptions"
            placeholder="选择机器人"
            style="width: 220px"
            size="small"
            @update:value="val => val && emit('select', val)"
          />
        </div>
        <NSpace v-if="selectedRobot" align="center" :size="6">
          <span
            class="inline-block h-8px w-8px rounded-full"
            :style="{ backgroundColor: statusColorMap[selectedRobot.status]?.color ?? '#999' }"
          />
          <span class="text-13px" :style="{ color: statusColorMap[selectedRobot.status]?.color ?? '#999' }">
            {{ statusColorMap[selectedRobot.status]?.label ?? selectedRobot.status }}
          </span>
        </NSpace>
      </NSpace>
    </div>

    <NGrid v-if="selectedRobot" :x-gap="16" :y-gap="8" :cols="3" class="mt-16px">
      <!-- 电量 -->
      <NGi>
        <NCard :bordered="false" size="small" class="h-full">
          <div class="status-item">
            <img src="@/assets/imgs/monitor-battery.png" />
            <div class="status-main">
              <div class="flex items-baseline gap-4px">
                <span class="text-24px font-bold">{{ statusRecord?.battery ?? '--' }}</span>
                <span class="text-12px text-gray-400">% 电池</span>
              </div>
              <!-- <NProgress
                v-if="statusRecord"
                type="line"
                :percentage="statusRecord.battery"
                :color="getBatteryColor(statusRecord.battery)"
                :show-indicator="false"
                :height="6"
                class="mt-4px"
              /> -->
            </div>
            <div class="status-extra">
              <span
                v-if="statusRecord"
                class="text-14px font-medium"
                :style="{ color: getBatteryLabel(statusRecord.battery).color }"
              >
                {{ getBatteryLabel(statusRecord.battery).text }}
              </span>
            </div>
          </div>
        </NCard>
      </NGi>

      <!-- 信号 -->
      <NGi>
        <NCard :bordered="false" size="small" class="h-full">
          <div class="status-item">
            <img src="@/assets/imgs/monitor-signal.png" />
            <div class="status-main">
              <div class="flex items-baseline gap-4px">
                <span class="text-24px font-bold">{{ statusRecord?.signal ?? '--' }}</span>
                <span class="text-12px text-gray-400">dBm 信号</span>
              </div>
            </div>
            <div class="status-extra">
              <span
                v-if="statusRecord"
                class="text-14px font-medium"
                :style="{ color: getSignalLabel(statusRecord.signal).color }"
              >
                {{ getSignalLabel(statusRecord.signal).text }}
              </span>
            </div>
          </div>
        </NCard>
      </NGi>

      <!-- 速度 -->
      <NGi>
        <NCard :bordered="false" size="small" class="h-full">
          <div class="status-item">
            <img src="@/assets/imgs/monitor-speed.png" />
            <div class="status-main">
              <div class="flex items-baseline gap-4px">
                <span class="text-24px font-bold">{{ statusRecord?.speed?.toFixed(1) ?? '0.0' }}</span>
                <span class="text-12px text-gray-400">m/s 速度</span>
              </div>
            </div>
            <div class="status-extra">
              <span
                v-if="statusRecord"
                class="text-14px font-medium"
                :style="{ color: getSpeedLabel(statusRecord.speed).color }"
              >
                {{ getSpeedLabel(statusRecord.speed).text }}
              </span>
            </div>
          </div>
        </NCard>
      </NGi>
    </NGrid>
  </NCard>
</template>

<style scoped lang="scss">
.status-item {
  display: flex;
  align-items: center;
  // justify-content: center;
  gap: 12px;
  width: 100%;
  img{
    width: 60px;
    height: 60px;
    object-fit: contain;
  }
}

.status-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.status-extra {
  display: flex;
  align-items: center;
  margin-left: 8px;
}
</style>
