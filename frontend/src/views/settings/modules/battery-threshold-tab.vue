<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { NText, useMessage } from 'naive-ui';
import { fetchGetAllRobots, fetchGetRobot, fetchUpdateBatteryThreshold } from '@/service/api';
import { useAuth } from '@/hooks/business/auth';

defineOptions({ name: 'BatteryThresholdTab' });

const { hasAuth } = useAuth();
const message = useMessage();

const robotList = ref<Api.Robot.AllRobot[]>([]);
const selectedRobotId = ref<number | null>(null);
const batteryThreshold = ref(5);
const robotLoading = ref(false);
const configLoading = ref(false);
const saving = ref(false);

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
      batteryThreshold.value = data.battery_threshold ?? 5;
    }
  } catch (err) {
    console.error('加载电量阈值失败:', err);
  } finally {
    configLoading.value = false;
  }
}

function handleSelectRobot(robotId: number | null) {
  selectedRobotId.value = robotId;
  batteryThreshold.value = 5;
  if (robotId) {
    loadConfig(robotId);
  }
}

async function handleSave() {
  // 顶层互斥：锁必须在任何 await 之前置位，挡住双击导致的 1s 内重复提交
  if (saving.value) return;
  saving.value = true;
  try {
    if (!selectedRobotId.value) {
      message.warning('请先选择机器人');
      return;
    }
    const { data, error } = await fetchUpdateBatteryThreshold(selectedRobotId.value, batteryThreshold.value);
    if (!error) {
      const msg = data?.grpc_status === 'pending_retry' ? '保存成功（设备同步待重试）' : '保存成功';
      message.success(msg);
    }
  } catch (err) {
    console.error('保存电量阈值失败:', err);
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
      <NSelect
        :value="selectedRobotId"
        :options="robotOptions"
        :loading="robotLoading"
        placeholder="请选择机器人"
        filterable
        clearable
        @update:value="handleSelectRobot"
      />
    </NCard>

    <NCard title="电量报警阈值设置" size="small">
      <div v-if="!selectedRobotId" class="empty-tip">请先选择机器人</div>
      <NSpin v-else :show="configLoading">
        <div class="flex-col gap-16px">
          <div class="text-14px font-medium">
            当前机器人：{{ selectedRobot?.name }}（{{ selectedRobot?.serial_number }}）
          </div>
          <NForm label-placement="left" :label-width="120">
            <NFormItem label="电量报警阈值">
              <div class="w-full flex-col gap-4px">
                <div class="slider-row">
                  <NSlider v-model:value="batteryThreshold" :min="5" :max="50" :step="5" />
                  <span class="threshold-value">{{ batteryThreshold }}%</span>
                </div>
                <NText depth="3" class="text-12px">
                  拖动滑块调整阈值（范围 5% - 50%），电量低于该值时将触发低电量告警。
                </NText>
              </div>
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
.slider-row {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 12px;
}
.threshold-value {
  min-width: 48px;
  text-align: right;
}
.w-full {
  width: 100%;
}
.gap-4px {
  gap: 4px;
}
.text-12px {
  font-size: 12px;
}
</style>
