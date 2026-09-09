<script setup lang="ts">
import { computed, onActivated, onMounted, reactive, ref } from 'vue';
import { NSwitch, NText, useMessage } from 'naive-ui';
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
const replyTestText = ref('');
let replyTestTimer: ReturnType<typeof setTimeout> | null = null;

const robotList = ref<Api.Robot.AllRobot[]>([]);
const selectedRobotId = ref<number | null>(null);

const model = reactive<Api.RobotConfig.VoiceConfig>({
  robot_id: 0,
  wake_word_enabled: true,
  wake_word: '',
  tts_voice: 'female',
  tts_speed: 1.0,
  tts_volume: 80,
  greeting_mode: 'wave',
  wake_reply_mode: 'corpus',
  wake_reply_text: ''
});

/** 唤醒词占位符：预设语料模板中的【唤醒词】在展示/推送时替换为实际唤醒词 */
const WAKE_WORD_PLACEHOLDER = '【唤醒词】';

/** 预设回复语料模板原文（存库值，含占位符） */
const REPLY_TEMPLATES = {
  wake_prefix: '【唤醒词】在呢，有什么可以帮您',
  plain: '在呢，有什么可以帮您'
} as const;

type ReplyTemplateKey = keyof typeof REPLY_TEMPLATES | 'custom';

/** 语料模板选择（本地 UI 状态）：预设模板或自定义 */
const replyTemplate = ref<ReplyTemplateKey>('wake_prefix');
/** 自定义回复内容（本地 UI 状态） */
const customReplyText = ref('');

const replyTemplateOptions = [
  { label: '「唤醒词」在呢，有什么可以帮您', value: 'wake_prefix' },
  { label: '在呢，有什么可以帮您', value: 'plain' },
  { label: '自定义回复内容', value: 'custom' }
];

const replyModeOptions = [
  { label: '配置语料', value: 'corpus' },
  { label: '调用大模型', value: 'llm' }
];

/** 语料预览：模板原文替换占位符；自定义取输入值 */
const replyPreview = computed(() => {
  if (replyTemplate.value === 'custom') {
    return customReplyText.value.trim();
  }
  return REPLY_TEMPLATES[replyTemplate.value].split(WAKE_WORD_PLACEHOLDER).join(model.wake_word || '');
});

/** 根据加载到的 wake_reply_text 回填模板选择 */
function syncReplyTemplate() {
  const text = model.wake_reply_text || '';
  if (text === REPLY_TEMPLATES.wake_prefix) {
    replyTemplate.value = 'wake_prefix';
    customReplyText.value = '';
  } else if (text === REPLY_TEMPLATES.plain) {
    replyTemplate.value = 'plain';
    customReplyText.value = '';
  } else if (text) {
    replyTemplate.value = 'custom';
    customReplyText.value = text;
  } else {
    replyTemplate.value = 'wake_prefix';
    customReplyText.value = '';
  }
}

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

/**
 * 招手模式开关 - UI 状态
 *   greetingWaveEnabled = true  ⇒ 招手模式（greeting_mode='wave'）
 *   greetingWaveEnabled = false ⇒ 无招手模式（greeting_mode='no_wave'）
 */
const greetingWaveEnabled = computed<boolean>({
  get: () => model.greeting_mode === 'wave',
  set: val => {
    model.greeting_mode = val ? 'wave' : 'no_wave';
  }
});

const canSaveWakeWord = computed(() => {
  // 唤醒词模式下才校验
  if (faceWakeEnabled.value) return true;
  return /^[\u4E00-\u9FA5]{4,6}$/.test(model.wake_word);
});

