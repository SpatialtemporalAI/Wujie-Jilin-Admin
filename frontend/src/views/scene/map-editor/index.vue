<script setup lang="ts">
import { computed, h, nextTick, onMounted, onBeforeUnmount, ref, watch } from 'vue';
import type { DialogReactive, UploadFileInfo } from 'naive-ui';
import { NButton, NSpace, useDialog, useMessage } from 'naive-ui';
import { $t } from '@/locales';
import { useMapEditor } from './composables/useMapEditor';
import type { SelectedElement } from './composables/useMapEditor';
import EditorToolbar from './modules/editor-toolbar.vue';
import CanvasEditor from './modules/canvas-editor.vue';
import PropertyPanel from './modules/property-panel.vue';
import { fetchCreateSceneMap, fetchUpdateSceneMap, fetchGetSceneMap, fetchUploadSceneMapEditorImage, fetchParseSceneMapConfig } from '@/service/api/scene';
import { fetchGetMapRobotLocations } from '@/service/api';
import { getFilePreviewUrl } from '@/service/api/file';
import { extractRobotPoint } from './utils/robot-location';
import { radToDeg } from '@/utils/coordinate';

defineOptions({ name: 'SceneMapEditor' });
const message = useMessage()
const dialog = useDialog()

const editor = useMapEditor();
const canvasRef = ref<InstanceType<typeof CanvasEditor>>();

const zoomLevel = ref(1);
const cursorX = ref(0);
const cursorY = ref(0);

// 当前地图绑定机器人的实时位置（画布展示）。位置数据由外部写入 DB，平台只读，定时轮询刷新。
const ROBOT_LOCATION_POLL_MS = 5000;
const robotLocations = ref<Api.Robot.RobotLocationItem[]>([]);
let robotPollTimer: number | null = null;

async function loadRobotLocations(mapId: number) {
  const { data, error } = await fetchGetMapRobotLocations(mapId);
  if (!error && data) {
    robotLocations.value = data;
  }
}

function stopRobotPolling() {
  if (robotPollTimer !== null) {
    window.clearInterval(robotPollTimer);
    robotPollTimer = null;
  }
}

// 切换地图时重启轮询；selectedMapId 由 loadMap 设置，覆盖初始加载/选择/新建场景等所有入口
watch(
  () => editor.selectedMapId.value,
  mapId => {
    stopRobotPolling();
    robotLocations.value = [];
    if (mapId) {
      loadRobotLocations(mapId);
      robotPollTimer = window.setInterval(() => loadRobotLocations(mapId), ROBOT_LOCATION_POLL_MS);
    }
  }
);

// 右键菜单状态
const contextMenuShow = ref(false);
const contextMenuX = ref(0);
const contextMenuY = ref(0);
const contextMenuScenePoint = ref({ x: 0, y: 0 });
const contextMenuTarget = ref<{ type: 'annotation' | 'object'; id: number } | null>(null);

const baseContextMenuOptions = [
  { label: '添加点位', key: 'add-point' },
  {
    label: '新增障碍物',
    key: 'add-obstacle',
    children: [
      { label: '圆形', key: 'add-obstacle-circle' },
      { label: '三角形', key: 'add-obstacle-triangle' },
      { label: '正方形', key: 'add-obstacle-square' },
    ],
  },
  { label: '禁行区域/虚拟墙', key: 'add-restricted' },
  { label: '电子围栏', key: 'add-fence' },
];

const contextMenuOptions = computed(() => {
  if (!contextMenuTarget.value) return baseContextMenuOptions;
  const target = contextMenuTarget.value;
  const item = target.type === 'annotation'
    ? editor.editorData.value?.annotations.find(a => a.id === target.id)
    : editor.editorData.value?.objects.find(o => o.id === target.id);
  const name = (item as any)?.name || (target.type === 'annotation' ? '点位' : '对象');
  return [
    ...baseContextMenuOptions,
    { type: 'divider', key: 'divider' },
    { label: `删除「${name}」`, key: 'delete-target', props: { style: 'color: #ef4444' } },
  ];
});

// 改名弹窗状态
const renameDialogVisible = ref(false);
const renameValue = ref('');
const renameTarget = ref<{ type: 'annotation' | 'object'; id: number } | null>(null);

// 点位类型切换 tooltip 状态
const typeSwitchShow = ref(false);
const typeSwitchX = ref(0);
const typeSwitchY = ref(0);
const typeSwitchTargetId = ref<number | null>(null);
const typeSwitchCurrentType = ref<'navigation' | 'reception'>('reception');

