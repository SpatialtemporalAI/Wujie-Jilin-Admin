<script setup lang="ts">
import { useMonitorData } from './shared';
import SystemGauges from './modules/system-gauges.vue';
import ApiStatsChart from './modules/api-stats-chart.vue';

const { systemMetrics, apiStats, loading } = useMonitorData();
</script>

<template>
  <NSpace vertical :size="16">
    <NSpin :show="loading">
      <!-- 四宫格: CPU / 内存 / 系统信息 / 磁盘 -->
      <SystemGauges :metrics="systemMetrics" />

      <!-- API 统计折线图 -->
      <NCard :bordered="false" :title="$t('page.monitor.apiStats')" class="card-wrapper">
        <ApiStatsChart :data="apiStats" />
      </NCard>
    </NSpin>
  </NSpace>
</template>

<style scoped></style>