/** 配置语料模式下回复语料必填（调用大模型 / 免唤醒模式不校验） */
const canSaveReply = computed(() => {
  if (faceWakeEnabled.value) return true;
  if (model.wake_reply_mode !== 'corpus') return true;
  return replyPreview.value.length > 0;
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
    greeting_mode: 'wave',
    wake_reply_mode: 'corpus',
    wake_reply_text: ''
  });
  replyTemplate.value = 'wake_prefix';
  customReplyText.value = '';
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
      if (!model.wake_reply_mode) {
        model.wake_reply_mode = 'corpus';
      }
      syncReplyTemplate();
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
    // 保存前把模板选择落到 wake_reply_text：预设模板存原文（含【唤醒词】占位符），自定义存输入
    if (model.wake_reply_mode === 'corpus') {
      model.wake_reply_text =
        replyTemplate.value === 'custom'
          ? customReplyText.value.trim()
          : REPLY_TEMPLATES[replyTemplate.value];
    }
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

async function handleTestReply() {
  if (!selectedRobotId.value) {
    message.warning('请先选择机器人');
    return;
  }
  if (model.wake_reply_mode !== 'corpus') {
    message.warning('调用大模型模式下无需测试回复语料');
    return;
  }
  if (!replyPreview.value) {
    message.warning('请先填写回复语料');
    return;
  }
  // 点击后立即显示提示文字
  replyTestText.value = replyPreview.value;
  if (replyTestTimer) clearTimeout(replyTestTimer);
  replyTestTimer = setTimeout(() => {
    replyTestText.value = '';
  }, 5000);
  try {
    // 复用 TTS 测试通道，按当前音色/语速/音量播报回复语料
    const { error } = await fetchTestTTS({
      robot_id: model.robot_id,
      voice: model.tts_voice,
      speed: model.tts_speed,
      volume: model.tts_volume,
      text: replyPreview.value
    });
    if (!error) {
      message.success('测试指令已下发');
    }
  } catch (err) {
    console.error('测试回复失败:', err);
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
      <NSelect :value="selectedRobotId" :options="robotOptions" :loading="robotLoading" placeholder="请选择机器人" filterable
        clearable @update:value="handleSelectRobot" />
    </NCard>

    <!-- 配置区域 -->
    <NCard title="语音配置" size="small">
      <div v-if="!selectedRobotId" class="empty-tip">请先选择机器人</div>
      <NSpin v-else :show="loading">
        <div class="flex-col gap-16px">
          <NAlert v-if="showAlert" type="info" closable>唤醒词设置成功，请等待生效</NAlert>

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
                      <NText depth="3" class="text-13px leading-relaxed mt-12px text-gray-700">
                        关闭时通过唤醒词与机器人交互；开启时检测到人脸可直接唤醒机器人，无需唤醒词
                      </NText>
                    </div>
                  </NFormItemGi>
                  <NFormItemGi v-if="!faceWakeEnabled" label="唤醒词" path="wake_word">
                    <NInput v-model:value="model.wake_word" placeholder="请输入 4-6 个中文汉字" maxlength="6" show-count
                      clearable />
                  </NFormItemGi>
                  <NFormItemGi v-if="!faceWakeEnabled">
                    <NSpace align="center" wrap>
                      <NButton v-if="hasAuth('robot:config:edit')" type="primary" ghost size="small"
                        :disabled="!canSaveWakeWord" @click="handleTestWakeWord">
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
                  <!-- 回复方式 -->
                  <NFormItemGi v-if="!faceWakeEnabled" label="回复方式">
                    <NRadioGroup v-model:value="model.wake_reply_mode">
                      <NSpace>
                        <NRadio v-for="opt in replyModeOptions" :key="opt.value" :value="opt.value">
                          {{ opt.label }}
                        </NRadio>
                      </NSpace>
                    </NRadioGroup>
                  </NFormItemGi>
                  <!-- 配置语料：模板选择 / 自定义输入 / 预览 -->
                  <template v-if="!faceWakeEnabled && model.wake_reply_mode === 'corpus'">
                    <NFormItemGi label="语料模板">
                      <NSelect v-model:value="replyTemplate" :options="replyTemplateOptions" />
                    </NFormItemGi>
                    <NFormItemGi v-if="replyTemplate === 'custom'" label="自定义回复内容">
                      <NInput v-model:value="customReplyText" placeholder="请输入自定义回复内容" maxlength="100"
                        show-count clearable />
                    </NFormItemGi>
                    <NFormItemGi v-else label="语料预览">
                      <div class="w-full flex-col gap-4px">
                        <div class="reply-preview">{{ replyPreview }}</div>
                        <NText depth="3" class="text-13px text-gray-700">
                          该模板不可编辑；如需自定义请在上方切换为「自定义回复内容」。
                        </NText>
                      </div>
                    </NFormItemGi>
                    <NFormItemGi>
                      <NSpace align="center" wrap>
                        <NButton v-if="hasAuth('robot:config:edit')" type="primary" ghost size="small"
                          :disabled="!replyPreview" @click="handleTestReply">
                          测试回复
                        </NButton>
                        <div v-if="replyTestText" class="flex-y-center gap-4px">
                          <SvgIcon icon="mdi:volume-high" class="text-16px" />
                          <NText type="info" class="text-14px">
                            "{{ replyTestText }}"
                          </NText>
                        </div>
                      </NSpace>
                    </NFormItemGi>
                  </template>
                  <NFormItemGi v-if="!faceWakeEnabled && model.wake_reply_mode === 'llm'">
                    <NText depth="3" class="text-13px leading-relaxed text-gray-700">
                      唤醒后由大模型生成回复语料，无需配置语料模板
                    </NText>
                  </NFormItemGi>
                </NGrid>
              </NCard>

              <!-- 打招呼模式 -->
              <NCard title="打招呼模式" size="small" class="config-card">
                <NGrid :cols="1" :y-gap="8">
                  <NFormItemGi label="招手模式">
                    <div class="flex-col gap-4px">
                      <div class="flex-y-center">
                        <NSwitch v-model:value="greetingWaveEnabled" />
                        <span class="ml-8px text-gray-400">
                          {{ greetingWaveEnabled ? '已开启' : '已关闭' }}
                        </span>
                      </div>
                      <NText depth="3" class="text-13px leading-relaxed mt-12px text-gray-700">
                        开启后机器人检测到访客执行打招呼动作；关闭后机器人唤醒后无招手动作，仅语音问候。
                      </NText>
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
                      <NSlider v-model:value="model.tts_speed" :min="0.5" :max="2" :step="0.1" :tooltip="false"
                        :marks="{ 0.5: '0.5', 1: '1.0', 1.5: '1.5', 2: '2.0' }" />
                      <span class="text-13px text-gray-400">当前语速：{{ model.tts_speed.toFixed(1) }} 倍</span>
                    </div>
                  </NFormItemGi>
                  <NFormItemGi label="音量">
                    <div class="w-full flex-col gap-8px">
                      <NSlider v-model:value="model.tts_volume" :min="0" :max="100" :step="1" :tooltip="false"
                        :marks="{ 0: '0', 50: '50', 100: '100' }" />
                      <span class="text-13px text-gray-400">当前音量：{{ model.tts_volume }}</span>
                    </div>
                  </NFormItemGi>
                  <NFormItemGi>
                    <NSpace>
                      <NButton v-if="hasAuth('robot:config:edit')" type="primary" ghost size="small"
                        @click="handleTestTTS">
                        测试语音
                      </NButton>
                    </NSpace>
                  </NFormItemGi>
                </NGrid>
              </NCard>
            </div>

            <div class="mt-16px">
              <NButton v-if="hasAuth('robot:config:edit')" type="primary" :loading="saving"
                :disabled="!canSaveWakeWord || !canSaveReply" @click="handleSaveVoice">
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

.reply-preview {
  padding: 8px 12px;
  border-radius: 6px;
  background: #f5f7fa;
  color: #4b5563;
  line-height: 1.6;
  word-break: break-all;
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

@media (max-width: 1024px) {
  .config-row {
    grid-template-columns: 1fr;
  }
}
</style>