// 元素信息悬浮 tooltip
const hoverInfoShow = ref(false);
const hoverInfoX = ref(0);
const hoverInfoY = ref(0);
const hoverInfoTarget = ref<{ type: 'annotation' | 'object' | 'robot'; id: number } | null>(null);

const hoverInfo = computed(() => {
  const t = hoverInfoTarget.value;
  if (!t) return null;
  // 机器人：位置由外部写入 DB，世界坐标(米)直接展示（与点位同坐标系）
  if (t.type === 'robot') {
    const robot = robotLocations.value.find(r => r.id === t.id);
    if (!robot) return null;
    const pt = extractRobotPoint(robot);
    if (!pt) return null;
    return {
      kind: '机器人',
      name: robot.name || '-',
      type: robot.status || '-',
      x: pt.x.toFixed(2),
      y: pt.y.toFixed(2),
      size: null as string | null,
      // 朝向角(ROS 弧度) → 度并归一到 [0,360)
      angle: pt.angle !== undefined ? `${Math.round(((radToDeg(pt.angle) % 360) + 360) % 360)}°` : '-',
    };
  }
  if (!editor.editorData.value) return null;
  if (t.type === 'annotation') {
    const ann = editor.editorData.value.annotations.find(a => a.id === t.id);
    if (!ann) return null;
    const typeName = ann.type === 'navigation' || ann.type === '返回点' ? '返回点' : '接待点';
    const angleDeg = Math.round(((ann.angle || 0) * 180 / Math.PI + 360) % 360);
    const w = editor.pixelToWorldCoords(ann.x, ann.y);
    return {
      kind: '点位',
      name: ann.name || '-',
      type: typeName,
      x: w.x.toFixed(2),
      y: w.y.toFixed(2),
      size: null as string | null,
      angle: `${angleDeg}°`,
    };
  }
  const obj = editor.editorData.value.objects.find(o => o.id === t.id);
  if (!obj) return null;
  const isRestricted = obj.type === 'restricted' || obj.type === '禁区';
  const isFence = obj.type === 'fence' || obj.type === '电子围栏';
  const shapeMap: Record<string, string> = {
    'obstacle-circle': '圆形',
    'obstacle-triangle': '三角形',
    'obstacle-square': '正方形',
  };
  const kind = isFence ? '电子围栏' : (isRestricted ? '禁行区域/虚拟墙' : '障碍物');
  const typeName = isFence ? '围栏' : (isRestricted ? '禁区' : (shapeMap[obj.type] || '障碍物'));
  const w = editor.pixelToWorldCoords(obj.x, obj.y);
  return {
    kind,
    name: obj.name || '-',
    type: typeName,
    x: w.x.toFixed(2),
    y: w.y.toFixed(2),
    size: `${(obj.width * editor.resolution.value).toFixed(2)} × ${(obj.height * editor.resolution.value).toFixed(2)} m`,
    angle: `${Math.round(obj.angle || 0)}°`,
  };
});

function handleHoverElement(data: { type: 'annotation' | 'object' | 'robot'; id: number; clientX: number; clientY: number } | null) {
  if (!data) {
    hoverInfoShow.value = false;
    hoverInfoTarget.value = null;
    return;
  }
  hoverInfoTarget.value = { type: data.type, id: data.id };
  hoverInfoX.value = data.clientX + 16;
  hoverInfoY.value = data.clientY + 16;
  hoverInfoShow.value = true;
}

const sceneDialogVisible = ref(false);
const sceneDialogMode = ref<'add' | 'edit'>('add');
const editMapId = ref<number | null>(null);
const sceneFormName = ref('');
const sceneFormImageId = ref<number | null>(null);
const sceneFormImageUrl = ref('');
const sceneFormOriginalWidth = ref<number | null>(null);
const sceneFormOriginalHeight = ref<number | null>(null);
const sceneFormImageRef = ref<HTMLImageElement>();
const sceneFormPointX = ref<number | null>(null);
const sceneFormPointY = ref<number | null>(null);
const sceneFormResolution = ref(0.05);
const sceneUploading = ref(false);
const sceneUploadFileList = ref<UploadFileInfo[]>([]);
const configUploading = ref(false);
const configUploadFileList = ref<UploadFileInfo[]>([]);
const configFileName = ref('');

// 场景地图切换守卫
type SwitchAction = 'save' | 'discard' | 'cancel';

interface SwitchMapOptions {
  /** 即使 mapId 与当前选中相同也强制重新加载（如编辑当前场景元数据） */
  force?: boolean;
}

