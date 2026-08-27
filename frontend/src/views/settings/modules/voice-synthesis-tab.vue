<script setup lang="ts">
import { computed, onActivated, onMounted, reactive, ref } from 'vue';
import { NRadioButton, NRadioGroup, NText, useMessage } from 'naive-ui';
import {
  fetchGetAllRobots,
  fetchGetVoiceConfig,
  fetchSaveVoiceConfig,
  fetchTestTTS,
  fetchTestWakeWord
} from '@/service/api';
import { useNaiveForm } from '@/hooks/common/form';
import { useAuth } from '@/hooks/business/auth';
import SvgIcon from '@/components/custom/svg-icon.vue';

defineOptions({ name: 'VoiceSynthesisTab' });

const { hasAuth } = useAuth();
const message = useMessage();
const { formRef, validate, restoreValidation } = useNaiveForm();
const loading = ref(false);
const saving = ref(false);
const robotLoading = ref(false);
const showAlert = ref(false);
const wakeWordTestText = ref('');
let wakeWordTestTimer: ReturnType<typeof setTimeout> | null = null;

const robotList = ref<Api.Robot.AllRobot[]>([]);
const selectedRobotId = ref<number | null>(null);

const model = reactive<Api.RobotConfig.VoiceConfig>({
  robot_id: 0,
  wake_word_enabled: true,
  wake_word: '',
  tts_voice: 'female',
  tts_speed: 1.0,
  tts_volume: 80,
  greeting_mode: 'wave'
});

const rules = computed(() => ({
  wake_word: !faceWakeEnabled.value
    ? [
        { required: true, message: '请输入唤醒词', trigger: 'blur' },
        {
          validator: (_rule: unknown, value: string) => {
            if (!value) return true;
            if (!/^[\u4E00-\u9FA5]{4,6}$/.test(value)) {
              return new Error('唤醒词必须为 4-6 个中文汉字，不能包含字母、数字、符号或空格');
            }
            return true;
          },
          trigger: 'blur'
        }
      ]
    : [],
  tts_voice: { required: true, message: '请选择音色', trigger: 'change' }
}));

const voiceOptions = [
  { label: '男声', value: 'male' },
  { label: '女声', value: 'female' }
];

const robotOptions = computed(() =>
  robotList.value.map(robot => ({
    label: `${robot.name}`,
    value: robot.id
  }))
);

/**
 * 人脸识别（免唤醒）开关 - UI 状态
 * 与后端 wake_word_enabled 字段语义相反：
 *   faceWakeEnabled = true  ⇒ 人脸识别免唤醒模式（wake_word_enabled=false）
 *   faceWakeEnabled = false ⇒ 唤醒词模式（wake_word_enabled=true）
 */
const faceWakeEnabled = computed<boolean>({
  get: () => !model.wake_word_enabled,
  set: val => {
    model.wake_word_enabled = !val;
  }
});

const canSaveWakeWord = computed(() => {
  // 唤醒词模式下才校验
  if (faceWakeEnabled.value) return true;
  return /^[\u4E00-\u9FA5]{4,6}$/.test(model.wake_word);
});

const selectedRobot = computed(() => robotList.value.find(r => r.id === selectedRobotId.value) || null);

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

function resetModel() {
  Object.assign(model, {
    robot_id: selectedRobotId.value || 0,
    wake_word_enabled: true,
    wake_word: '',
    tts_voice: 'female',
    tts_speed: 1.0,
    tts_volume: 80,
    greeting_mode: 'wave'
  });
}

async function loadConfig(robotId: number) {
  loading.value = true;
  resetModel();
  try {
    const { data, error } = await fetchGetVoiceConfig(robotId);
    if (!error && data) {
      Object.assign(model, data);
      // 兜底：后端旧数据可能返回 null/空，避免 NRadioGroup 因 null 失去绑定
      if (!model.greeting_mode) {
        model.greeting_mode = 'wave';
      }
    }
  } catch (err) {
    console.error('加载语音配置失败:', err);
  } finally {
    loading.value = false;
  }
}

function handleSelectRobot(robotId: number | null) {
  selectedRobotId.value = robotId;
  restoreValidation();
  if (robotId) {
    loadConfig(robotId);
  } else {
    resetModel();
  }
}

onActivated(() => {
  // 页面被 keep-alive 缓存后重新进入时刷新当前配置
  if (selectedRobotId.value) {
    loadConfig(selectedRobotId.value);
  }
});

