<script setup lang="ts">
import { watch } from 'vue';
import { useEcharts } from '@/hooks/common/echarts';
import { $t } from '@/locales';

interface Props {
  data?: Api.Monitor.ApiStats[];
}

const props = withDefaults(defineProps<Props>(), {
  data: () => []
});

const { domRef, updateOptions } = useEcharts(() => ({
  tooltip: {
    trigger: 'axis' as const,
    axisPointer: {
      type: 'cross' as const
    }
  },
  legend: {
    data: [$t('page.monitor.avgResponseTime'), $t('page.monitor.errorRate')],
    top: '0'
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '15%',
    containLabel: true
  },
  xAxis: {
    type: 'category' as const,
    boundaryGap: false,
    data: [] as string[]
  },
  yAxis: [
    {
      type: 'value' as const,
      name: $t('page.monitor.avgResponseTime'),
      position: 'left' as const,
      axisLabel: {
        formatter: '{value} ms'
      }
    },
    {
      type: 'value' as const,
      name: $t('page.monitor.errorRate'),
      position: 'right' as const,
      axisLabel: {
        formatter: '{value} %'
      }
    }
  ],
  series: [
    {
      name: $t('page.monitor.avgResponseTime'),
      type: 'line' as const,
      smooth: true,
      yAxisIndex: 0,
      data: [] as number[]
    },
    {
      name: $t('page.monitor.errorRate'),
      type: 'line' as const,
      smooth: true,
      yAxisIndex: 1,
      data: [] as number[]
    }
  ]
}));

watch(
  () => props.data,
  val => {
    if (!val || val.length === 0) return;
    updateOptions(opts => {
      opts.xAxis.data = val.map(item => item.timestamp);
      opts.series[0].data = val.map(item => item.avg_elapsed_ms);
      opts.series[1].data = val.map(item => item.error_rate);
      return opts;
    });
  },
  { immediate: true, deep: true }
);
</script>

<template>
  <div ref="domRef" class="h-360px overflow-hidden"></div>
</template>

<style scoped></style>