function showDirtySwitchDialog(): Promise<SwitchAction> {
  return new Promise(resolve => {
    let dialogInst: DialogReactive | null = null;

    const close = (action: SwitchAction) => {
      dialogInst?.destroy();
      resolve(action);
    };

    dialogInst = dialog.warning({
      title: $t('page.sceneMapEditor.unsavedChangesTitle'),
      content: $t('page.sceneMapEditor.unsavedChangesTip'),
      action: () =>
        h(NSpace, { justify: 'end' }, () => [
          h(
            NButton,
            { size: 'small', onClick: () => close('cancel') },
            { default: () => $t('common.cancel') }
          ),
          h(
            NButton,
            { size: 'small', onClick: () => close('discard') },
            { default: () => $t('page.sceneMapEditor.discardAndSwitch') }
          ),
          h(
            NButton,
            { size: 'small', type: 'primary', onClick: () => close('save') },
            { default: () => $t('page.sceneMapEditor.saveAndSwitch') }
          )
        ]),
      onClose: () => close('cancel'),
      onMaskClick: () => close('cancel')
    });
  });
}

function showDeleteUnsavedDialog(): Promise<boolean> {
  return new Promise(resolve => {
    let dialogInst: DialogReactive | null = null;

    const close = (confirmed: boolean) => {
      dialogInst?.destroy();
      resolve(confirmed);
    };

    dialogInst = dialog.warning({
      title: $t('page.sceneMapEditor.unsavedChangesTitle'),
      content: $t('page.sceneMapEditor.deleteUnsavedTip'),
      positiveText: $t('page.sceneMapEditor.continueDelete'),
      negativeText: $t('common.cancel'),
      onPositiveClick: () => close(true),
      onNegativeClick: () => close(false),
      onClose: () => close(false),
      onMaskClick: () => close(false)
    });
  });
}

async function switchMap(mapId: number, options: SwitchMapOptions = {}): Promise<boolean> {
  if (editor.switching.value) return false;
  if (!options.force && mapId === editor.selectedMapId.value) return true;

  editor.switching.value = true;
  try {
    if (editor.isDirty.value) {
      const action = await showDirtySwitchDialog();
      if (action === 'cancel') return false;

      if (action === 'save') {
        const saved = await editor.saveMap({ silent: true });
        if (!saved) return false;
      }
    }

    return await editor.loadMap(mapId);
  } finally {
    editor.switching.value = false;
  }
}

// 删除确认相关
let isDeleteConfirming = false;

function isInputElementFocused() {
  const active = document.activeElement;
  if (!active) return false;
  const tagName = active.tagName;
  return tagName === 'INPUT' || tagName === 'TEXTAREA' || (active as HTMLElement).isContentEditable;
}

function getElementNameAndKind(target: SelectedElement) {
  const data = editor.editorData.value;
  if (!data) return { name: '', kind: '' };
  if (target.type === 'annotation') {
    const ann = data.annotations.find(a => a.id === target.id);
    return { name: ann?.name || '', kind: '点位' };
  }
  if (target.type === 'object') {
    const obj = data.objects.find(o => o.id === target.id);
    if (!obj) return { name: '', kind: '' };
    const shapeMap: Record<string, string> = {
      'obstacle-circle': '圆形',
      'obstacle-triangle': '三角形',
      'obstacle-square': '正方形',
    };
    const isRestricted = obj.type === 'restricted' || obj.type === '禁区';
    const isFence = obj.type === 'fence' || obj.type === '电子围栏';
    const kind = isFence ? '电子围栏' : (isRestricted ? '禁行区域/虚拟墙' : (shapeMap[obj.type] || '障碍物'));
    return { name: obj.name || '', kind };
  }
  return { name: '', kind: '路径' };
}

function confirmAndRemoveElement(target: SelectedElement | null) {
  if (!target || isDeleteConfirming) return;

  // 点位：仅当已关联任务时才弹窗确认，未关联任务直接删除
  if (target.type === 'annotation') {
    const ann = editor.editorData.value?.annotations.find(a => a.id === target.id);
    const taskCount = ann?.task_count ?? 0;
    if (taskCount <= 0) {
      editor.removeElement(target.type, target.id);
      return;
    }
    isDeleteConfirming = true;
    const resetFlag = () => {
      isDeleteConfirming = false;
    };
    dialog.warning({
      title: '提示',
      content: `当前点位已关联 ${taskCount} 个任务，删除点位后任务自动取消关联该点位，确认是否删除？ 删除后点击右上角保存生效`,
      positiveText: '确认',
      negativeText: '取消',
      draggable: true,
      onPositiveClick: () => {
        editor.removeElement(target.type, target.id);
      },
      onNegativeClick: resetFlag,
      onClose: resetFlag,
    });
    return;
  }

  // 障碍物/禁行区域/电子围栏：保持通用确认
  isDeleteConfirming = true;
  const resetFlag = () => {
    isDeleteConfirming = false;
  };
  const { name, kind } = getElementNameAndKind(target);
  const displayName = name || '未命名';
  dialog.warning({
    title: '提示',
    content: `确认删除选中的「${displayName}」(${kind})？ 删除后点击右上角保存生效`,
    positiveText: '确认',
    negativeText: '取消',
    draggable: true,
    onPositiveClick: () => {
      editor.removeElement(target.type, target.id);
    },
    onNegativeClick: resetFlag,
    onClose: resetFlag,
  });
}

