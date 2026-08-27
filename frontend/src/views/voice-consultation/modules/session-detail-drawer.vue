<script setup lang="ts">
import { ref, watch } from 'vue';
import {
  NButton,
  NDescriptions,
  NDescriptionsItem,
  NDivider,
  NDrawer,
  NDrawerContent,
  NEmpty,
  NSpin,
  NTag
} from 'naive-ui';
import dayjs from 'dayjs';
import { fetchGetVoiceConsultationSession } from '@/service/api';
import { $t } from '@/locales';

defineOptions({
  name: 'VoiceConsultationSessionDetailDrawer'
});

interface Props {
  sessionId: number | null;
}

const props = defineProps<Props>();

const visible = defineModel<boolean>('visible', { required: true });

const loading = ref(false);
const detail = ref<Api.VoiceConsultation.SessionDetail | null>(null);

const statusTagMap: Record<string, NaiveUI.ThemeColor> = {
  completed: 'success',
  in_progress: 'info',
  interrupted: 'warning'
};

const triggerTagMap: Record<string, NaiveUI.ThemeColor> = {
  wake_word: 'info',
  face_recognition: 'default'
};

watch(
  () => props.sessionId,
  async newId => {
    if (newId && visible.value) {
      await loadDetail(newId);
    }
  }
);

watch(visible, async val => {
  if (val && props.sessionId) {
    await loadDetail(props.sessionId);
  }
  if (!val) {
    detail.value = null;
  }
});

async function loadDetail(id: number) {
  loading.value = true;
  try {
    const { data, error } = await fetchGetVoiceConsultationSession(id);
    if (!error) {
      detail.value = data;
    }
  } catch (error) {
    console.error('获取语音问诊会话详情失败:', error);
  } finally {
    loading.value = false;
  }
}

function formatDuration(seconds: number | null): string {
  if (seconds == null) return '-';
  if (seconds < 60) return `${seconds} 秒`;
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return rest > 0 ? `${minutes} 分 ${rest} 秒` : `${minutes} 分`;
}

function formatTime(time: string | null): string {
  return time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-';
}

const INTENT_LABEL_KEYS = [
  'indoor_navigation',
  'triage_qa',
  'medical_guide',
  'health_check_notice',
  'insurance_guide',
  'admission_notice'
] as const;

function intentLabel(type: string | null): string {
  if (!type) return '-';
  const key = `page.manage.voiceConsultation.intentType.${type}` as App.I18n.I18nKey;
  return INTENT_LABEL_KEYS.includes(type as (typeof INTENT_LABEL_KEYS)[number]) ? $t(key) : type;
}
</script>

<template>
  <NDrawer v-model:show="visible" :width="560" display-directive="show">
    <NDrawerContent :title="$t('page.manage.voiceConsultation.detailTitle')" :native-scrollbar="false" closable>
      <NSpin :show="loading">
        <template v-if="detail">
          <NDescriptions label-placement="left" bordered :column="1" size="small">
            <NDescriptionsItem :label="$t('page.manage.voiceConsultation.time')">
              {{ formatTime(detail.occurred_at) }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.voiceConsultation.trigger')">
              <NTag :type="triggerTagMap[detail.trigger_method] || 'default'" size="small">
                {{ $t(`page.manage.voiceConsultation.triggerMethod.${detail.trigger_method}`) }}
              </NTag>
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.voiceConsultation.robot')">
              {{ detail.robot_name || detail.robot_id }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.voiceConsultation.turns')">
              {{ detail.turn_count }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.voiceConsultation.questionSummary')">
              {{ detail.question_summary || '-' }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.voiceConsultation.duration')">
              {{ formatDuration(detail.duration_seconds) }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.voiceConsultation.status')">
              <NTag :type="statusTagMap[detail.status] || 'default'" size="small">
                {{ $t(`page.manage.voiceConsultation.statusLabel.${detail.status}`) }}
              </NTag>
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.manage.voiceConsultation.createdAt')">
              {{ formatTime(detail.created_at) }}
            </NDescriptionsItem>
          </NDescriptions>

          <NDivider>{{ $t('page.manage.voiceConsultation.turnList') }}</NDivider>
          <NEmpty v-if="!detail.turns || detail.turns.length === 0" class="py-24px" />
          <div v-else class="flex flex-col gap-12px">
            <div
              v-for="turn in detail.turns"
              :key="turn.id"
              class="rounded-6px border border-gray-200 px-12px py-8px dark:border-dark-500"
            >
              <div class="flex-y-center gap-8px pb-4px">
                <NTag size="small" type="primary">
                  {{ $t('page.manage.voiceConsultation.turnNo') }} {{ turn.turn_no }}
                </NTag>
                <span v-if="turn.intent_type" class="text-12px text-gray-400">
                  {{ intentLabel(turn.intent_type) }}
                </span>
                <span v-if="turn.duration_seconds != null" class="text-12px text-gray-400">
                  {{ formatDuration(turn.duration_seconds) }}
                </span>
              </div>
              <div class="text-14px">
                <span class="font-500">{{ $t('page.manage.voiceConsultation.question') }}：</span>
                <span>{{ turn.question || '-' }}</span>
              </div>
              <div class="text-14px">
                <span class="font-500">{{ $t('page.manage.voiceConsultation.answer') }}：</span>
                <span>{{ turn.answer || '-' }}</span>
              </div>
            </div>
          </div>
        </template>
      </NSpin>
      <template #footer>
        <NButton @click="visible = false">{{ $t('common.close') }}</NButton>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>
