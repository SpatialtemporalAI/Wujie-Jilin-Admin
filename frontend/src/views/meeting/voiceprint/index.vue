<script setup lang="tsx">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import { NButton, NCard, NDataTable, NPopconfirm, NTag, useMessage } from 'naive-ui';
import type { FlatResponseData } from '@sa/axios';
import {
  fetchDeleteVoiceprint,
  fetchGetVoiceprintList,
  fetchGetVoiceprintOverview,
  fetchGetVoiceprintRobots,
  fetchRegisterVoiceprint,
  fetchUpdateMeetingMode
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';

defineOptions({
  name: 'MeetingVoiceprint'
});

const message = useMessage();
const appStore = useAppStore();
const { hasAuth } = useAuth();

const ROLE_TYPES = ['主持人', '发言人', '记录员', '旁听'];
const STATUS_OPTIONS = [
  { label: '注册成功', value: 'success' },
  { label: '处理中', value: 'processing' },
  { label: '注册失败', value: 'failed' }
];

/** ==================== 机器人 & 会议模式状态 ==================== */

const robots = ref<Api.Meeting.VoiceprintRobot[]>([]);
const robotsLoading = ref(false);
const selectedRobotId = ref<number | null>(null);
const overview = ref<Api.Meeting.VoiceprintOverview>({ meeting_mode: false, registered_count: 0 });
const overviewLoading = ref(false);
const meetingModeSaving = ref(false);

const robotOptions = computed(() =>
  robots.value.map(item => ({ label: `${item.name}（${item.serial_number}）`, value: item.id }))
);

const selectedRobot = computed(() => robots.value.find(item => item.id === selectedRobotId.value) || null);

/** ==================== 声纹注册状态 ==================== */

const roleName = ref('');
const roleType = ref('发言人');
const transcriptHint = ref('');

const currentStep = ref<0 | 1 | 2 | 3>(0);
const recording = ref(false);
const recordSeconds = ref(0);
const audioBlob = ref<Blob | null>(null);
const audioUrl = ref('');
const submitting = ref(false);

let mediaRecorder: MediaRecorder | null = null;
let mediaStream: MediaStream | null = null;
let recordTimer: ReturnType<typeof setInterval> | null = null;

const roleTypeOptions = ROLE_TYPES.map(item => ({ label: item, value: item }));

const canStartRecord = computed(() => selectedRobotId.value !== null && roleName.value.trim().length > 0);

/** ==================== 注册记录表格 ==================== */

const searchParams: Api.Meeting.VoiceprintSearchParams = reactive({
  page: 1,
  page_size: 10,
  robot_id: null,
  status: null,
  keyword: null
});

function getStatusText(status: string) {
  const map: Record<string, string> = { success: '注册成功', processing: '处理中', failed: '注册失败' };
  return map[status] || status;
}

function getStatusType(status: string): NaiveUI.ThemeColor {
  const map: Record<string, NaiveUI.ThemeColor> = { success: 'success', processing: 'warning', failed: 'error' };
  return map[status] || 'default';
}

const {
  columns: voiceprintColumns,
  columnChecks: voiceprintColumnChecks,
  data: voiceprintData,
  getData: getVoiceprintData,
  getDataByPage: getVoiceprintDataByPage,
  loading: voiceprintLoading,
  mobilePagination: voiceprintMobilePagination
} = useNaivePaginatedTable<FlatResponseData<any, Api.Meeting.VoiceprintList>, Api.Meeting.VoiceprintRecord>({
  api: () => fetchGetVoiceprintList(searchParams),
  transform: defaultTransform,
  onPaginationParamsChange: params => {
    searchParams.page = params.page;
    searchParams.page_size = params.pageSize;
  },
  columns: () => [
    {
      key: 'role_name',
      title: '发言人',
      align: 'center',
      width: 120,
      ellipsis: { tooltip: true }
    },
    {
      key: 'role_type',
      title: '角色',
      align: 'center',
      width: 90
    },
    {
      key: 'robot_name',
      title: '机器人',
      align: 'center',
      width: 140,
      ellipsis: { tooltip: true }
    },
    {
      key: 'status',
      title: $t('common.status'),
      align: 'center',
      width: 100,
      render: row => (
        <NTag type={getStatusType(row.status)} size="small">
          {getStatusText(row.status)}
        </NTag>
      )
    },
    {
      key: 'score',
      title: '清晰度分',
      align: 'center',
      width: 90,
      render: row => row.score ?? '-'
    },
    {
      key: 'match_score',
      title: '匹配度',
      align: 'center',
      width: 90,
      render: row => row.match_score ?? '-'
    },
    {
      key: 'noise_level',
      title: '噪声等级',
      align: 'center',
      width: 100,
      render: row => row.noise_level || '-'
    },
    {
      key: 'sample_url',
      title: '录音',
      align: 'center',
      width: 200,
      render: row =>
        row.sample_url ? <audio controls preload="none" src={row.sample_url} class="h-28px w-full" /> : '-'
    },
    {
      key: 'created_at',
      title: '注册时间',
      align: 'center',
      width: 170
    },
    {
      key: 'error_msg',
      title: '失败原因',
      align: 'center',
      minWidth: 160,
      ellipsis: { tooltip: true },
      render: row => row.error_msg || '-'
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 90,
      fixed: 'right',
      render: row => {
        if (!hasAuth('meeting:voiceprint:delete')) return null;
        return (
          <NPopconfirm onPositiveClick={() => handleDelete(row.id)}>
            {{
              default: () => $t('common.confirmDelete'),
              trigger: () => (
                <NButton type="error" ghost size="small">
                  {$t('common.delete')}
                </NButton>
              )
            }}
          </NPopconfirm>
        );
      }
    }
  ]
});

/** ==================== 机器人 & 会议模式操作 ==================== */

function getRobotStatusText(status: string) {
  const map: Record<string, string> = { online: '在线', offline: '离线', inactive: '未激活' };
  return map[status] || status || '未知';
}

function getRobotStatusType(status: string): NaiveUI.ThemeColor {
  const map: Record<string, NaiveUI.ThemeColor> = { online: 'success', offline: 'default', inactive: 'warning' };
  return map[status] || 'default';
}

async function loadRobots() {
  robotsLoading.value = true;
  try {
    const { data, error } = await fetchGetVoiceprintRobots();
    if (error) return;
    robots.value = data || [];
    if (robots.value.length && selectedRobotId.value === null) {
      selectedRobotId.value = robots.value[0].id;
      searchParams.robot_id = robots.value[0].id;
      await loadOverview();
      getVoiceprintDataByPage(1);
    }
  } finally {
    robotsLoading.value = false;
  }
}

async function loadOverview() {
  if (selectedRobotId.value === null) return;
  overviewLoading.value = true;
  try {
    const { data, error } = await fetchGetVoiceprintOverview(selectedRobotId.value);
    if (!error && data) overview.value = data;
  } finally {
    overviewLoading.value = false;
  }
}

async function handleRobotChange(value: number | null) {
  selectedRobotId.value = value;
  searchParams.robot_id = value;
  resetRecording();
  await loadOverview();
  getVoiceprintDataByPage(1);
}

async function handleToggleMeetingMode(enabled: boolean) {
  if (selectedRobotId.value === null) {
    message.warning('请先选择机器人');
    return;
  }
  if (enabled && overview.value.registered_count === 0) {
    message.warning('请先注册至少一位发言人声纹，再开启会议模式');
    return;
  }
  meetingModeSaving.value = true;
  try {
    const { data, error } = await fetchUpdateMeetingMode({ robot_id: selectedRobotId.value, enabled });
    if (error || !data) {
      message.error('切换会议模式失败');
      return;
    }
    overview.value = data;
    const robot = robots.value.find(item => item.id === selectedRobotId.value);
    if (robot) robot.meeting_mode = data.meeting_mode;
    message.success(data.meeting_mode ? '已进入会议模式' : '已退出会议模式');
  } finally {
    meetingModeSaving.value = false;
  }
}

/** ==================== 录音与注册 ==================== */

function clearTimer() {
  if (recordTimer) {
    clearInterval(recordTimer);
    recordTimer = null;
  }
}

function releaseStream() {
  mediaStream?.getTracks().forEach(track => track.stop());
  mediaStream = null;
}

async function startRecording() {
  if (!canStartRecord.value) {
    message.warning('请先选择机器人并填写发言人姓名');
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
    message.error('当前浏览器不支持麦克风录音，请更换 Chrome / Edge 浏览器');
    return;
  }

  resetRecording();

  let stream: MediaStream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    message.error('无法访问麦克风，请检查浏览器权限设置');
    return;
  }
  mediaStream = stream;

  const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus' : 'audio/webm';
  const chunks: Blob[] = [];
  mediaRecorder = new MediaRecorder(stream, { mimeType });

  mediaRecorder.ondataavailable = event => {
    if (event.data.size > 0) chunks.push(event.data);
  };

  mediaRecorder.onstop = () => {
    const blob = new Blob(chunks, { type: 'audio/webm' });
    audioBlob.value = blob;
    audioUrl.value = URL.createObjectURL(blob);
    recording.value = false;
    currentStep.value = 2;
    clearTimer();
    releaseStream();
  };

  mediaRecorder.start(200);
  recording.value = true;
  currentStep.value = 1;
  recordSeconds.value = 0;
  recordTimer = setInterval(() => {
    recordSeconds.value += 1;
    if (recordSeconds.value >= 60) stopRecording();
  }, 1000);
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
}