function handleRemoveElement(type: 'annotation' | 'path' | 'object', id: number) {
  // 点位删除统一走确认函数：仅在已关联任务时弹窗，否则直接删除
  if (type === 'annotation') {
    confirmAndRemoveElement({ type, id });
    return;
  }
  editor.removeElement(type, id);
}

function handleDeleteKeyDown(e: KeyboardEvent) {
  if (e.key !== 'Delete' && e.key !== 'Backspace') return;
  if (isInputElementFocused()) return;
  const target = editor.selectedElement.value;
  if (!target) return;
  e.preventDefault();
  confirmAndRemoveElement(target);
}

function resetSceneForm() {
  sceneFormName.value = '';
  sceneFormImageId.value = null;
  sceneFormImageUrl.value = '';
  sceneFormOriginalWidth.value = null;
  sceneFormOriginalHeight.value = null;
  sceneFormPointX.value = null;
  sceneFormPointY.value = null;
  sceneFormResolution.value = 0.05;
  configUploadFileList.value = [];
  configFileName.value = '';
}

onMounted(async () => {
  window.addEventListener('keydown', handleDeleteKeyDown);
  await editor.loadSceneList();
  if (editor.sceneList.value.length > 0) {
    await switchMap(editor.sceneList.value[0].id);
  }
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleDeleteKeyDown);
  stopRobotPolling();
});

async function handleSelectMap(mapId: number) {
  await switchMap(mapId);
}

function handleOpenAddScene() {
  resetSceneForm();
  sceneDialogMode.value = 'add';
  editMapId.value = null;
  sceneDialogVisible.value = true;
}

async function handleOpenEditScene(mapId: number) {
  try {
    const { data, error } = await fetchGetSceneMap(mapId);
    if (error || !data) {
      window.$message?.error('加载场景详情失败');
      return;
    }
    resetSceneForm();
    sceneDialogMode.value = 'edit';
    editMapId.value = mapId;
    sceneFormName.value = data.name || '';
    sceneFormImageId.value = data.image_id ?? null;
    sceneFormOriginalWidth.value = data.width ?? null;
    sceneFormOriginalHeight.value = data.height ?? null;
    sceneFormPointX.value = data.start_point_x ?? null;
    sceneFormPointY.value = data.start_point_y ?? null;
    sceneFormResolution.value = data.resolution ?? 0.05;
    if (data.image_id) {
      sceneFormImageUrl.value = getFilePreviewUrl(data.image_id);
    }
    sceneDialogVisible.value = true;
  } catch (e: any) {
    window.$message?.error(e?.message || '加载场景详情失败');
  }
}

async function handleSceneUpload({ file }: { file: { file: File | null } }) {
  if (!file.file) return;
  sceneUploading.value = true;
  try {
    const { data, error } = await fetchUploadSceneMapEditorImage(file.file, { includeImageInfo: true });
    if (!error && data) {
      sceneFormImageId.value = data.id;
      sceneFormImageUrl.value = getFilePreviewUrl(data.id);
      sceneFormOriginalWidth.value = data.image_width ?? null;
      sceneFormOriginalHeight.value = data.image_height ?? null;
      window.$message?.success('图片上传成功');
    }
  } finally {
    sceneUploading.value = false;
    sceneUploadFileList.value = [];
  }
}

function handleRemoveSceneImage() {
  sceneFormImageId.value = null;
  sceneFormImageUrl.value = '';
  sceneFormOriginalWidth.value = null;
  sceneFormOriginalHeight.value = null;
}

