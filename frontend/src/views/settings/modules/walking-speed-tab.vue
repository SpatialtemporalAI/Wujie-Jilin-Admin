<script setup lang="tsx">
import { ref, onMounted } from 'vue';
import { NButton, NCard, NDataTable, NSelect, useMessage } from 'naive-ui';
import { fetchGetRobotList, fetchUpdateRobot } from '@/service/api';
import { useAppStore } from '@/store/modules/app';

defineOptions({ name: 'WalkingSpeedTab' });

const message = useMessage();
const appStore = useAppStore();

const robotList = ref<Api.Robot.Robot[]>([]);
const loading = ref(false);
const savingMap = ref<Record<number, boolean>>({});

const speedOptions = [
  { label: '正常速度 1m/s', value: 'normal' },
  { label: '慢速 ≤0.8m/s', value: 'slow' },
  { label: '低速 0.5m/s', value: 'low' }
];

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
      speed_level: robot.speed_level
    });
    if (!error) {
      message.success('保存成功');
    }
  } catch (err) {
    console.error('保存速度设置失败:', err);
  } finally {
    savingMap.value[robot.id] = false;
  }
}

const columns = [
  { key: 'index', title: '序号', align: 'center' as const, width: 64, render: (_: any, index: number) => index + 1 },
  { key: 'name', title: '机器人名称', align: 'center' as const, minWidth: 140 },
  { key: 'serial_number', title: '序列号', align: 'center' as const, width: 160 },
  {
    key: 'speed_level',
    title: '速度等级',
    align: 'center' as const,
    width: 200,
    render: (row: Api.Robot.Robot) => (
      <NSelect
        v-model:value={row.speed_level}
        options={speedOptions}
        placeholder="请选择速度等级"
        clearable
      />
    )
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
    <NCard title="行走速度设置" size="small">
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

<style scoped></style>
