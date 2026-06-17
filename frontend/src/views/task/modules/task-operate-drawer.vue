<script setup lang="ts">
import { computed, h, onMounted, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { NText, NTooltip } from 'naive-ui';
import { useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchCreateTask, fetchUpdateTask, fetchGetTask, fetchGetRobotList, fetchGetMapAnnotations, fetchGetSceneMapList } from '@/service/api';

defineOptions({ name: 'TaskOperateDrawer' });

interface Props {
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.Task.Task | null;
}

const props = defineProps<Props>();

interface Emits {
  (e: 'submitted'): void;
}

const emit = defineEmits<Emits>();

const visible = defineModel<boolean>('visible', { default: false });
const { formRef, validate, restoreValidation } = useNaiveForm();

const title = computed(() => (props.operateType === 'add' ? '创建任务' : '编辑任务'));

/** 任务类型选项 */
const taskTypeOptions = [
  { label: '巡逻', value: 'patrol' },
  { label: '播报', value: 'broadcast' }
];

/** 运控动作选项 */
const actionOptions = [
  { label: '挥手', value: 'wave' },
  { label: '鞠躬', value: 'bow' },
  { label: '转身', value: 'turn' },
  { label: '停留等待', value: 'wait' },
  { label: '点头', value: 'nod' }
];

/** 播报次数选项 */
const broadcastCountOptions = [
  { label: '1 次', value: '1' },
  { label: '2 次', value: '2' },
  { label: '3 次', value: '3' },
  { label: '5 次', value: '5' },
  { label: '循环播报', value: 'loop' }
];

/** 重复周期选项（星期复选框） */
const weekdayOptions = [
  { label: '周一', value: 'mon' },
  { label: '周二', value: 'tue' },
  { label: '周三', value: 'wed' },
  { label: '周四', value: 'thu' },
  { label: '周五', value: 'fri' },
  { label: '周六', value: 'sat' },
  { label: '周日', value: 'sun' }
];

const mapOptions = ref<{ label: string; value: number }[]>([]);

async function loadMapOptions() {
  const { data, error } = await fetchGetSceneMapList({ page: 1, page_size: 999, name: null, group_id: undefined, status: null });
  if (!error && data) {
    mapOptions.value = (data.records || []).map(map => ({ label: map.name, value: map.id }));
  }
}

/** 机器人选项 */
interface RobotOption {
  label: string;
  value: number;
  status: string;
  map_id: number | null;
  map_name: string | null;
  disabled?: boolean;
}
const robotOptions = ref<RobotOption[]>([]);

async function loadRobotOptions() {
  const { data, error } = await fetchGetRobotList({ page: 1, page_size: 200 });
  if (!error && data) {
    robotOptions.value = (data.records || []).map(r => ({
      label: r.name + (r.status === 'online' ? ' (在线)' : r.status === 'offline' ? ' (离线)' : ' (未激活)'),
      value: r.id,
      status: r.status || 'inactive',
      map_id: r.map_id ?? null,
      map_name: r.map_name ?? null
    }));
  }
}

/** 场景点位（annotation）选项 */
interface AnnotationOption {
  label: string;
  value: number;
}
const annotationOptions = ref<AnnotationOption[]>([]);
const annotationMap = ref<Map<number, Api.Scene.SceneMapAnnotation>>(new Map());

async function loadAnnotations(mapId: number | null) {
  if (mapId === null) {
    annotationOptions.value = [];
    annotationMap.value = new Map();
    return;
  }
  const { data, error } = await fetchGetMapAnnotations(mapId);
  if (!error && data) {
    const list: Api.Scene.SceneMapAnnotation[] = Array.isArray(data) ? data : (data?.records ?? []);
    annotationMap.value = new Map(list.map(a => [a.id, a]));
    annotationOptions.value = list.map(a => ({
      label: `${a.name} (${a.x}, ${a.y})`,
      value: a.id
    }));
  } else {
    annotationOptions.value = [];
    annotationMap.value = new Map();
  }
}

/** 巡逻任务机器人约束 */
const isPatrol = computed(() => model.value.task_type === 'patrol');

const selectedMapId = computed<number | null>(() => model.value.map_id);

const filteredRobotOptions = computed(() => robotOptions.value);

function renderRobotLabel(option: RobotOption) {
  if (option.disabled && isPatrol.value) {
    const tip = option.map_id === null ? '需要分配场景' : '该机器人与已选机器人不在同一场景';
    return h(
      NTooltip,
      { placement: 'right' },
      {
        trigger: () =>
          h(NText, { depth: 3, style: 'text-decoration: line-through' }, { default: () => option.label }),
        default: () => tip
      }
    );
  }
  return option.label;
}

/** 表单模型 */
interface PointItem {
  sort_order: number;
  point_name: string | null;
  annotation_id: number | null;
  action: Api.Task.TaskAction;
  voice_text: string | null;
}

interface FormModel {
  name: string;
  task_type: Api.Task.TaskType;
  map_id: number | null;
  points: PointItem[];
  broadcast_text: string | null;
  broadcast_count: string | null;
  robot_ids: number[];
  schedule_enabled: boolean;
  schedule_date: number | null;
  schedule_start_time: number | null;
  schedule_repeat_cycles: string[];
}

function createDefaultModel(): FormModel {
  return {
    name: '',
    task_type: 'patrol',
    map_id: null,
    points: [],
    broadcast_text: null,
    broadcast_count: '1',
    robot_ids: [],
    schedule_enabled: false,
    schedule_date: null,
    schedule_start_time: null,
    schedule_repeat_cycles: []
  };
}

const model = ref<FormModel>(createDefaultModel());

/** 点位管理 */
function addPoint() {
  model.value.points.push({
    sort_order: model.value.points.length,
    point_name: null,
    annotation_id: null,
    action: 'wave',
    voice_text: null
  });
}

function removePoint(index: number) {
  model.value.points.splice(index, 1);
  model.value.points.forEach((p, i) => {
    p.sort_order = i;
  });
}

/** 校验规则 */
const rules = computed(() => ({
  name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    { min: 2, max: 20, message: '任务名称为 2-20 字', trigger: 'blur' }
  ],
  task_type: { required: true, message: '请选择任务类型', trigger: 'change' },
  map_id: { required: true, type: 'number' as const, message: '请选择场景地图', trigger: 'change' },
  robot_ids: {
    required: true,
    type: 'array' as const,
    min: 1,
    message: '至少选择一台机器人',
    trigger: 'change'
  }
}));