async function handleConfigUpload({ file }: { file: { file: File | null } }) {
  if (!file.file) return;
  configUploading.value = true;
  try {
    const { data, error } = await fetchParseSceneMapConfig(file.file);
    if (!error && data) {
      sceneFormResolution.value = data.resolution;
      sceneFormPointX.value = data.start_point_x;
      sceneFormPointY.value = data.start_point_y;
      configFileName.value = file.file.name;
      window.$message?.success('配置文件解析成功，已回显分辨率与起始点');
    }
  } finally {
    configUploading.value = false;
    configUploadFileList.value = [];
  }
}

function handleRemoveConfig() {
  configFileName.value = '';
}

async function confirmSceneSubmit() {
  const name = sceneFormName.value.trim();
  if (!name) {
    window.$message?.warning('请输入场景名称');
    return false;
  }
  if (sceneFormImageId.value == null) {
    window.$message?.warning('请上传场景图片');
    return false;
  }
  if (sceneFormOriginalWidth.value == null || sceneFormOriginalHeight.value == null) {
    window.$message?.warning('请确认图片原图尺寸');
    return false;
  }
  if (sceneFormPointX.value == null || sceneFormPointY.value == null) {
    window.$message?.warning('请输入扫图起始点 X、Y');
    return false;
  }
  if (sceneFormResolution.value == null) {
    window.$message?.warning('请输入分辨率');
    return false;
  }

  if (sceneDialogMode.value === 'add') {
    try {
      const { data } = await fetchCreateSceneMap({
        name,
        image_id: sceneFormImageId.value,
        width: sceneFormOriginalWidth.value,
        height: sceneFormOriginalHeight.value,
        resolution: sceneFormResolution.value,
        // start_point 为世界坐标（米），直接使用输入值，不做像素缩放转换
        start_point_x: sceneFormPointX.value,
        start_point_y: sceneFormPointY.value
      });
      if (data) {
        sceneDialogVisible.value = false;
        await editor.loadSceneList();
        const switched = await switchMap(data.id);
        if (!switched) return false;

        // 返回点固定在世界坐标 (0,0)，与场景 start_point 无关
        const origin = editor.worldToPixelCoords(0, 0);
        editor.addAnnotation({
          x: origin.x,
          y: origin.y,
          name: '扫图起始点',
          angle: 0,
          type: 'navigation',
        });
        await editor.saveMap({ silent: true });

        window.$message?.success('创建成功');
      }
    } catch (e: any) {
      window.$message?.error(e?.message || '创建失败');
    }
    return false;
  }

  // edit 模式
  if (!editMapId.value) {
    window.$message?.error('未找到场景 ID');
    return false;
  }
  try {
    const { error } = await fetchUpdateSceneMap(editMapId.value, {
      name,
      image_id: sceneFormImageId.value,
      width: sceneFormOriginalWidth.value,
      height: sceneFormOriginalHeight.value,
      resolution: sceneFormResolution.value,
      start_point_x: sceneFormPointX.value,
      start_point_y: sceneFormPointY.value
    });
    if (!error) {
      sceneDialogVisible.value = false;
      await editor.loadSceneList();
      if (editor.selectedMapId.value === editMapId.value) {
        await switchMap(editMapId.value, { force: true });
      }
      window.$message?.success('修改成功');
    }
  } catch (e: any) {
    window.$message?.error(e?.message || '修改失败');
  }
  return false;
}

async function handleDeleteScene(mapId: number) {
  try {
    if (editor.isDirty.value && editor.selectedMapId.value === mapId) {
      const confirmed = await showDeleteUnsavedDialog();
      if (!confirmed) return;
    }

    const { wasSelected } = await editor.deleteScene(mapId);
    if (wasSelected && editor.sceneList.value.length > 0) {
      await switchMap(editor.sceneList.value[0].id);
    }
  } catch (e: any) {
    window.$message?.error(e?.message || '删除失败');
  }
}

function handleContextMenu(data: { x: number; y: number; clientX: number; clientY: number; target: { type: 'annotation' | 'object'; id: number } | null }) {
  contextMenuScenePoint.value = { x: data.x, y: data.y };
  contextMenuX.value = data.clientX;
  contextMenuY.value = data.clientY;
  contextMenuTarget.value = data.target;
  contextMenuShow.value = true;
}

