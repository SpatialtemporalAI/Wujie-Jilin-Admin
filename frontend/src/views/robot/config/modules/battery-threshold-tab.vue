<script setup lang="tsx">
import { ref, onMounted } from 'vue';
import { NButton, NCard, NDataTable, NSlider, useMessage } from 'naive-ui';
import { fetchGetRobotList, fetchUpdateRobot } from '@/service/api';
import { useAppStore } from '@/store/modules/app';

defineOptions({ name: 'BatteryThresholdTab' });

const message = useMessage();
const appStore = useAppStore();

const robotList = ref<Api.Robot.Robot[]>([]);
const loading = ref(false);
const savingMap = ref<Record<number, boolean>>({});

async function loadRobots() {
  loading.value = true;
  try {
    const { data, error } = await fetchGetRobotList({ page: 1, page_size: 200 });
    if (!error && data) {
      robotList.value = data.records || [];
    }
  } catch (err) {
    console.error('加载机器人列表失败:', err);
  } finally {
    loading.value = false;
  }
}

async function handleSave(robot: Api.Robot.Robot) {
  savingMap.value[robot.id] = true;
  try {
    const { error } = await fetchUpdateRobot(robot.id, {
      battery_threshold: robot.battery_threshold
    });
    if (!error) {
      message.success('保存成功');
    }
  } catch (err) {
    console.error('保存电量阈值失败:', err);
  } finally {
    savingMap.value[robot.id] = false;
  }
}

const columns = [
  { key: 'index', title: '序号', align: 'center' as const, width: 64, render: (_: any, index: number) => index + 1 },
  { key: 'name', title: '机器人名称', align: 'center' as const, minWidth: 140 },
  { key: 'serial_number', title: '序列号', align: 'center' as const, width: 160 },
  {
    key: 'battery_threshold',
    title: '电量报警阈值',
    align: 'center' as const,
    minWidth: 280,
    render: (row: Api.Robot.Robot) => {
      const value = row.battery_threshold ?? 5;
      return (
        <div class="flex items-center gap-8px px-16px">
          <NSlider
            value={value}
            onUpdate:value={(v: number) => { row.battery_threshold = v; }}
            min={5}
            max={50}
            step={5}
            class="flex-1"
          />
          <span class="min-w-48px text-right">{value}%</span>
        </div>
      );
    }
  },
  {
    key: 'operate',
    title: '操作',
    align: 'center' as const,
    width: 120,
    render: (row: Api.Robot.Robot) => (
      <NButton
        type="primary"
        size="small"
        loading={savingMap.value[row.id]}
        onClick={() => handleSave(row)}
      >
        保存设置
      </NButton>
    )
  }
];

onMounted(() => {
  loadRobots();
});
</script>

<template>
  <div class="flex-col gap-16px">
    <NCard title="电量报警阈值设置" size="small">
      <NDataTable
        :columns="columns"
        :data="robotList"
        size="small"
        :loading="loading"
        :row-key="row => row.id"
        :scroll-x="600"
        :flex-height="!appStore.isMobile"
        class="sm:h-full"
      />
    </NCard>
  </div>
</template>

<style scoped>
.flex {
  display: flex;
}
.items-center {
  align-items: center;
}
.gap-8px {
  gap: 8px;
}
.px-16px {
  padding-left: 16px;
  padding-right: 16px;
}
.flex-1 {
  flex: 1;
}
.min-w-48px {
  min-width: 48px;
}
.text-right {
  text-align: right;
}
</style>