const taskId = computed(() => props.rowData?.id || -1);
const isEdit = computed(() => props.operateType === 'edit');

async function handleInitModel() {
  model.value = createDefaultModel();
  annotationOptions.value = [];
  annotationMap.value = new Map();

  if (props.operateType === 'edit' && props.rowData) {
    const cloned = jsonClone(props.rowData) as Api.Task.Task;
    model.value.name = cloned.name || '';
    model.value.task_type = cloned.task_type || 'patrol';
    model.value.broadcast_text = cloned.broadcast_text || null;
    model.value.broadcast_count = cloned.broadcast_count || '1';
    model.value.schedule_enabled = cloned.schedule_enabled || false;
    model.value.schedule_repeat_cycles = cloned.schedule_repeat_cycle
      ? cloned.schedule_repeat_cycle.split(',').filter(v => v && v !== 'none')
      : [];
    model.value.map_id = cloned.robots?.find(r => r.map_id)?.map_id ?? null;
    model.value.robot_ids = cloned.robots?.map(r => r.id) || [];

    if (model.value.map_id !== null) {
      await loadAnnotations(model.value.map_id);
    }

    if (cloned.points && cloned.points.length > 0) {
      model.value.points = cloned.points.map((p, i) => ({
        sort_order: i,
        point_name: p.point_name || null,
        annotation_id: p.annotation_id ?? null,
        action: p.action || 'wave',
        voice_text: p.voice_text || null
      }));
    }

    if (cloned.id) {
      const { data: detail } = await fetchGetTask(cloned.id);
      if (detail) {
        model.value.map_id = detail.robots?.find(r => r.map_id)?.map_id ?? model.value.map_id;
        model.value.robot_ids = detail.robots?.map(r => r.id) || [];
        if (model.value.map_id !== null) {
          await loadAnnotations(model.value.map_id);
        }
        if (detail.points && detail.points.length > 0) {
          model.value.points = detail.points.map((p, i) => ({
            sort_order: i,
            point_name: p.point_name || null,
            annotation_id: p.annotation_id ?? null,
            action: p.action || 'wave',
            voice_text: p.voice_text || null
          }));
        }
      }
    }
  }
}

