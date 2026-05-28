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
    trigger: 'axis',
    axisPointer: {
      type: 'cross'
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
    type: 'category',
    boundaryGap: false,
    data: [] as string[]
  },
  yAxis: [
    {
      type: 'value',
      name: $t('page.monitor.avgResponseTime'),
      position: 'left',
      axisLabel: {
        formatter: '{value} ms'
      }
    },
    {
      type: 'value',
      name: $t('page.monitor.errorRate'),
      position: 'right',
      axisLabel: {
        formatter: '{value} %'
      }
    }
  ],
  series: [
    {
      name: $t('page.monitor.avgResponseTime'),
      type: 'line',
      smooth: true,
      yAxisIndex: 0,
      data: [] as number[]
    },
    {
      name: $t('page.monitor.errorRate'),
      type: 'line',
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