function handleContextMenuSelect(key: string) {
  contextMenuShow.value = false;
  const { x, y } = contextMenuScenePoint.value;

  if (key === 'delete-target') {
    confirmAndRemoveElement(contextMenuTarget.value);
    return;
  }

  if (key === 'add-point') {
    // 点位不能设置在障碍物上：右键落在障碍物上时拦截并提示
    const target = contextMenuTarget.value;
    if (target?.type === 'object') {
      const obj = editor.editorData.value?.objects.find(o => o.id === target.id);
      if (obj && typeof obj.type === 'string' && obj.type.startsWith('obstacle-')) {
        contextMenuTarget.value = null;
        window.$message?.warning('注意：点位不能设置在障碍物上！');
        return;
      }
    }
    const count = (editor.editorData.value?.annotations.length || 0) + 1;
    editor.addAnnotation({
      x,
      y,
      name: `点位${count}`,
      angle: 0,
      type: 'reception',
    });
    // 保持无选中状态
    editor.selectedElement.value = null;
    const pointWorld = editor.pixelToWorldCoords(x, y);
    window.$message?.success(`已添加点位(${pointWorld.x.toFixed(2)}, ${pointWorld.y.toFixed(2)})`);
    return;
  }

  if (key === 'add-obstacle-circle' || key === 'add-obstacle-triangle' || key === 'add-obstacle-square') {
    const type = key.replace('add-', '');
    const count = (editor.editorData.value?.objects.filter(o => o.type.startsWith('obstacle-')).length || 0) + 1;
    editor.addObject({
      type,
      name: `障碍物${count}`,
      x: x - 5,
      y: y - 5,
      width: 10,
      height: 10,
      points: null,
    });
    window.$message?.success('已添加障碍物');
    return;
  }

  if (key === 'add-restricted') {
    const count = (editor.editorData.value?.objects.filter(o => o.type === 'restricted').length || 0) + 1;
    editor.addObject({
      type: 'restricted',
      name: `禁区${count}`,
      x: x - 5,
      y: y - 5,
      width: 10,
      height: 10,
      points: null,
    });
    window.$message?.success('已添加禁行区域');
    return;
  }

  if (key === 'add-fence') {
    const count = (editor.editorData.value?.objects.filter(o => o.type === 'fence').length || 0) + 1;
    editor.addObject({
      type: 'fence',
      name: `电子围栏${count}`,
      x: x - 5,
      y: y - 5,
      width: 10,
      height: 10,
      points: null,
    });
    window.$message?.success('已添加电子围栏');
    return;
  }

  contextMenuTarget.value = null;
}

function handleRequestTypeSwitch(data: { id: number; clientX: number; clientY: number }) {
  if (!editor.editorData.value) return;
  const ann = editor.editorData.value.annotations.find(a => a.id === data.id);
  if (!ann) return;
  typeSwitchTargetId.value = data.id;
  typeSwitchCurrentType.value = (ann.type === 'navigation' ? 'navigation' : 'reception');
  typeSwitchX.value = data.clientX;
  typeSwitchY.value = data.clientY;
  typeSwitchShow.value = true;
}

function switchAnnotationType(type: 'navigation' | 'reception') {
  if (typeSwitchTargetId.value === null) return;
  editor.updateElement('annotation', typeSwitchTargetId.value, { type });
  typeSwitchShow.value = false;
  typeSwitchTargetId.value = null;
}

function handleRequestRename(data: { type: 'annotation' | 'object'; id: number }) {
  if (!editor.editorData.value) return;
  const list = data.type === 'annotation' ? editor.editorData.value.annotations : editor.editorData.value.objects;
  const item = list.find((i: any) => i.id === data.id);
  if (!item) return;
  renameTarget.value = { type: data.type, id: data.id };
  renameValue.value = (item as any).name || '';
  renameDialogVisible.value = true;
}

function confirmRename() {
  if (!renameTarget.value) return;
  const value = renameValue.value.trim();
  if (!value) {
    window.$message?.warning('请输入名称');
    return false;
  }
  editor.updateElement(renameTarget.value.type, renameTarget.value.id, { name: value });
  renameTarget.value = null;
  renameValue.value = '';
  renameDialogVisible.value = false;
  return true;
}

function handleUpdateElement(data: { type: string; id: number; updates: Record<string, any> }) {
  editor.updateElement(data.type as any, data.id, data.updates);
}

function handleExport(format: 'png' | 'jpeg' | 'webp') {
  canvasRef.value?.exportCanvas(format);
}

function handleZoomChange(zoom: number) {
  zoomLevel.value = zoom;
}

async function handleLocateRobot(data: { mapId: number; x: number; y: number }) {
  if (editor.selectedMapId.value !== data.mapId) {
    const switched = await switchMap(data.mapId);
    if (!switched) return;
  }
  await nextTick();
  const px = editor.worldToPixelCoords(data.x, data.y);
  canvasRef.value?.locatePixelPoint(px.x, px.y);
}

