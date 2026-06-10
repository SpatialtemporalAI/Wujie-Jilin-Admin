<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue';
import { useMessage } from 'naive-ui';
import {
  fetchGetVoiceConfig,
  fetchSaveVoiceConfig,
  fetchTestWakeWord,
  fetchTestTTS
} from '@/service/api';
import { useNaiveForm } from '@/hooks/common/form';

defineOptions({ name: 'VoiceSynthesisTab' });

const message = useMessage();
const { formRef, validate } = useNaiveForm();
const loading = ref(false);
const showAlert = ref(false);

const model = reactive<Api.RobotConfig.VoiceConfig>({
  wake_word: '',
  tts_voice: 'xiaoyan',
  tts_speed: 50,
  tts_volume: 80
});

const rules = computed(() => ({
  wake_word: [
    { required: true, message: '请输入唤醒词', trigger: 'blur' },
    { min: 4, max: 6, message: '唤醒词必须为 4-6 个字', trigger: 'blur' }
  ],
  tts_voice: { required: true, message: '请选择音色', trigger: 'change' }
}));

const voiceOptions = [
  { label: '小燕', value: 'xiaoyan' },
  { label: '小宇', value: 'xiaoyu' },
  { label: '小倩', value: 'xiaoqian' },
  { label: '小杰', value: 'xiaojie' }
];

const canSaveWakeWord = computed(() => {
  const len = model.wake_word.trim().length;
  return len >= 4 && len <= 6;
});

async function loadConfig() {
  try {
    const { data, error } = await fetchGetVoiceConfig();
    if (!error && data) {
      Object.assign(model, data);
    }
  } catch (err) {
    console.error('加载语音配置失败:', err);
  }
}

async function handleSaveVoice() {
  try {
    await validate();
    loading.value = true;
    const { error } = await fetchSaveVoiceConfig(model);
    if (!error) {
      message.success('保存成功');
      showAlert.value = true;
      setTimeout(() => {
        showAlert.value = false;
      }, 5000);
    }
  } catch (err) {
    console.error('保存语音配置失败:', err);
  } finally {
    loading.value = false;
  }
}

async function handleTestWakeWord() {
  if (!canSaveWakeWord.value) {
    message.warning('唤醒词必须为 4-6 个字');
    return;
  }
  try {
    const { error } = await fetchTestWakeWord(model.wake_word);
    if (!error) {
      message.success('测试指令已下发');
    }
  } catch (err) {
    console.error('测试唤醒词失败:', err);
  }
}

async function handleTestTTS() {
  try {
    const { error } = await fetchTestTTS({
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
  loadConfig();
});
</script>

<template>
  <div class="flex-col gap-16px">
    <NAlert v-if="showAlert" type="info" closable>
      唤醒词设置成功，预计 1 分钟后生效
    </NAlert>

    <NForm ref="formRef" :model="model" :rules="rules" label-placement="left" :label-width="100">
      <!-- 唤醒词 -->
      <NCard title="唤醒词设置" size="small">
        <NGrid responsive="screen" :cols="1">
          <NFormItemGi label="唤醒词" path="wake_word">
            <NInput
              v-model:value="model.wake_word"
              placeholder="请输入 4-6 字唤醒词"
              maxlength="6"
              show-count
              clearable
            />
          </NFormItemGi>
          <NFormItemGi>
            <NSpace>
              <NButton type="primary" ghost @click="handleTestWakeWord">测试</NButton>
              <NButton type="primary" :disabled="!canSaveWakeWord" :loading="loading" @click="handleSaveVoice">
                保存
              </NButton>
            </NSpace>
          </NFormItemGi>
        </NGrid>
      </NCard>

      <!-- 语音合成 -->
      <NCard title="语音合成设置" size="small" class="mt-16px">
        <NGrid responsive="screen" :cols="1">
          <NFormItemGi label="音色" path="tts_voice">
            <NSelect v-model:value="model.tts_voice" :options="voiceOptions" placeholder="请选择音色" />
          </NFormItemGi>
          <NFormItemGi label="语速">
            <NSlider v-model:value="model.tts_speed" :min="0" :max="100" :step="1" />
            <span class="ml-8px">{{ model.tts_speed }}</span>
          </NFormItemGi>
          <NFormItemGi label="音量">
            <NSlider v-model:value="model.tts_volume" :min="0" :max="100" :step="1" />
            <span class="ml-8px">{{ model.tts_volume }}</span>
          </NFormItemGi>
          <NFormItemGi>
            <NSpace>
              <NButton type="primary" ghost @click="handleTestTTS">测试语音</NButton>
              <NButton type="primary" :loading="loading" @click="handleSaveVoice">保存设置</NButton>
            </NSpace>
          </NFormItemGi>
        </NGrid>
      </NCard>
    </NForm>
  </div>
</template>

<style scoped>
.mt-16px {
  margin-top: 16px;
}
.ml-8px {
  margin-left: 8px;
}
</style>
