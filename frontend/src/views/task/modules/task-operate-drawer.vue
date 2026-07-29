<script setup lang="ts">
import { computed, h, onMounted, ref, watch } from 'vue';
import { NText, NTooltip } from 'naive-ui';
import dayjs from 'dayjs';
import { jsonClone } from '@sa/utils';
import {
  fetchCreateTask,
  fetchGetAllRobots,
  fetchGetMapAnnotations,
  fetchGetSceneMapList,
  fetchGetTask,
  fetchUpdateTask
} from '@/service/api';
import { useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

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
  { label: '握手', value: 'shake_hand' },
  { label: '高举挥手', value: 'high_wave' },
  { label: '鼓掌', value: 'clap' },
  { label: '挥手', value: 'face_wave' },
  { label: '平举双手', value: 'hands_up' },
  { label: '平举右手', value: 'right_hand_up' },
  { label: '拒绝', value: 'reject' },
  { label: '无动作', value: 'no' }
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
let mapOptionsLoaded = false;

async function loadMapOptions(force = false) {
  if (!force && mapOptionsLoaded) return;
  const { data, error } = await fetchGetSceneMapList({
    page: 1,
    page_size: 999,
    name: null,
    group_id: undefined,
    status: null
  });
  if (error) {
    return;
  }
  if (data) {
    const list = (data.records || []).map(map => ({ label: map.name, value: map.id }));
    const currentId = model.value.map_id;
    if (currentId !== null && !list.some(opt => opt.value === currentId)) {
      const existing = mapOptions.value.find(opt => opt.value === currentId);
      list.unshift(existing || { label: `地图 #${currentId}`, value: currentId });
    }
    mapOptions.value = list;
    mapOptionsLoaded = true;
  }
}

/** 机器人选项 */
interface RobotOption {
  label: string;
  value: number;
  status: string;
  map_id: number | null;
  disabled?: boolean;
}
const robotOptions = ref<RobotOption[]>([]);

async function loadRobotOptions() {
  const { data, error } = await fetchGetAllRobots();
  if (!error && data) {
    robotOptions.value = (data || []).map(r => ({
      label: r.name + (r.status === 'online' ? ' (在线)' : r.status === 'offline' ? ' (离线)' : ' (未激活)'),
      value: r.id,
      status: r.status || 'inactive',
      map_id: r.map_id ?? null
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
        trigger: () => h(NText, { depth: 3, style: 'text-decoration: line-through' }, { default: () => option.label }),
        default: () => tip
      }
    );
  }
  return option.label;
}

/** 表单模型 */
interface ActionItem {
  action: Api.Task.TaskAction;
  voice_text: string | null;
}

interface PointItem {
  sort_order: number;
  point_name: string | null;
  annotation_id: number | null;
  actions: ActionItem[];
}

interface FormModel {
  name: string;
  task_type: Api.Task.TaskType;
  map_id: number | null;
  points: PointItem[];
  broadcast_text: string | null;
  robot_ids: number[];
  schedule_enabled: boolean;
  /** 调度日期（时间戳，ms），提交时转换为 yyyy-MM-dd */
  schedule_date: number | null;
  /** 调度开始时间（时间戳，ms），提交时转换为 HH:mm:ss */
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
    robot_ids: [],
    schedule_enabled: false,
    schedule_date: null,
    schedule_start_time: null,
    schedule_repeat_cycles: []
  };
}

const model = ref<FormModel>(createDefaultModel());

/** 机器人单选绑定（API 仍为 robot_ids 数组，但当前限制仅 1 个） */
const robotId = computed({
  get: () => model.value.robot_ids[0] ?? null,
  set: (val: number | null) => {
    model.value.robot_ids = val !== null ? [val] : [];
  }
});

/** 调度日期字符串（yyyy-MM-dd）→ 时间戳（ms），用于回填 NDatePicker */
function dateStrToTs(value: string | null): number | null {
  if (!value) return null;
  const ts = dayjs(value, 'YYYY-MM-DD').valueOf();
  return Number.isNaN(ts) ? null : ts;
}

/** 调度时间字符串（HH:mm 或 HH:mm:ss）→ 时间戳（ms），用于回填 NTimePicker */
function timeStrToTs(value: string | null): number | null {
  if (!value) return null;
  // 以当天日期拼接，NTimePicker 仅取时分，具体日期不影响
  const ts = dayjs(`${dayjs().format('YYYY-MM-DD')} ${value}`).valueOf();
  return Number.isNaN(ts) ? null : ts;
}

/** 时间戳（ms）→ 调度日期字符串（yyyy-MM-dd），用于提交 */
function tsToDateStr(ts: number | null): string | null {
  return ts === null ? null : dayjs(ts).format('YYYY-MM-DD');
}

/** 时间戳（ms）→ 调度时间字符串（HH:mm:ss），用于提交 */
function tsToTimeStr(ts: number | null): string | null {
  return ts === null ? null : dayjs(ts).format('HH:mm:ss');
}

/** 点位管理 */
function addPoint() {
  model.value.points.push({
    sort_order: model.value.points.length,
    point_name: null,
    annotation_id: null,
    // 动作列表可为空：新增点位时不预置默认动作，用户按需添加
    actions: []
  });
}

function removePoint(index: number) {
  model.value.points.splice(index, 1);
  model.value.points.forEach((p, i) => {
    p.sort_order = i;
  });
}

/** 点位内动作管理 */
function addAction(point: PointItem) {
  point.actions.push({ action: 'no', voice_text: null });
}

function removeAction(point: PointItem, index: number) {
  point.actions.splice(index, 1);
}

/** 校验规则 */
const rules = computed(() => ({
  name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    { min: 2, max: 20, message: '任务名称为 2-20 字', trigger: 'blur' }
  ],
  task_type: { required: true, message: '请选择任务类型', trigger: 'change' },
  // 播报任务不需要场景地图，仅巡逻任务必填
  map_id: isPatrol.value
    ? { required: true, type: 'number' as const, message: '请选择场景地图', trigger: 'change' }
    : { required: false },
  robot_ids: {
    required: true,
    type: 'array' as const,
    min: 1,
    // 巡逻任务仅支持单台机器人，播报任务支持多选
    max: isPatrol.value ? 1 : undefined,
    message: isPatrol.value ? '请选择一台机器人' : '请至少选择一台机器人',
    trigger: 'change'
  }
}));