function handleMapChange(mapId: number | null) {
  model.value.map_id = mapId;
  model.value.robot_ids = [];
  model.value.points = [];
}

function closeDrawer() {
  visible.value = false;
}

async function handleSubmit() {
  await validate();

  // Custom validations
  if (model.value.map_id === null) {
    window.$message?.warning('请选择场景地图');
    return;
  }
  if (model.value.task_type === 'patrol' && model.value.points.length === 0) {
    window.$message?.warning('巡逻任务至少添加一个巡逻点位');
    return;
  }
  if (model.value.task_type === 'patrol') {
    const invalidPointIndex = model.value.points.findIndex(point => point.annotation_id === null);
    if (invalidPointIndex !== -1) {
      window.$message?.warning(`请选择点位 ${invalidPointIndex + 1} 的巡逻点位`);
      return;
    }
    const invalidActionIndex = model.value.points.findIndex(point => !point.action);
    if (invalidActionIndex !== -1) {
      window.$message?.warning(`请选择点位 ${invalidActionIndex + 1} 的运控动作`);
      return;
    }
  }
  if (model.value.task_type === 'broadcast' && !model.value.broadcast_text) {
    window.$message?.warning('请填写播报文本');
    return;
  }
  if (model.value.schedule_enabled) {
    if (model.value.schedule_date === null) {
      window.$message?.warning('请选择调度日期');
      return;
    }
    if (model.value.schedule_start_time === null) {
      window.$message?.warning('请选择开始时间');
      return;
    }
  }
  const submitData: Api.Task.TaskCreate = {
    name: model.value.name,
    task_type: model.value.task_type,
    robot_ids: model.value.robot_ids,
    schedule_enabled: model.value.schedule_enabled,
    schedule_repeat_cycle: model.value.schedule_repeat_cycles.length > 0
      ? model.value.schedule_repeat_cycles.join(',')
      : null,
    points: model.value.task_type === 'patrol' ? model.value.points : undefined,
    broadcast_text: model.value.task_type === 'broadcast' ? model.value.broadcast_text : undefined,
    broadcast_count: model.value.task_type === 'broadcast' ? model.value.broadcast_count : undefined
  };

  let error: unknown = null;
  if (isEdit.value) {
    const result = await fetchUpdateTask(taskId.value, submitData);
    error = result.error;
  } else {
    const result = await fetchCreateTask(submitData);
    error = result.error;
  }

  if (!error) {
    window.$message?.success(isEdit.value ? $t('common.updateSuccess') : $t('common.addSuccess'));
    closeDrawer();
    emit('submitted');
  }
}

watch(visible, () => {
  if (visible.value) {
    handleInitModel();
    restoreValidation();
  }
});

watch(selectedMapId, newMapId => {
  loadAnnotations(newMapId);
});

