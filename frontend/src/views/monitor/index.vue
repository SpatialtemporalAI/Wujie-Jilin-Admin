<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useMonitorData } from './shared';
import SystemGauges from './modules/system-gauges.vue';
import ApiStatsChart from './modules/api-stats-chart.vue';
import SystemInfoCards from './modules/system-info-cards.vue';

const appStore = useAppStore();
const gap = computed(() => (appStore.isMobile ? 0 : 16));

const { systemMetrics, apiStats, loading } = useMonitorData();

const cpuPercent = computed(() => systemMetrics.value?.cpu_percent ?? 0);
const memoryPercent = computed(() => systemMetrics.value?.memory.percent ?? 0);
const diskPercent = computed(() => systemMetrics.value?.disk.percent ?? 0);

const bootTime = computed(() => systemMetrics.value?.boot_time ?? '');
const processCount = computed(() => systemMetrics.value?.process_count ?? 0);
const pythonVersion = computed(() => systemMetrics.value?.python_version ?? '');
const osName = computed(() => systemMetrics.value?.os_name ?? '');
const cpuCount = computed(() => systemMetrics.value?.cpu_count ?? 0);
</script>

<template>
  <NSpace vertical :size="16">
    <NSpin :show="loading">
      <!-- 仪表盘: CPU / 内存 / 磁盘 -->
      <NCard :bordered="false" :title="$t('page.monitor.systemResources')" class="card-wrapper">
        <SystemGauges
          :cpu-percent="cpuPercent"
          :memory-percent="memoryPercent"
          :disk-percent="diskPercent"
          :disk-total-mb="systemMetrics?.disk?.total_mb ?? 0"
          :disk-used-mb="systemMetrics?.disk?.used_mb ?? 0"
          :disk-total-gb="systemMetrics?.disk?.total ?? 0"
          :disk-used-gb="systemMetrics?.disk?.used ?? 0"
        />
      </NCard>

      <!-- API 统计折线图 -->
      <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
        <NGi span="24">
          <NCard :bordered="false" :title="$t('page.monitor.apiStats')" class="card-wrapper">
            <ApiStatsChart :data="apiStats" />
          </NCard>
        </NGi>
      </NGrid>

      <!-- 系统信息卡片 -->
      <NCard :bordered="false" :title="$t('page.monitor.systemInfo')" class="card-wrapper">
        <SystemInfoCards
          :boot-time="bootTime"
          :process-count="processCount"
          :python-version="pythonVersion"
          :os-name="osName"
          :cpu-count="cpuCount"
        />
      </NCard>
    </NSpin>
  </NSpace>
</template>

<style scoped></style>
