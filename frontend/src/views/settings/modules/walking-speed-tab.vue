<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useMessage } from 'naive-ui';
import { fetchGetRobot, fetchGetAllRobots, fetchUpdateSpeedLevel } from '@/service/api';
import { useAuth } from '@/hooks/business/auth';

defineOptions({ name: 'WalkingSpeedTab' });

const { hasAuth } = useAuth();
const message = useMessage();

const robotList = ref<Api.Robot.AllRobot[]>([]);
const selectedRobotId = ref<number | null>(null);
const speedLevel = ref<string | null>(null);
const robotLoading = ref(false);
const configLoading = ref(false);
const saving = ref(false);

// const speedOptions = [
//   { label: '正常速度 1m/s', value: 'normal' },
//   { label: '慢速 ≤0.8m/s', value: 'slow' },
//   { label: '低速 0.5m/s', value: 'low' }
// ];

const speedOptions = [
  { label: '快速 ≤0.5m/s', value: 'normal' },
  { label: '慢速 ≤0.25m/s', value: 'slow' }
];

const robotOptions = computed(() =>
  robotList.value.map(robot => ({
    label: `${robot.name}`,
    value: robot.id
  }))
);

const selectedRobot = computed(() => robotList.value.find(robot => robot.id === selectedRobotId.value) || null);

async function loadRobots() {
  robotLoading.value = true;
  try {
    // 跨模块下拉用 /robot/manage/all（仅需登录，无 robot:manage:list 权限），
    // 避免参数配置页面因缺少机器人管理权限而报「权限不足」
    const { data, error } = await fetchGetAllRobots();
    if (!error && data) {
      robotList.value = data;
    }
  } catch (err) {
    console.error('加载机器人列表失败:', err);
  } finally {
    robotLoading.value = false;
  }
}

async function loadConfig(robotId: number) {
  configLoading.value = true;
  try {
    const { data, error } = await fetchGetRobot(robotId);
    if (!error && data) {
      speedLevel.value = data.speed_level || null;
    }
  } catch (err) {
    console.error('加载速度设置失败:', err);
  } finally {
    configLoading.value = false;
  }
}

function handleSelectRobot(robotId: number | null) {
  selectedRobotId.value = robotId;
  speedLevel.value = null;
  if (robotId) {
    loadConfig(robotId);
  }
}

async function handleSave() {
  if (!selectedRobotId.value) {
    message.warning('请先选择机器人');
    return;
  }

  saving.value = true;
  try {
    const { data, error } = await fetchUpdateSpeedLevel(selectedRobotId.value, speedLevel.value);
    if (!error) {
      const msg = data?.grpc_status === 'pending_retry' ? '保存成功（设备同步待重试）' : '保存成功';
      message.success(msg);
    }
  } catch (err) {
    console.error('保存速度设置失败:', err);
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  loadRobots();
});
</script>

<template>
  <div class="flex-col gap-16px">
    <NCard title="选择机器人" size="small">
      <NSelect :value="selectedRobotId" :options="robotOptions" :loading="robotLoading" placeholder="请选择机器人" filterable
        clearable @update:value="handleSelectRobot" />
    </NCard>

    <NCard title="行走速度设置" size="small">
      <div v-if="!selectedRobotId" class="empty-tip">请先选择机器人</div>
      <NSpin v-else :show="configLoading">
        <div class="flex-col gap-16px">
          <div class="text-14px font-medium">
            当前机器人：{{ selectedRobot?.name }}（{{ selectedRobot?.serial_number }}）
          </div>
          <NForm label-placement="left" :label-width="100">
            <NFormItem label="速度等级">
              <NSelect v-model:value="speedLevel" :options="speedOptions" placeholder="请选择速度等级" clearable />
            </NFormItem>
            <NFormItem>
              <NButton v-if="hasAuth('robot:config:edit')" type="primary" :loading="saving" @click="handleSave">
                保存设置
              </NButton>
            </NFormItem>
          </NForm>
        </div>
      </NSpin>
    </NCard>
  </div>
</template>

<style scoped>
.flex-col {
  display: flex;
  flex-direction: column;
}

.gap-16px {
  gap: 16px;
}

.text-14px {
  font-size: 14px;
}

.font-medium {
  font-weight: 500;
}

.empty-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 160px;
  color: #9ca3af;
}
</style>
