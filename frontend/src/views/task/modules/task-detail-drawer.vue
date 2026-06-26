<script setup lang="ts">
import { ref, watch } from 'vue';
import { fetchGetExecutionRecordDetail } from '@/service/api';

defineOptions({ name: 'TaskDetailDrawer' });

interface Props {
  execId: number | null;
}

const props = defineProps<Props>();

const visible = defineModel<boolean>('visible', { default: false });

const loading = ref(false);
const detail = ref<Api.Task.TaskExecutionRecordDetail | null>(null);

const taskTypeLabel: Record<string, string> = {
  patrol: '巡逻',
  broadcast: '播报'
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
  manual: '手动'
};

const actionLabel: Record<string, string> = {
  shake_hands: '握手',
  wave: '挥手',
  left_hand: '伸左手',
  right_hand: '伸右手',
  bend_no_hands: '弯腰',
  bend_with_hands: '弯腰和伸手',
  no: '无动作',
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
            <NTag size="small" :type="detail.status === 'completed' ? 'success' : detail.status === 'failed' ? 'error' : 'default'">
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
                    动作{{ point.actions.length > 1 ? ` ${actionIdx + 1}` : '' }}: {{
                      actionLabel[actionItem.action] || actionItem.action
                    }}
                  </NText>
                  <br v-if="actionItem.voice_text" />
                  <NText v-if="actionItem.voice_text" depth="3">
                    语音: {{ actionItem.voice_text }}
                  </NText>
                </div>
              </template>
            </NTimelineItem>
          </NTimeline>
        </template>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped></style>