function resetRecording() {
  clearTimer();
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  mediaRecorder = null;
  releaseStream();
  recording.value = false;
  recordSeconds.value = 0;
  audioBlob.value = null;
  if (audioUrl.value) URL.revokeObjectURL(audioUrl.value);
  audioUrl.value = '';
  currentStep.value = 0;
}

function handleReRecord() {
  resetRecording();
  startRecording();
}

async function handleSubmit() {
  if (selectedRobotId.value === null) {
    message.warning('请先选择机器人');
    return;
  }
  if (!roleName.value.trim()) {
    message.warning('请填写发言人姓名');
    return;
  }
  if (!audioBlob.value) {
    message.warning('请先录制一段声纹');
    return;
  }

  submitting.value = true;
  try {
    const file = new File([audioBlob.value], `${roleName.value.trim()}.webm`, { type: 'audio/webm' });
    const { data: record, error } = await fetchRegisterVoiceprint({
      robot_id: selectedRobotId.value,
      role_name: roleName.value.trim(),
      role_type: roleType.value,
      method: 'record',
      transcript_hint: transcriptHint.value.trim(),
      audio: file
    });
    if (error || !record) {
      message.error('声纹注册失败，请稍后重试');
      return;
    }
    if (record.status === 'success') {
      message.success('声纹注册成功');
    } else {
      message.error(record.error_msg || '声纹注册失败');
    }
    resetRecording();
    roleName.value = '';
    transcriptHint.value = '';
    await loadOverview();
    getVoiceprintData();
  } catch (error: any) {
    message.error(error?.message || '声纹注册失败');
  } finally {
    submitting.value = false;
  }
}

