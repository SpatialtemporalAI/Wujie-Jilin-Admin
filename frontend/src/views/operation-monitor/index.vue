<script setup lang="ts">
import { ref } from 'vue';
import { useRobotMonitor } from './composables/useRobotMonitor';
import RobotStatusCard from './modules/robot-status-card.vue';
import PositionMapPanel from './modules/position-map-panel.vue';
import AlertPanel from './modules/alert-panel.vue';
import VideoPlayer from './modules/video-player.vue';

defineOptions({ name: 'OperationMonitorPage' });

const activeTab = ref('realtime');

const {
  robotList,
  selectedRobotId,
  selectedRobot,
  latestStatus,
  parsedLocation,
  loading,
  selectRobot
} = useRobotMonitor();
</script>

<template>
  <div class="flex-col-stretch gap-16px overflow-y-auto pb-16px">
    <NSpin :show="loading">
      <div class="flex flex-col gap-16px">
        <!-- 机器人选择 + 状态卡片 -->
        <RobotStatusCard
          :robot-list="robotList"
          :selected-robot="selectedRobot"
          :status-record="latestStatus"
          @select="selectRobot"
        />

        <!-- Tab 切换 -->
        <NCard :bordered="false" size="small" class="card-wrapper">
          <NTabs v-model:value="activeTab" type="line" animated>
            <NTabPane name="realtime" tab="实时">
              <NGrid :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
                <NGi span="24 m:16">
                  <NCard :bordered="true" size="small" content-class="!p-0 overflow-hidden">
                    <template #header>
                      <NSpace align="center" :size="8">
                        <span>实时位置</span>
                        <NTag v-if="selectedRobot?.status === 'online'" type="success" size="small" round>
                          直播中
                        </NTag>
                      </NSpace>
                    </template>
                    <div class="h-520px">
                      <PositionMapPanel
                        :map-id="selectedRobot?.map_id ?? null"
                        :location="parsedLocation"
                        :robot-name="selectedRobot?.name ?? ''"
                      />
                    </div>
                  </NCard>
                </NGi>
                <NGi span="24 m:8">
                  <div class="h-520px">
                    <AlertPanel class="h-full" :robot-id="selectedRobotId" />
                  </div>
                </NGi>
              </NGrid>
            </NTabPane>
            <NTabPane name="video" tab="视频监控">
              <VideoPlayer
                :robot-id="selectedRobot?.id ?? 0"
                :serial-number="selectedRobot?.serial_number ?? ''"
              />
            </NTabPane>
          </NTabs>
        </NCard>
      </div>
    </NSpin>
  </div>
</template>

<style scoped></style>