async function handleSaveVoice() {
  // 顶层互斥：锁必须在任何 await（含 validate）之前置位，挡住双击导致的 1s 内重复提交
  if (saving.value) return;
  saving.value = true;
  try {
    if (!selectedRobotId.value) {
      message.warning('请先选择机器人');
      return;
    }
    await validate();
    const { data, error } = await fetchSaveVoiceConfig(model);
    if (!error) {
      const msg = data?.grpc_status === 'pending_retry' ? '保存成功（设备同步待重试）' : '保存成功';
      message.success(msg);
      showAlert.value = true;
      setTimeout(() => {
        showAlert.value = false;
      }, 5000);
    }
  } catch (err) {
    console.error('保存语音配置失败:', err);
  } finally {
    saving.value = false;
  }
}

async function handleTestWakeWord() {
  if (!selectedRobotId.value) {
    message.warning('请先选择机器人');
    return;
  }
  if (faceWakeEnabled.value) {
    message.warning('人脸识别免唤醒模式下无需测试唤醒词');
    return;
  }
  if (!canSaveWakeWord.value) {
    message.warning('唤醒词必须为 4-6 个字');
    return;
  }
  // 点击后立即显示提示文字
  wakeWordTestText.value = `${model.wake_word}在呢，有什么可以帮您？`;
  if (wakeWordTestTimer) clearTimeout(wakeWordTestTimer);
  wakeWordTestTimer = setTimeout(() => {
    wakeWordTestText.value = '';
  }, 5000);
  try {
    const { error } = await fetchTestWakeWord({
      robot_id: model.robot_id,
      text: model.wake_word
    });
    if (!error) {
      message.success('测试指令已下发');
    }
  } catch (err) {
    console.error('测试唤醒词失败:', err);
  }
}

async function handleTestTTS() {
  if (!selectedRobotId.value) {
    message.warning('请先选择机器人');
    return;
  }
  try {
    const { error } = await fetchTestTTS({
      robot_id: model.robot_id,
      voice: model.tts_voice,
      speed: model.tts_speed,
      volume: model.tts_volume,
      text: '您好，这是语音合成测试。'
    });
    if (!error) {
      message.success('测试指令已下发');
    }
  } catch (err) {
    console.error('测试TTS失败:', err);
  }
}

onMounted(() => {
  loadRobots();
});
</script>

