<script setup lang="ts">
import { ref, watch } from 'vue';
import { fetchGetExecutionRecordDetail, fetchGetPerformanceActions, fetchGetPerformanceMusic } from '@/service/api';

defineOptions({ name: 'TaskDetailDrawer' });

interface Props {
  execId: number | null;
}

const props = defineProps<Props>();

const visible = defineModel<boolean>('visible', { default: false });

const loading = ref(false);
const detail = ref<Api.Task.TaskExecutionRecordDetail | null>(null);
const performanceActionLabels = ref<Record<string, string>>({});
const performanceMusicLabels = ref<Record<string, string>>({});

const taskTypeLabel: Record<string, string> = {
  patrol: '巡逻',
  broadcast: '播报',
  instant: '即时',
  performance: '表演'
};

const statusLabelMap: Record<string, string> = {
  pending: '等待中',
  running: '执行中',
  paused: '已暂停',
  completed: '已完成',
  failed: '已失败',
  cancelled: '已取消'
};

const sourceLabelMap: Record<string, string> = {
  platform_schedule: '平台定时',
  voice_trigger: '语音触发',
  manual: '手动',
  text_input: '语音输入',
  resume: '手动恢复'
};

const actionLabel: Record<string, string> = {
  shake_hand: '握手',
  high_five: '击掌',
  hug: '拥抱',
  high_wave: '高举挥手',
  clap: '鼓掌',
  face_wave: '挥手',
  left_kiss: '左手飞吻',
  hands_up: '平举双手',
  x_ray: '动感光波',
  right_hand_up: '平举右手',
  reject: '拒绝',
  right_kiss: '右手飞吻',
  two_hand_kiss: '双手飞吻',
  no: '无动作',
  // 兼容历史快照数据
  shake_hands: '握手',
  wave: '挥手',
  left_hand: '伸左手',
  right_hand: '伸右手',
  bend_no_hands: '弯腰',
  bend_with_hands: '弯腰和伸手',
  bow: '鞠躬',
  turn: '转身',
  wait: '停留等待',
  nod: '点头'
};

async function loadDetail() {
  if (!props.execId) return;
  loading.value = true;
  try {
    const { data, error } = await fetchGetExecutionRecordDetail(props.execId);
    if (!error && data) {
      detail.value = data;
      if (data.task_definition?.task_type === 'performance') {
        const [actionResult, musicResult] = await Promise.all([
          fetchGetPerformanceActions(),
          fetchGetPerformanceMusic()
        ]);
        performanceActionLabels.value =
          !actionResult.error && actionResult.data
            ? Object.fromEntries(actionResult.data.map(option => [option.value, option.label]))
            : {};
        performanceMusicLabels.value =
          !musicResult.error && musicResult.data
            ? Object.fromEntries(musicResult.data.map(option => [option.value, option.label]))
            : {};
      }
    }
  } finally {
    loading.value = false;
  }
}

watch(visible, () => {
  if (visible.value && props.execId) {
    loadDetail();
  }
});

function pointStatusType(index: number): 'success' | 'default' | 'error' {
  if (!detail.value?.progress) return 'default';
  const statusItem = detail.value.progress.points_status.find(p => p.index === index);
  if (!statusItem) return 'default';
  if (statusItem.status === 'completed') return 'success';
  if (statusItem.status === 'failed') return 'error';
  return 'default';
}