const taskId = computed(() => props.rowData?.id || -1);
const isEdit = computed(() => props.operateType === 'edit');
const submitting = ref(false);

async function handleInitModel() {
  model.value = createDefaultModel();
  annotationOptions.value = [];
  annotationMap.value = new Map();
  mapOptions.value = [];
  mapOptionsLoaded = false;

  if (props.operateType === 'edit' && props.rowData) {
    const cloned = jsonClone(props.rowData) as Api.Task.Task;
    model.value.name = cloned.name || '';
    model.value.task_type = cloned.task_type || 'patrol';
    model.value.broadcast_text = cloned.broadcast_text || null;
    model.value.schedule_enabled = cloned.schedule_enabled || false;
    model.value.schedule_date = dateStrToTs(cloned.schedule_date);
    model.value.schedule_start_time = timeStrToTs(cloned.schedule_start_time);
    model.value.schedule_repeat_cycles = cloned.schedule_repeat_cycle
      ? cloned.schedule_repeat_cycle.split(',').filter(v => v && v !== 'none')
      : [];
    model.value.map_id = cloned.map_id ?? cloned.robots?.find(r => r.map_id)?.map_id ?? null;
    model.value.robot_ids = cloned.robots?.map(r => r.id).slice(0, 1) || [];

    if (model.value.map_id !== null) {
      const fallbackName =
        cloned.map_name || cloned.robots?.find(r => r.map_id)?.map_name || `地图 #${model.value.map_id}`;
      mapOptions.value = [{ label: fallbackName, value: model.value.map_id }];
      await loadAnnotations(model.value.map_id);
    }

    if (cloned.points && cloned.points.length > 0) {
      model.value.points = cloned.points.map((p, i) => ({
        sort_order: i,
        point_name: p.point_name || null,
        annotation_id: p.annotation_id ?? null,
        actions:
          p.actions && p.actions.length > 0
            ? p.actions.map(a => ({ action: a.action || 'no', voice_text: a.voice_text ?? null }))
            : []
      }));
    }

    if (cloned.id) {
      const { data: detail } = await fetchGetTask(cloned.id);
      if (detail) {
        model.value.map_id = detail.map_id ?? detail.robots?.find(r => r.map_id)?.map_id ?? model.value.map_id;
        model.value.robot_ids = detail.robots?.map(r => r.id) || [];
        if (model.value.map_id !== null) {
          await loadAnnotations(model.value.map_id);
        }
        if (detail.points && detail.points.length > 0) {
          model.value.points = detail.points.map((p, i) => ({
            sort_order: i,
            point_name: p.point_name || null,
            annotation_id: p.annotation_id ?? null,
            actions:
              p.actions && p.actions.length > 0
                ? p.actions.map(a => ({ action: a.action || 'no', voice_text: a.voice_text ?? null }))
                : []
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

/** 任务类型切换：播报 → 巡逻时清空地图与机器人选择。
 * 巡逻需先选场景地图再按场景选机器人，播报阶段选的机器人/地图不适用，一并清空（点位随地图失效）。 */
function handleTaskTypeChange(val: Api.Task.TaskType) {
  const previous = model.value.task_type;
  model.value.task_type = val;
  if (previous === 'broadcast' && val === 'patrol') {
    model.value.map_id = null;
    model.value.robot_ids = [];
    model.value.points = [];
    annotationOptions.value = [];
    annotationMap.value = new Map();
    mapOptions.value = [];
    mapOptionsLoaded = false;
  }
}

function closeDrawer() {
  visible.value = false;
}

async function handleSubmit() {
  await validate();

  // Custom validations
  if (isPatrol.value && model.value.map_id === null) {
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
    for (let i = 0; i < model.value.points.length; i += 1) {
      const point = model.value.points[i];
      const invalidActionIndex = point.actions.findIndex(a => !a.action);
      if (invalidActionIndex !== -1) {
        window.$message?.warning(`请选择点位 ${i + 1} 中动作 ${invalidActionIndex + 1} 的运控类型`);
        return;
      }
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
    // 播报任务不绑定场景地图，强制置空避免脏数据
    map_id: isPatrol.value ? model.value.map_id : null,
    task_type: model.value.task_type,
    // 巡逻任务仅提交单台机器人，播报任务提交全部已选机器人
    robot_ids: isPatrol.value ? model.value.robot_ids.slice(0, 1) : model.value.robot_ids,
    schedule_enabled: model.value.schedule_enabled,
    // 未启用定时执行时，清空调度相关字段，避免残留脏数据
    schedule_date: model.value.schedule_enabled ? tsToDateStr(model.value.schedule_date) : null,
    schedule_start_time: model.value.schedule_enabled ? tsToTimeStr(model.value.schedule_start_time) : null,
    schedule_repeat_cycle:
      model.value.schedule_enabled && model.value.schedule_repeat_cycles.length > 0
        ? model.value.schedule_repeat_cycles.join(',')
        : null,
    points:
      model.value.task_type === 'patrol'
        ? model.value.points.map(p => ({
            sort_order: p.sort_order,
            point_name: p.point_name,
            annotation_id: p.annotation_id,
            actions: p.actions
          }))
        : undefined,
    broadcast_text: model.value.task_type === 'broadcast' ? model.value.broadcast_text : undefined
  };

  submitting.value = true;
  try {
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
  } finally {
    submitting.value = false;
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
  loadRobotOptions();
});
</script>

<template>
  <NModal
    v-model:show="visible"
    display-directive="show"
    preset="card"
    :mask-closable="false"
    :title="title"
    style="width: 640px; max-width: 90vw"
  >
    <NForm ref="formRef" :model="model" :rules="rules" label-placement="top">
      <!-- 基础信息 -->
      <NGrid :cols="2" :x-gap="16">
        <NFormItemGi :span="2" label="任务名称" path="name">
          <NInput v-model:value="model.name" placeholder="请输入任务名称（2-20字）" :maxlength="20" show-count />
        </NFormItemGi>
        <NFormItemGi :span="2" label="任务类型" path="task_type">
          <NRadioGroup :value="model.task_type" @update:value="handleTaskTypeChange">
            <NRadioButton v-for="opt in taskTypeOptions" :key="opt.value" :value="opt.value" :label="opt.label" />
          </NRadioGroup>
        </NFormItemGi>
        <!-- 场景约束提示：仅巡逻任务需绑定场景地图，才展示该约束 -->
        <NGi v-if="isPatrol" :span="2">
          <NAlert type="warning" class="mb-12px">
            注意：任务绑定机器人后，若机器人不在任务绑定的场景下，该任务无法执行！
          </NAlert>
        </NGi>
      </NGrid>

      <!-- 场景地图：仅巡逻任务需要选择 -->
      <NFormItem v-if="isPatrol" label="场景地图" path="map_id" class="mt-20px">
        <NSelect
          :value="model.map_id"
          :options="mapOptions"
          placeholder="请先选择场景地图"
          filterable
          clearable
          @update:value="handleMapChange"
          @focus="() => loadMapOptions()"
        />
      </NFormItem>

      <!-- 机器人绑定：巡逻单选（需先选场景且受场景约束），播报多选（不受场景约束） -->
      <NFormItem label="绑定机器人" path="robot_ids">
        <NSelect
          v-if="isPatrol"
          v-model:value="robotId"
          :options="filteredRobotOptions"
          :placeholder="model.map_id === null ? '请先选择场景地图' : '请选择一台机器人'"
          filterable
          clearable
          :disabled="model.map_id === null"
          :render-label="renderRobotLabel"
        />
        <NSelect
          v-else
          v-model:value="model.robot_ids"
          multiple
          :options="robotOptions"
          placeholder="请选择机器人（可多选）"
          filterable
          clearable
          max-tag-count="responsive"
        />
      </NFormItem>

      <!-- 巡逻点位配置 -->
      <template v-if="model.task_type === 'patrol'">
        <NDivider style="font-size: 16px" title-placement="center">巡逻点位配置</NDivider>
        <div v-if="selectedMapId === null" class="mb-12px text-13px" style="color: var(--n-text-color-3, #999)">
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
            <NFormItem label="巡逻点位" required>
              <NSelect
                v-model:value="point.annotation_id"
                :options="annotationOptions"
                :placeholder="selectedMapId === null ? '请先选择场景地图' : '请选择场景点位'"
                :disabled="selectedMapId === null"
                filterable
                @update:value="
                  (val: number | null) => {
                    const ann = val === null ? undefined : annotationMap.get(val);
                    point.point_name = ann?.name ?? null;
                  }
                "
              />
            </NFormItem>

            <NDivider title-placement="center" style="font-size: 16px">运控动作（可添加多个）</NDivider>
            <div v-for="(actionItem, actionIndex) in point.actions" :key="actionIndex" class="mb-8px">
              <NGrid :cols="3" :x-gap="12" responsive="screen">
                <NFormItemGi label="动作">
                  <NSelect v-model:value="actionItem.action" :options="actionOptions" placeholder="选择动作" />
                </NFormItemGi>
                <NFormItemGi :span="2" label="语音文本">
                  <NInput v-model:value="actionItem.voice_text" placeholder="语音播报文本" />
                </NFormItemGi>
              </NGrid>
              <div class="mb-40px flex">
                <NButton type="error" ghost size="small" @click="removeAction(point, actionIndex)">删除动作</NButton>
              </div>
            </div>
            <NButton dashed size="small" block @click="addAction(point)">
              <template #icon>
                <icon-ic-round-plus class="text-icon" />
              </template>
              添加动作
            </NButton>
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
        <NDivider style="font-size: 16px" title-placement="center">播报配置</NDivider>
        <NFormItem label="播报文本">
          <NInput v-model:value="model.broadcast_text" type="textarea" placeholder="请输入播报文本" :rows="3" />
        </NFormItem>
      </template>

      <!-- 定时配置 -->
      <NDivider style="font-size: 16px" title-placement="center">定时配置（可选）</NDivider>
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

    <template #action>
      <NSpace justify="end" :size="16">
        <NButton @click="closeDrawer">{{ $t('common.cancel') }}</NButton>
        <NButton type="primary" :loading="submitting" :disabled="submitting" @click="handleSubmit">
          {{ $t('common.confirm') }}
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<style scoped>
:deep(.n-divider:not(.n-divider--dashed) .n-divider__line) {
  background-color: transparent;
}
</style>
