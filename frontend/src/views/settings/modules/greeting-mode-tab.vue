<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useMessage } from 'naive-ui';
import { fetchGetAllRobots, fetchGetVoiceConfig, fetchUpdateGreetingMode } from '@/service/api';
import { useAuth } from '@/hooks/business/auth';

defineOptions({ name: 'GreetingModeTab' });

type GreetingMode = 'wave' | 'no_wave';

const { hasAuth } = useAuth();
const message = useMessage();

const robotList = ref<Api.Robot.AllRobot[]>([]);
const selectedRobotId = ref<number | null>(null);
const greetingMode = ref<GreetingMode>('wave');
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
    const { data, error } = await fetchGetVoiceConfig(robotId);
    if (!error && data) {
      greetingMode.value = data.greeting_mode || 'wave';
    }
  } catch (err) {
    console.error('加载打招呼模式失败:', err);
  } finally {
    configLoading.value = false;
  }
}

function handleSelectRobot(robotId: number | null) {
  selectedRobotId.value = robotId;
  greetingMode.value = 'wave';
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
    const { data, error } = await fetchUpdateGreetingMode(selectedRobotId.value, greetingMode.value);
    if (!error) {
      const msg = data?.grpc_status === 'pending_retry' ? '保存成功（设备同步待重试）' : '保存成功';
      message.success(msg);
    }
  } catch (err) {
    console.error('保存打招呼模式失败:', err);
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

    <NCard title="打招呼模式" size="small">
      <div v-if="!selectedRobotId" class="empty-tip">请先选择机器人</div>
      <NSpin v-else :show="configLoading">
        <div class="flex-col gap-16px">
          <div class="text-14px font-medium">
            当前机器人：{{ selectedRobot?.name }}（{{ selectedRobot?.serial_number }}）
          </div>
          <NForm label-placement="left" :label-width="100">
            <NFormItem label="动作模式">
              <NRadioGroup v-model:value="greetingMode">
                <NRadioButton value="wave">招手模式</NRadioButton>
                <NRadioButton value="no_wave">无招手模式</NRadioButton>
              </NRadioGroup>
            </NFormItem>
            <NFormItem>
              <div class="tip-text">
                招手模式下机器人检测到访客执行打招呼动作；无招手模式下机器人唤醒后无招手动作，仅语音问候。
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

.tip-text {
  color: #9ca3af;
  font-size: 13px;
  line-height: 1.6;
}

.empty-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 160px;
  color: #9ca3af;
}
</style>
