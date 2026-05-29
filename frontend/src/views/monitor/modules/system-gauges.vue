<script setup lang="ts">
import { watch } from 'vue';
import { useEcharts } from '@/hooks/common/echarts';
import { $t } from '@/locales';

interface Props {
  cpuPercent?: number;
  memoryPercent?: number;
  diskPercent?: number;
  diskTotalMb?: number;
  diskUsedMb?: number;
  diskTotalGb?: number;
  diskUsedGb?: number;
}

const props = withDefaults(defineProps<Props>(), {
  cpuPercent: 0,
  memoryPercent: 0,
  diskPercent: 0,
  diskTotalMb: 0,
  diskUsedMb: 0,
  diskTotalGb: 0,
  diskUsedGb: 0
});

function getGaugeOption(title: string, value: number, color: string) {
  return {
    series: [
      {
        type: 'gauge',
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: 100,
        splitNumber: 10,
        itemStyle: {
          color
        },
        progress: {
          show: true,
          width: 12
        },
        pointer: {
          show: true,
          width: 4
        },
        axisLine: {
          lineStyle: {
            width: 12
          }
        },
        axisTick: {
          distance: -18,
          splitNumber: 5,
          lineStyle: {
            width: 1,
            color: '#999'
          }
        },
        splitLine: {
          distance: -22,
          length: 8,
          lineStyle: {
            width: 2,
            color: '#999'
          }
        },
        axisLabel: {
          distance: -14,
          color: '#999',
          fontSize: 10
        },
        anchor: {
          show: true,
          size: 15,
          itemStyle: {
            borderWidth: 2
          }
        },
        title: {
          show: true,
          offsetCenter: [0, '70%'],
          fontSize: 14
        },
        detail: {
          valueAnimation: true,
          fontSize: 20,
          offsetCenter: [0, '50%'],
          formatter: '{value}%'
        },
        data: [
          {
            value: Math.round(value),
            name: title
          }
        ]
      }
    ]
  };
}

const { domRef: cpuDomRef, updateOptions: updateCpu } = useEcharts(() =>
  getGaugeOption($t('page.monitor.cpuUsage'), 0, '#5470c6')
);
const { domRef: memoryDomRef, updateOptions: updateMemory } = useEcharts(() =>
  getGaugeOption($t('page.monitor.memoryUsage'), 0, '#91cc75')
);
const { domRef: diskDomRef, updateOptions: updateDisk } = useEcharts(() =>
  getGaugeOption($t('page.monitor.diskUsage'), 0, '#fac858')
);

watch(
  () => props.cpuPercent,
  val => {
    updateCpu(opts => {
      opts.series[0].data[0].value = Math.round(val);
      return opts;
    });
  }
);

watch(
  () => props.memoryPercent,
  val => {
    updateMemory(opts => {
      opts.series[0].data[0].value = Math.round(val);
      return opts;
    });
  }
);

watch(
  () => props.diskPercent,
  val => {
    updateDisk(opts => {
      opts.series[0].data[0].value = Math.round(val);
      return opts;
    });
  }
);
</script>

<template>
  <NGrid cols="s:1 m:2" responsive="screen" :x-gap="16" :y-gap="16">
    <NGi>
      <div ref="cpuDomRef" class="h-260px overflow-hidden"></div>
    </NGi>
    <NGi>
      <div ref="memoryDomRef" class="h-260px overflow-hidden"></div>
    </NGi>
    <NGi span="m:2">
      <div class="flex items-center">
        <div class="flex-1">
          <NDescriptions label-placement="left" :column="1" bordered size="small">
            <NDescriptionsItem label="Total (MB)">
              {{ props.diskTotalMb?.toLocaleString() }}
            </NDescriptionsItem>
            <NDescriptionsItem label="Used (MB)">
              {{ props.diskUsedMb?.toLocaleString() }}
            </NDescriptionsItem>
            <NDescriptionsItem label="Total (GB)">
              {{ props.diskTotalGb?.toLocaleString() }}
            </NDescriptionsItem>
            <NDescriptionsItem label="Used (GB)">
              {{ props.diskUsedGb?.toLocaleString() }}
            </NDescriptionsItem>
          </NDescriptions>
        </div>
        <div ref="diskDomRef" class="h-260px w-300px flex-shrink-0 overflow-hidden"></div>
      </div>
    </NGi>
  </NGrid>
</template>

<style scoped></style>