<template>
  <div class="flex-col gap-16px">
    <!-- 选择机器人 -->
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

    <!-- 配置区域 -->
    <NCard title="语音配置" size="small">
      <div v-if="!selectedRobotId" class="empty-tip">请先选择机器人</div>
      <NSpin v-else :show="loading">
        <div class="flex-col gap-16px">
          <NAlert v-if="showAlert" type="info" closable>唤醒词设置成功，预计 1 分钟后生效</NAlert>

          <div class="text-14px font-medium">
            当前机器人：{{ selectedRobot?.name }}（{{ selectedRobot?.serial_number }}）
          </div>

          <NForm ref="formRef" :model="model" :rules="rules" label-placement="top">
            <div class="config-row">
              <!-- 唤醒词配置 -->
              <NCard title="唤醒词配置" size="small" class="config-card">
                <NGrid :cols="1" :y-gap="8">
                  <NFormItemGi label="人脸识别（免唤醒）">
                    <div class="flex-col gap-4px">
                      <div class="flex-y-center">
                        <NSwitch v-model:value="faceWakeEnabled" />
                        <span class="ml-8px text-gray-400">
                          {{ faceWakeEnabled ? '已开启' : '已关闭' }}
                        </span>
                      </div>
                      <NText depth="3" class="text-13px leading-relaxed">
                        关闭时通过唤醒词与机器人交互；开启时检测到人脸可直接唤醒机器人，无需唤醒词
                      </NText>
                    </div>
                  </NFormItemGi>
                  <NFormItemGi v-if="!faceWakeEnabled" label="唤醒词" path="wake_word">
                    <NInput
                      v-model:value="model.wake_word"
                      placeholder="请输入 4-6 个中文汉字"
                      maxlength="6"
                      show-count
                      clearable
                    />
                  </NFormItemGi>
                  <NFormItemGi v-if="!faceWakeEnabled">
                    <NSpace align="center" wrap>
                      <NButton
                        v-if="hasAuth('robot:config:edit')"
                        type="primary"
                        ghost
                        size="small"
                        :disabled="!canSaveWakeWord"
                        @click="handleTestWakeWord"
                      >
                        测试
                      </NButton>
                      <div v-if="wakeWordTestText" class="flex-y-center gap-4px">
                        <SvgIcon icon="mdi:volume-high" class="text-16px" />
                        <NText type="info" class="text-14px">
                          {{ wakeWordTestText }}
                        </NText>
                      </div>
                    </NSpace>
                  </NFormItemGi>
                </NGrid>
              </NCard>

              <!-- 打招呼模式 -->
              <NCard title="打招呼模式" size="small" class="config-card">
                <NGrid :cols="1" :y-gap="8">
                  <NFormItemGi label="动作模式">
                    <NRadioGroup v-model:value="model.greeting_mode" size="small">
                      <NRadioButton value="wave">招手模式</NRadioButton>
                      <NRadioButton value="no_wave">无招手模式</NRadioButton>
                    </NRadioGroup>
                  </NFormItemGi>
                  <NFormItemGi>
                    <div class="tip-text">
                      招手模式下机器人检测到访客执行打招呼动作；无招手模式下机器人唤醒后无招手动作，仅语音问候。
                    </div>
                  </NFormItemGi>
                </NGrid>
              </NCard>

              <!-- 语音合成设置 -->
              <NCard title="语音合成设置" size="small" class="config-card">
                <NGrid :cols="1" :y-gap="8">
                  <NFormItemGi label="音色" path="tts_voice">
                    <NSelect v-model:value="model.tts_voice" :options="voiceOptions" placeholder="请选择音色" />
                  </NFormItemGi>
                  <NFormItemGi label="语速">
                    <div class="w-full flex-col gap-8px">
                      <NSlider
                        v-model:value="model.tts_speed"
                        :min="0.5"
                        :max="2"
                        :step="0.1"
                        :tooltip="false"
                        :marks="{ 0.5: '0.5', 1: '1.0', 1.5: '1.5', 2: '2.0' }"
                      />
                      <span class="text-13px text-gray-400">当前语速：{{ model.tts_speed.toFixed(1) }} 倍</span>
                    </div>
                  </NFormItemGi>
                  <NFormItemGi label="音量">
                    <div class="w-full flex-col gap-8px">
                      <NSlider
                        v-model:value="model.tts_volume"
                        :min="0"
                        :max="100"
                        :step="1"
                        :tooltip="false"
                        :marks="{ 0: '0', 50: '50', 100: '100' }"
                      />
                      <span class="text-13px text-gray-400">当前音量：{{ model.tts_volume }}</span>
                    </div>
                  </NFormItemGi>
                  <NFormItemGi>
                    <NSpace>
                      <NButton v-if="hasAuth('robot:config:edit')" type="primary" ghost size="small" @click="handleTestTTS">
                        测试语音
                      </NButton>
                    </NSpace>
                  </NFormItemGi>
                </NGrid>
              </NCard>
            </div>

            <div class="mt-16px">
              <NButton
                v-if="hasAuth('robot:config:edit')"
                type="primary"
                :loading="saving"
                :disabled="!canSaveWakeWord"
                @click="handleSaveVoice"
              >
                保存设置
              </NButton>
            </div>
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
.flex-1 {
  flex: 1;
}
.gap-16px {
  gap: 16px;
}
.gap-4px {
  gap: 4px;
}
.gap-8px {
  gap: 8px;
}
.w-full {
  width: 100%;
}
.mt-16px {
  margin-top: 16px;
}
.ml-8px {
  margin-left: 8px;
}
.text-14px {
  font-size: 14px;
}
.text-13px {
  font-size: 13px;
}
.font-medium {
  font-weight: 500;
}
.text-gray-400 {
  color: #9ca3af;
}
.leading-relaxed {
  line-height: 1.6;
}
.empty-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 160px;
  color: #9ca3af;
}
.config-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  align-items: stretch;
}

.config-card {
  min-width: 0;
}

.config-card :deep(.n-card__content) {
  padding: 16px;
}

.flex-y-center {
  display: flex;
  align-items: center;
}

.tip-text {
  color: #9ca3af;
  font-size: 13px;
  line-height: 1.6;
}

@media (max-width: 1024px) {
  .config-row {
    grid-template-columns: 1fr;
  }
}
</style>