function handleCursorPosition(x: number, y: number) {
  cursorX.value = x;
  cursorY.value = y;
}

function handleFocusAnnotation(id: number) {
  if (!editor.editorData.value) return;
  const ann = editor.editorData.value.annotations.find(a => a.id === id);
  if (!ann) return;
  canvasRef.value?.locatePixelPoint(ann.x, ann.y);
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col">
    <EditorToolbar :can-undo="editor.canUndo.value"
      :can-redo="editor.canRedo.value" :is-dirty="editor.isDirty.value" :saving="editor.saving.value"
      :has-history="editor.hasHistory.value" :history-list="editor.historyList.value"
      @undo="editor.undo()" @redo="editor.redo()"
      @jump-to-step="(step: number) => editor.jumpToStep(step)" @save="editor.saveMap()" @export="handleExport" />

    <div class="flex min-h-0 flex-1 overflow-hidden">
      <div class="relative min-w-0 flex-1">
        <CanvasEditor ref="canvasRef" :editor-data="editor.editorData.value"
          :selected-element="editor.selectedElement.value"
          :grid-spacing="editor.gridSpacing.value" :resolution="editor.resolution.value" :loading="editor.loading.value"
          :robot-locations="robotLocations"
          @select-element="el => (editor.selectedElement.value = el)" @update-element="handleUpdateElement"
          @zoom-change="handleZoomChange" @cursor-position="handleCursorPosition" @undo="editor.undo()"
          @redo="editor.redo()" @context-menu="handleContextMenu"
          @request-type-switch="handleRequestTypeSwitch" @rename-element="handleRequestRename"
          @blank-click="typeSwitchShow = false"
          @hover-element="handleHoverElement" />
      </div>

      <PropertyPanel class="w-380px flex-shrink-0" :editor-data="editor.editorData.value"
        :selected-element="editor.selectedElement.value" :resolution="editor.resolution.value"
        :scene-list="editor.sceneList.value" :selected-map-id="editor.selectedMapId.value"
        :map-id="editor.selectedMapId.value" @update-element="handleUpdateElement"
        @remove-element="handleRemoveElement" @select-scene="handleSelectMap" @add-scene="handleOpenAddScene"
        @edit-scene="handleOpenEditScene" @delete-scene="handleDeleteScene" @locate-robot="handleLocateRobot"
        @focus-annotation="handleFocusAnnotation" @select-element="el => (editor.selectedElement.value = el)" />
    </div>

    <!-- 右键上下文菜单 -->
    <NDropdown placement="bottom-start" trigger="manual" :x="contextMenuX" :y="contextMenuY"
      :show="contextMenuShow" :options="contextMenuOptions" @select="handleContextMenuSelect"
      @clickoutside="() => (contextMenuShow = false)" />

    <!-- 元素信息浮窗（hover） -->
    <div v-if="hoverInfoShow && hoverInfo" class="pointer-events-none fixed z-50 rounded-md bg-black/80 px-10px py-8px text-xs text-white shadow-lg"
      :style="{ left: hoverInfoX + 'px', top: hoverInfoY + 'px' }">
      <div class="mb-4px font-medium">{{ hoverInfo.kind }}</div>
      <div class="grid grid-cols-[auto_1fr] gap-x-8px gap-y-2px">
        <span class="text-white/60">名称</span><span>{{ hoverInfo.name }}</span>
        <span class="text-white/60">类型</span><span>{{ hoverInfo.type }}</span>
        <span class="text-white/60">坐标</span><span>{{ hoverInfo.x }}, {{ hoverInfo.y }} m</span>
        <template v-if="hoverInfo.size">
          <span class="text-white/60">大小</span><span>{{ hoverInfo.size }}</span>
        </template>
        <span class="text-white/60">角度</span><span>{{ hoverInfo.angle }}</span>
      </div>
    </div>

    <!-- 点位类型切换 tooltip -->
    <NPopover v-model:show="typeSwitchShow" trigger="manual" placement="top" :x="typeSwitchX" :y="typeSwitchY"
      :show-arrow="true" @clickoutside="() => (typeSwitchShow = false)">
      <div class="flex gap-6px py-2px">
        <NButton size="tiny" :type="typeSwitchCurrentType === 'navigation' ? 'primary' : 'default'"
          @click="switchAnnotationType('navigation')">
          返回点
        </NButton>
        <NButton size="tiny" :type="typeSwitchCurrentType === 'reception' ? 'primary' : 'default'"
          @click="switchAnnotationType('reception')">
          接待点
        </NButton>
      </div>
    </NPopover>

    <!-- 重命名弹窗 -->
    <NModal v-model:show="renameDialogVisible" preset="dialog" title="重命名" positive-text="确定" negative-text="取消"
      @positive-click="confirmRename">
      <NInput v-model:value="renameValue" placeholder="请输入名称" @keydown.enter="confirmRename" />
    </NModal>

    <!-- Scene dialog (add/edit) -->
    <NModal v-model:show="sceneDialogVisible" preset="dialog" :title="sceneDialogMode === 'edit' ? '编辑场景' : '新增场景'"
      positive-text="确定" negative-text="取消" @positive-click="confirmSceneSubmit">
      <NForm label-placement="left" label-width="92">
        <NFormItem label="场景名称">
          <NInput v-model:value="sceneFormName" placeholder="请输入场景名称" />
        </NFormItem>
        <NFormItem v-if="sceneDialogMode === 'add'" label="场景图片">
          <div class="w-full">
            <NUpload
              v-model:file-list="sceneUploadFileList"
              :max="1"
              accept="image/*"
              :custom-request="handleSceneUpload"
              :show-file-list="false"
            >
              <NButton :loading="sceneUploading" ghost>
                <template #icon><icon-ic-round-upload /></template>
                {{ sceneUploading ? '上传中...' : '选择图片' }}
              </NButton>
            </NUpload>
            <div v-if="sceneFormImageUrl" class="mt-8px flex items-center gap-8px">
              <img ref="sceneFormImageRef" :src="sceneFormImageUrl" class="max-h-160px max-w-260px object-contain" />
              <div class="text-xs text-gray-500">
                原图：{{ sceneFormOriginalWidth ?? '-' }} × {{ sceneFormOriginalHeight ?? '-' }} px
              </div>
              <NButton text type="error" @click="handleRemoveSceneImage">移除</NButton>
            </div>
          </div>
        </NFormItem>
        <NFormItem v-else label="场景图片">
          <div v-if="sceneFormImageUrl" class="flex w-full items-center gap-8px">
            <img :src="sceneFormImageUrl" class="max-h-160px max-w-260px object-contain" />
            <div class="text-xs text-gray-500">
              原图：{{ sceneFormOriginalWidth ?? '-' }} × {{ sceneFormOriginalHeight ?? '-' }} px
            </div>
          </div>
          <span v-else class="text-xs text-gray-400">未设置图片</span>
        </NFormItem>
        <NFormItem v-if="sceneDialogMode === 'add'" label="配置文件">
          <div class="w-full">
            <NUpload
              v-model:file-list="configUploadFileList"
              :max="1"
              accept=".yaml,.yml,application/yaml,text/yaml"
              :custom-request="handleConfigUpload"
              :show-file-list="false"
            >
              <NButton :loading="configUploading" ghost>
                <template #icon><icon-ic-round-upload /></template>
                {{ configUploading ? '解析中...' : '选择配置文件' }}
              </NButton>
            </NUpload>
            <div v-if="configFileName" class="mt-8px flex items-center gap-8px">
              <NTag size="small" type="success" round>{{ configFileName }}</NTag>
              <NButton text type="error" @click="handleRemoveConfig">移除</NButton>
            </div>
            <div class="mt-4px text-xs text-gray-400">
              上传 ROS 地图 yaml，自动解析 resolution 与 origin 回显分辨率与起始点
            </div>
          </div>
        </NFormItem>
        <NFormItem label="扫图起始点">
          <div class="grid w-full grid-cols-2 gap-8px">
            <NInputNumber v-model:value="sceneFormPointX" :placeholder="sceneDialogMode === 'edit' ? 'X' : '原始X'"
              :disabled="sceneDialogMode === 'add'" class="w-full">
              <template #suffix>
                <span class="text-xs text-gray-400">米</span>
              </template>
            </NInputNumber>
            <NInputNumber v-model:value="sceneFormPointY" :placeholder="sceneDialogMode === 'edit' ? 'Y' : '原始Y'"
              :disabled="sceneDialogMode === 'add'" class="w-full">
              <template #suffix>
                <span class="text-xs text-gray-400">米</span>
              </template>
            </NInputNumber>
          </div>
        </NFormItem>
        <NFormItem label="分辨率">
          <NInputNumber v-model:value="sceneFormResolution" placeholder="m/px" :step="0.01" :min="0.01"
            :disabled="sceneDialogMode === 'add'" class="w-full">
            <template #suffix>
              <span class="text-xs text-gray-400">m/px</span>
            </template>
          </NInputNumber>
        </NFormItem>
      </NForm>
    </NModal>
  </div>
</template>