/** ==================== 删除注册记录 ==================== */

async function handleDelete(recordId: number) {
  const { error } = await fetchDeleteVoiceprint(recordId);
  if (error) return;
  message.success($t('common.deleteSuccess'));
  await loadOverview();
  getVoiceprintData();
}

onMounted(async () => {
  await loadRobots();
});

onBeforeUnmount(() => {
  clearTimer();
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  releaseStream();
  if (audioUrl.value) URL.revokeObjectURL(audioUrl.value);
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <NAlert type="info" :bordered="false">
      开启会议模式前，需为每位发言人录入声纹并注册角色，用于会中区分发言人身份。
    </NAlert>

    <NGrid :cols="24" :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
      <NGridItem span="24 s:24 m:14">
        <NCard :bordered="false" size="small" class="h-full card-wrapper">
          <template #header>
            <div class="flex-y-center gap-8px">
              <SvgIcon icon="mdi:account-voice" class="text-18px text-primary" />
              <span>声纹注册</span>
            </div>
          </template>

          <NSteps :current="currentStep" size="small" class="mb-20px">
            <NStep title="选择机器人与角色" />
            <NStep title="录制声纹" />
            <NStep title="试听确认" />
            <NStep title="提交注册" />
          </NSteps>

          <NForm label-placement="top" :show-feedback="false">
            <NGrid :cols="24" :x-gap="16" :y-gap="16" item-responsive>
              <NGridItem span="24 m:12">
                <NFormItem label="目标机器人">
                  <NSelect
                    v-model:value="selectedRobotId"
                    :options="robotOptions"
                    :loading="robotsLoading"
                    placeholder="请选择机器人"
                    filterable
                    @update:value="handleRobotChange"
                  />
                </NFormItem>
              </NGridItem>
              <NGridItem span="24 m:12">
                <NFormItem label="发言人姓名">
                  <NInput v-model:value="roleName" placeholder="请输入发言人姓名" :maxlength="20" clearable />
                </NFormItem>
              </NGridItem>
              <NGridItem span="24 m:12">
                <NFormItem label="角色类型">
                  <NSelect v-model:value="roleType" :options="roleTypeOptions" />
                </NFormItem>
              </NGridItem>
              <NGridItem span="24 m:12">
                <NFormItem label="文本提示（可选）">
                  <NInput v-model:value="transcriptHint" placeholder="录音时说的内容，用于辅助建模" clearable />
                </NFormItem>
              </NGridItem>
            </NGrid>
          </NForm>

          <div class="mt-16px flex-col items-center gap-12px rounded-8px bg-#f7f9fc p-20px dark:bg-#1f1f1f">
            <div class="text-40px text-primary">
              <SvgIcon :icon="recording ? 'mdi:microphone' : 'mdi:microphone-outline'" />
            </div>
            <div class="text-14px text-gray-500">
              {{ recording ? `正在录音 ${recordSeconds}s / 60s` : '请用正常语速朗读一段 10~30 秒的内容' }}
            </div>
            <div class="flex-center flex-wrap gap-12px">
              <NButton v-if="!recording" type="primary" :disabled="!canStartRecord" @click="startRecording">
                {{ audioBlob ? '重新录制' : '开始录音' }}
              </NButton>
              <NButton v-else type="error" @click="stopRecording">停止录音</NButton>
              <NButton v-if="audioUrl" :disabled="submitting" @click="resetRecording">清除</NButton>
              <NButton
                v-if="audioBlob"
                type="primary"
                :loading="submitting"
                :disabled="!audioBlob"
                @click="handleSubmit"
              >
                提交注册
              </NButton>
            </div>
            <audio v-if="audioUrl" :src="audioUrl" controls class="max-w-420px w-full" />
            <NButton v-if="audioBlob" text type="primary" @click="handleReRecord">不满意？直接重录</NButton>
          </div>
        </NCard>
      </NGridItem>

      <NGridItem span="24 s:24 m:10">
        <NCard :bordered="false" size="small" class="h-full card-wrapper">
          <template #header>
            <div class="flex-y-center justify-between">
              <div class="flex-y-center gap-8px">
                <SvgIcon icon="mdi:video-account" class="text-18px text-primary" />
                <span>会议模式</span>
              </div>
              <NTag :type="overview.meeting_mode ? 'success' : 'default'" size="small" round>
                {{ overview.meeting_mode ? '监听中' : '未开启' }}
              </NTag>
            </div>
          </template>

          <div class="flex-col gap-16px">
            <div class="flex-y-center justify-between rounded-8px bg-#f7f9fc px-16px py-12px dark:bg-#1f1f1f">
              <div class="flex-col">
                <span class="text-13px text-gray-500">当前机器人</span>
                <span class="text-15px font-medium">{{ selectedRobot?.name || '未选择' }}</span>
                <span v-if="selectedRobot" class="text-12px text-gray-400">
                  {{ selectedRobot.serial_number }} · {{ selectedRobot.model_name || '未绑定型号' }}
                </span>
              </div>
              <NTag v-if="selectedRobot" :type="getRobotStatusType(selectedRobot.robot_status)" size="small">
                {{ getRobotStatusText(selectedRobot.robot_status) }}
              </NTag>
            </div>

            <div class="flex-y-center justify-between">
              <div class="flex-col">
                <span class="text-13px text-gray-500">已注册发言人</span>
                <span class="text-20px text-primary font-medium">
                  {{ overview.registered_count }}
                  <span class="text-13px text-gray-400">/ 8</span>
                </span>
              </div>
              <NSwitch
                :value="overview.meeting_mode"
                :loading="meetingModeSaving || overviewLoading"
                :disabled="!selectedRobotId || !hasAuth('meeting:voiceprint:meeting_mode')"
                @update:value="handleToggleMeetingMode"
              />
            </div>

            <NAlert :type="overview.registered_count > 0 ? 'success' : 'warning'" :bordered="false">
              {{
                overview.registered_count > 0
                  ? '声纹已就绪，开启会议模式后机器人将在会中自动区分发言人。'
                  : '至少注册 1 位发言人后即可开启会议模式。'
              }}
            </NAlert>
          </div>
        </NCard>
      </NGridItem>
    </NGrid>

    <div class="flex-y-center justify-between gap-12px">
      <div class="flex-y-center flex-wrap gap-12px">
        <NInput
          v-model:value="searchParams.keyword"
          placeholder="搜索发言人姓名"
          clearable
          :style="{ width: '180px' }"
          @update:value="getVoiceprintDataByPage(1)"
        />
        <NSelect
          v-model:value="searchParams.status"
          :options="STATUS_OPTIONS"
          placeholder="注册状态"
          clearable
          :style="{ width: '140px' }"
          @update:value="getVoiceprintDataByPage(1)"
        />
      </div>
      <TableHeaderOperation
        v-model:columns="voiceprintColumnChecks"
        :show-add="false"
        :show-delete="false"
        :loading="voiceprintLoading"
        @refresh="getVoiceprintData"
      />
    </div>

    <NCard :bordered="false" size="small" class="card-wrapper sm:flex-1-hidden">
      <NDataTable
        :columns="voiceprintColumns"
        :data="voiceprintData"
        size="small"
        :flex-height="!appStore.isMobile"
        :scroll-x="1360"
        :loading="voiceprintLoading"
        remote
        :row-key="row => row.id"
        :pagination="voiceprintMobilePagination"
        class="sm:h-full"
      />
    </NCard>
  </div>
</template>

<style scoped></style>
