<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue';
import type { UploadFileInfo } from 'naive-ui';
import { useMapEditor } from './composables/useMapEditor';
import EditorToolbar from './modules/editor-toolbar.vue';
import CanvasEditor from './modules/canvas-editor.vue';
import PropertyPanel from './modules/property-panel.vue';
import { fetchCreateSceneMap, fetchUpdateSceneMap, fetchGetSceneMap, fetchUploadSceneMapEditorImage } from '@/service/api/scene';
import { getFilePreviewUrl } from '@/service/api/file';

defineOptions({ name: 'SceneMapEditor' });

const editor = useMapEditor();
const canvasRef = ref<InstanceType<typeof CanvasEditor>>();

const zoomLevel = ref(1);
const cursorX = ref(0);
const cursorY = ref(0);

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
  { label: '禁行区域', key: 'add-restricted' },
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
const hoverInfoTarget = ref<{ type: 'annotation' | 'object'; id: number } | null>(null);

const hoverInfo = computed(() => {
  const t = hoverInfoTarget.value;
  if (!t || !editor.editorData.value) return null;
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
  const kind = isFence ? '电子围栏' : (isRestricted ? '禁行区域' : '障碍物');
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

function handleHoverElement(data: { type: 'annotation' | 'object'; id: number; clientX: number; clientY: number } | null) {
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
const sceneFormGroupId = ref<number | null>(null);
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

function getScaledStartPoint() {
  const imageRect = sceneFormImageRef.value?.getBoundingClientRect();
  if (
    !imageRect ||
    !sceneFormOriginalWidth.value ||
    !sceneFormOriginalHeight.value ||
    imageRect.width <= 0 ||
    imageRect.height <= 0 ||
    sceneFormPointX.value === null ||
    sceneFormPointY.value === null
  ) {
    return null;
  }
  const scaleX = sceneFormOriginalWidth.value / imageRect.width;
  const scaleY = sceneFormOriginalHeight.value / imageRect.height;
  return {
    x: sceneFormPointX.value * scaleX,
    y: sceneFormPointY.value * scaleY,
  };
}

function resetSceneForm() {
  sceneFormName.value = '';
  sceneFormGroupId.value = null;
  sceneFormImageId.value = null;
  sceneFormImageUrl.value = '';
  sceneFormOriginalWidth.value = null;
  sceneFormOriginalHeight.value = null;
  sceneFormPointX.value = null;
  sceneFormPointY.value = null;
  sceneFormResolution.value = 0.05;
}

onMounted(async () => {
  await editor.loadSceneList();
  if (editor.sceneList.value.length > 0) {
    await editor.loadMap(editor.sceneList.value[0].id);
  }
});

async function handleSelectMap(mapId: number) {
  await editor.loadMap(mapId);
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

async function confirmSceneSubmit() {
  if (!sceneFormName.value.trim()) {
    window.$message?.warning('请输入场景名称');
    return false;
  }

  if (sceneDialogMode.value === 'add') {
    if (!sceneFormImageId.value) {
      window.$message?.warning('请上传场景图片');
      return false;
    }
    if (!sceneFormOriginalWidth.value || !sceneFormOriginalHeight.value) {
      window.$message?.warning('请确认图片原图尺寸');
      return false;
    }
    const startPoint = getScaledStartPoint();
    if (!startPoint) {
      window.$message?.warning('请输入扫图起始点 X、Y');
      return false;
    }
    try {
      const { data } = await fetchCreateSceneMap({
        name: sceneFormName.value.trim(),
        group_id: sceneFormGroupId.value,
        image_id: sceneFormImageId.value,
        width: sceneFormOriginalWidth.value,
        height: sceneFormOriginalHeight.value,
        resolution: sceneFormResolution.value,
        start_point_x: startPoint.x,
        start_point_y: startPoint.y,
      });
      if (data) {
        sceneDialogVisible.value = false;
        await editor.loadSceneList();
        await editor.loadMap((data as any).id);

        editor.addAnnotation({
          x: 0,
          y: 0,
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
  if (sceneFormPointX.value === null || sceneFormPointY.value === null) {
    window.$message?.warning('请输入扫图起始点 X、Y');
    return false;
  }
  if (!editMapId.value) {
    window.$message?.error('未找到场景 ID');
    return false;
  }
  try {
    const { error } = await fetchUpdateSceneMap(editMapId.value, {
      name: sceneFormName.value.trim(),
      resolution: sceneFormResolution.value,
      start_point_x: sceneFormPointX.value,
      start_point_y: sceneFormPointY.value,
    });
    if (!error) {
      sceneDialogVisible.value = false;
      await editor.loadSceneList();
      if (editor.selectedMapId.value === editMapId.value) {
        await editor.loadMap(editMapId.value);
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
    await editor.deleteScene(mapId);
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
    const target = contextMenuTarget.value;
    contextMenuTarget.value = null;
    if (target) {
      editor.removeElement(target.type, target.id);
    }
    return;
  }

  if (key === 'add-point') {
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
    await editor.loadMap(data.mapId);
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
        @remove-element="editor.removeElement" @select-scene="handleSelectMap" @add-scene="handleOpenAddScene"
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
        <NFormItem label="扫图起始点">
          <div class="grid w-full grid-cols-2 gap-8px">
            <NInputNumber v-model:value="sceneFormPointX" :placeholder="sceneDialogMode === 'edit' ? 'X (米)' : '原始X'"
              class="w-full" />
            <NInputNumber v-model:value="sceneFormPointY" :placeholder="sceneDialogMode === 'edit' ? 'Y (米)' : '原始Y'"
              class="w-full" />
          </div>
        </NFormItem>
        <NFormItem label="分辨率">
          <NInputNumber v-model:value="sceneFormResolution" placeholder="m/px" :step="0.01" :min="0.01"
            class="w-full" />
        </NFormItem>
        <div v-if="sceneDialogMode === 'add'" class="text-xs text-gray-500">
          扫图起始点按上方图片当前网页显示尺寸录入，保存时会按 原图尺寸 / 网页显示尺寸 缩放到地图原图坐标。分辨率(m/px)对应 ROS map.yaml 中的 resolution，默认 0.05。
        </div>
        <div v-else class="text-xs text-gray-500">
          扫图起始点使用地图原图坐标系下的米值。分辨率(m/px)对应 ROS map.yaml 中的 resolution。
        </div>
      </NForm>
    </NModal>
  </div>
</template>