onMounted(() => {
  loadMapOptions();
  loadRobotOptions();
});
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="640">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="model" :rules="rules" label-placement="top">
        <!-- 基础信息 -->
        <NGrid :cols="2" :x-gap="16">
          <NFormItemGi :span="2" label="任务名称" path="name">
            <NInput v-model:value="model.name" placeholder="请输入任务名称（2-20字）" :maxlength="20" show-count />
          </NFormItemGi>
          <NFormItemGi :span="2" label="任务类型" path="task_type">
            <NRadioGroup v-model:value="model.task_type">
              <NRadioButton v-for="opt in taskTypeOptions" :key="opt.value" :value="opt.value" :label="opt.label" />
            </NRadioGroup>
          </NFormItemGi>
        </NGrid>

        <NDivider title-placement="left">场景地图</NDivider>
        <NFormItem label="场景地图" path="map_id">
          <NSelect
            :value="model.map_id"
            :options="mapOptions"
            placeholder="请先选择场景地图"
            filterable
            clearable
            @update:value="handleMapChange"
          />
        </NFormItem>

        <!-- 机器人绑定 -->
        <NDivider title-placement="left">执行机器人</NDivider>
        <NFormItem label="绑定机器人" path="robot_ids">
          <NSelect
            v-model:value="model.robot_ids"
            :options="filteredRobotOptions"
            :placeholder="model.map_id === null ? '请先选择场景地图' : '至少选择一台机器人'"
            multiple
            filterable
            :disabled="model.map_id === null"
            :render-label="renderRobotLabel"
          />
        </NFormItem>

        <!-- 巡逻点位配置 -->
        <template v-if="model.task_type === 'patrol'">
          <NDivider title-placement="left">巡逻点位配置</NDivider>
          <div v-if="selectedMapId === null" class="mb-12px text-13px" style="color: var(--n-text-color-3, #999);">
            请先选择场景地图，才能选择巡逻点位
          </div>
          <div v-for="(point, index) in model.points" :key="index" class="mb-12px">
            <NCard size="small" embedded>
              <template #header>
                <NSpace align="center">
                  <span>点位 {{ index + 1 }}</span>
                  <NButton type="error" ghost size="tiny" @click="removePoint(index)">移除</NButton>
                </NSpace>
              </template>
              <NGrid :cols="3" :x-gap="12">
                <NFormItemGi label="巡逻点位" required>
                  <NSelect
                    v-model:value="point.annotation_id"
                    :options="annotationOptions"
                    :placeholder="selectedMapId === null ? '请先选择场景地图' : '请选择场景点位'"
                    :disabled="selectedMapId === null"
                    filterable
                    @update:value="(val: number | null) => {
                      const ann = val === null ? undefined : annotationMap.get(val);
                      point.point_name = ann?.name ?? null;
                    }"
                  />
                </NFormItemGi>
                <NFormItemGi label="运控动作" required>
                  <NSelect v-model:value="point.action" :options="actionOptions" placeholder="选择动作" />
                </NFormItemGi>
                <NFormItemGi label="语音文本">
                  <NInput v-model:value="point.voice_text" placeholder="语音播报文本" />
                </NFormItemGi>
              </NGrid>
            </NCard>
          </div>
          <NButton dashed block :disabled="selectedMapId === null" @click="addPoint">
            <template #icon>
              <icon-ic-round-plus class="text-icon" />
            </template>
            添加点位
          </NButton>
        </template>

        <!-- 播报配置 -->
        <template v-if="model.task_type === 'broadcast'">
          <NDivider title-placement="left">播报配置</NDivider>
          <NFormItem label="播报文本">
            <NInput v-model:value="model.broadcast_text" type="textarea" placeholder="请输入播报文本" :rows="3" />
          </NFormItem>
          <NFormItem label="播报次数">
            <NSelect v-model:value="model.broadcast_count" :options="broadcastCountOptions" placeholder="选择播报次数" />
          </NFormItem>
        </template>

        <!-- 定时配置 -->
        <NDivider title-placement="left">定时配置（可选）</NDivider>
        <NFormItem label="启用定时执行">
          <NSwitch v-model:value="model.schedule_enabled" />
        </NFormItem>
        <template v-if="model.schedule_enabled">
          <NGrid :cols="2" :x-gap="16">
            <NFormItemGi label="调度日期" required>
              <NDatePicker v-model:value="model.schedule_date" type="date" class="w-full" />
            </NFormItemGi>
            <NFormItemGi label="开始时间" required>
              <NTimePicker v-model:value="model.schedule_start_time" format="HH:mm" class="w-full" />
            </NFormItemGi>
          </NGrid>
          <NFormItem label="重复周期（未选择则不重复）">
            <NCheckboxGroup v-model:value="model.schedule_repeat_cycles">
              <NSpace>
                <NCheckbox v-for="opt in weekdayOptions" :key="opt.value" :value="opt.value" :label="opt.label" />
              </NSpace>
            </NCheckboxGroup>
          </NFormItem>
        </template>
      </NForm>

      <template #footer>
        <NSpace :size="16">
          <NButton @click="closeDrawer">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped></style>