/** 间隔仅非最后一步展示（最后一步无后续间隔，历史快照中可能残留数值） */
function showStepInterval(step: { interval: number | null | undefined }, index: number, total: number): boolean {
  return index < total - 1 && step.interval !== null && step.interval !== undefined;
}
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="560">
    <NDrawerContent title="执行详情" :native-scrollbar="false" closable>
      <NSpin v-if="loading" class="w-full" />
      <template v-else-if="detail">
        <NDescriptions bordered :column="2" label-placement="left" size="small">
          <NDescriptionsItem label="执行ID">{{ detail.id }}</NDescriptionsItem>
          <NDescriptionsItem label="任务名称">
            {{ detail.task_definition?.task_name || '-' }}
          </NDescriptionsItem>
          <NDescriptionsItem label="任务类型">
            {{ taskTypeLabel[detail.task_definition?.task_type || ''] || detail.task_definition?.task_type || '-' }}
          </NDescriptionsItem>
          <NDescriptionsItem label="执行状态">
            <NTag
              size="small"
              :type="detail.status === 'completed' ? 'success' : detail.status === 'failed' ? 'error' : 'default'"
            >
              {{ statusLabelMap[detail.status] || detail.status }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem label="执行机器人">{{ detail.robot_name || '-' }}</NDescriptionsItem>
          <NDescriptionsItem label="场景地图">{{ detail.scene_name || '-' }}</NDescriptionsItem>
          <NDescriptionsItem label="触发源">
            {{ sourceLabelMap[detail.source] || detail.source }}
          </NDescriptionsItem>
          <NDescriptionsItem label="触发用户">{{ detail.user_name || '-' }}</NDescriptionsItem>
          <NDescriptionsItem label="开始时间">{{ detail.start_time || '-' }}</NDescriptionsItem>
          <NDescriptionsItem label="结束时间">{{ detail.finish_time || '-' }}</NDescriptionsItem>
          <NDescriptionsItem label="进度" :span="2">
            <NProgress type="line" :percentage="detail.progress_per" />
          </NDescriptionsItem>
          <NDescriptionsItem v-if="detail.error_msg" label="错误信息" :span="2">
            <NText type="error">{{ detail.error_msg }}</NText>
          </NDescriptionsItem>
        </NDescriptions>

        <!-- 巡逻点位时间线 -->
        <template v-if="detail.task_definition?.task_type === 'patrol' && detail.task_definition?.points?.length">
          <NDivider title-placement="left">巡逻点位</NDivider>
          <NTimeline>
            <NTimelineItem
              v-for="(point, index) in detail.task_definition.points"
              :key="index"
              :type="pointStatusType(index)"
              :title="`点位 ${index + 1}: ${point.point_name || '-'}`"
            >
              <template v-if="point.actions && point.actions.length > 0">
                <div v-for="(actionItem, actionIdx) in point.actions" :key="actionIdx" class="mb-4px">
                  <NText depth="3">
                    动作{{ point.actions.length > 1 ? ` ${actionIdx + 1}` : '' }}:
                    {{ actionLabel[actionItem.action] || actionItem.action }}
                  </NText>
                  <br v-if="actionItem.voice_text" />
                  <NText v-if="actionItem.voice_text" depth="3">语音: {{ actionItem.voice_text }}</NText>
                </div>
              </template>
            </NTimelineItem>
          </NTimeline>
        </template>

        <!-- 播报步骤 -->
        <template v-if="detail.task_definition?.broadcast_steps?.length || detail.task_definition?.broadcast_text">
          <NDivider title-placement="left">播报内容</NDivider>
          <NTimeline v-if="detail.task_definition?.broadcast_steps?.length">
            <NTimelineItem
              v-for="(step, index) in detail.task_definition.broadcast_steps"
              :key="index"
              :title="`步骤 ${index + 1}`"
            >
              <NText v-if="step.content" depth="3">内容: {{ step.content }}</NText>
              <template v-if="step.actions && step.actions.length > 0">
                <br v-if="step.content" />
                <NText depth="3">动作: {{ step.actions.map(a => actionLabel[a] || a).join('、') }}</NText>
              </template>
              <template v-if="showStepInterval(step, index, detail.task_definition?.broadcast_steps?.length ?? 0)">
                <br v-if="step.content || (step.actions && step.actions.length > 0)" />
                <NText depth="3">间隔: {{ step.interval }} 秒</NText>
              </template>
            </NTimelineItem>
          </NTimeline>
          <NText v-else depth="3">{{ detail.task_definition?.broadcast_text }}</NText>
        </template>

        <!-- 表演步骤 -->
        <template
          v-if="
            detail.task_definition?.task_type === 'performance' && detail.task_definition?.performance_steps?.length
          "
        >
          <NDivider title-placement="left">表演内容</NDivider>
          <NTimeline>
            <NTimelineItem
              v-for="(step, index) in detail.task_definition.performance_steps"
              :key="index"
              :title="`第 ${index + 1} 套`"
            >
              <NText depth="3">表演动作: {{ performanceActionLabels[step.action] || step.action }}</NText>
              <br />
              <NText depth="3">
                背景音乐: {{ step.music ? performanceMusicLabels[step.music] || step.music : '无' }}
              </NText>
              <br />
              <NText depth="3">播放次数: {{ step.play_count }} 次</NText>
              <template v-if="showStepInterval(step, index, detail.task_definition?.performance_steps?.length ?? 0)">
                <br />
                <NText depth="3">与下一套间隔: {{ step.interval }} 秒</NText>
              </template>
            </NTimelineItem>
          </NTimeline>
        </template>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped></style>
