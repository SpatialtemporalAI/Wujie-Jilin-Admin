<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue';
import { useMapEditor } from './composables/useMapEditor';
import EditorToolbar from './modules/editor-toolbar.vue';
import CanvasEditor from './modules/canvas-editor.vue';
import PropertyPanel from './modules/property-panel.vue';
import { fetchCreateSceneMap } from '@/service/api/scene';
import { fetchUploadFile, getFilePreviewUrl } from '@/service/api/file';
import { degToRad } from '@/utils/coordinate';

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

const addDialogVisible = ref(false);
const newMapName = ref('');
const newMapGroupId = ref<number | null>(null);
const newMapImageId = ref<number | null>(null);
const newMapImageUrl = ref('');
const newMapOriginalWidth = ref<number | null>(null);
const newMapOriginalHeight = ref<number | null>(null);
const newMapImageRef = ref<HTMLImageElement>();
const newMapPointX = ref<number | null>(null);
const newMapPointY = ref<number | null>(null);
const newMapPointAngle = ref(0);
const newMapResolution = ref(0.05);
const addSceneUploading = ref(false);

function getScaledStartPoint() {
  const imageRect = newMapImageRef.value?.getBoundingClientRect();
  if (
    !imageRect ||
    !newMapOriginalWidth.value ||
    !newMapOriginalHeight.value ||
    imageRect.width <= 0 ||
    imageRect.height <= 0 ||
    newMapPointX.value === null ||
    newMapPointY.value === null
  ) {
    return null;
  }
  const scaleX = newMapOriginalWidth.value / imageRect.width;
  const scaleY = newMapOriginalHeight.value / imageRect.height;
  return {
    x: newMapPointX.value * scaleX,
    y: newMapPointY.value * scaleY,
    angle: newMapPointAngle.value,
  };
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

async function handleAddScene() {
  newMapName.value = '';
  newMapGroupId.value = null;
  newMapImageId.value = null;
  newMapImageUrl.value = '';
  newMapOriginalWidth.value = null;
  newMapOriginalHeight.value = null;
  newMapPointX.value = null;
  newMapPointY.value = null;
  newMapPointAngle.value = 0;
  newMapResolution.value = 0.05;
  addDialogVisible.value = true;
}

async function handleAddSceneUpload({ file }: { file: { file: File | null } }) {
  if (!file.file) return;
  addSceneUploading.value = true;
  try {
    const { data, error } = await fetchUploadFile(file.file, { includeImageInfo: true });
    if (!error && data) {
      newMapImageId.value = data.id;
      newMapImageUrl.value = getFilePreviewUrl(data.id);
      newMapOriginalWidth.value = data.image_width ?? null;
      newMapOriginalHeight.value = data.image_height ?? null;
      window.$message?.success('图片上传成功');
    }
  } finally {
    addSceneUploading.value = false;
  }
}

function handleRemoveAddSceneImage() {
  newMapImageId.value = null;
  newMapImageUrl.value = '';
  newMapOriginalWidth.value = null;
  newMapOriginalHeight.value = null;
}

async function confirmAddScene() {
  if (!newMapName.value.trim()) {
    window.$message?.warning('请输入场景名称');
    return false;
  }
  if (!newMapImageId.value) {
    window.$message?.warning('请上传场景图片');
    return false;
  }
  if (!newMapOriginalWidth.value || !newMapOriginalHeight.value) {
    window.$message?.warning('请确认图片原图尺寸');
    return false;
  }
  const startPoint = getScaledStartPoint();
  if (!startPoint) {
    window.$message?.warning('请输入起始点位 X、Y 和角度');
    return false;
  }
  try {
    const { data } = await fetchCreateSceneMap({
      name: newMapName.value.trim(),
      group_id: newMapGroupId.value,
      image_id: newMapImageId.value,
      width: newMapOriginalWidth.value,
      height: newMapOriginalHeight.value,
      resolution: newMapResolution.value,
      start_point_x: startPoint.x,
      start_point_y: startPoint.y,
    });
    if (data) {
      addDialogVisible.value = false;
      await editor.loadSceneList();
      await editor.loadMap((data as any).id);

      editor.addAnnotation({
        x: 0,
        y: 0,
        name: '起始点位',
        angle: degToRad(startPoint.angle || 0),
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
      name: `接待点${count}`,
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
          @blank-click="typeSwitchShow = false" />
      </div>

      <PropertyPanel class="w-380px flex-shrink-0" :editor-data="editor.editorData.value"
        :selected-element="editor.selectedElement.value" :resolution="editor.resolution.value"
        :scene-list="editor.sceneList.value" :selected-map-id="editor.selectedMapId.value"
        :map-id="editor.selectedMapId.value" @update-element="handleUpdateElement"
        @remove-element="editor.removeElement" @select-scene="handleSelectMap" @add-scene="handleAddScene"
        @delete-scene="handleDeleteScene" @locate-robot="handleLocateRobot" @focus-annotation="handleFocusAnnotation"
        @select-element="el => (editor.selectedElement.value = el)" />
    </div>

    <!-- 右键上下文菜单 -->
    <NDropdown placement="bottom-start" trigger="manual" :x="contextMenuX" :y="contextMenuY"
      :show="contextMenuShow" :options="contextMenuOptions" @select="handleContextMenuSelect"
      @clickoutside="() => (contextMenuShow = false)" />

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

    <!-- Add scene dialog -->
    <NModal v-model:show="addDialogVisible" preset="dialog" title="新增场景" positive-text="确定" negative-text="取消"
      @positive-click="confirmAddScene">
      <NForm label-placement="left" label-width="92">
        <NFormItem label="场景名称">
          <NInput v-model:value="newMapName" placeholder="请输入场景名称" />
        </NFormItem>
        <NFormItem label="场景图片">
          <div class="w-full">
            <NUpload :max="1" accept="image/*" :custom-request="handleAddSceneUpload" :show-file-list="false">
              <NButton :loading="addSceneUploading" ghost>
                <template #icon><icon-ic-round-upload /></template>
                {{ addSceneUploading ? '上传中...' : '选择图片' }}
              </NButton>
            </NUpload>
            <div v-if="newMapImageUrl" class="mt-8px flex items-center gap-8px">
              <img ref="newMapImageRef" :src="newMapImageUrl" class="max-h-160px max-w-260px object-contain" />
              <div class="text-xs text-gray-500">
                原图：{{ newMapOriginalWidth ?? '-' }} × {{ newMapOriginalHeight ?? '-' }} px
              </div>
              <NButton text type="error" @click="handleRemoveAddSceneImage">移除</NButton>
            </div>
          </div>
        </NFormItem>
        <NFormItem label="起始点位">
          <div class="grid w-full grid-cols-4 gap-8px">
            <NInputNumber v-model:value="newMapPointX" placeholder="原始X" class="w-full" />
            <NInputNumber v-model:value="newMapPointY" placeholder="原始Y" class="w-full" />
            <NInputNumber v-model:value="newMapPointAngle" placeholder="角度" class="w-full" />
            <NInputNumber v-model:value="newMapResolution" placeholder="分辨率" :step="0.01" :min="0.01" class="w-full" />
          </div>
        </NFormItem>
        <div class="text-xs text-gray-500">
          起始点位按上方图片当前网页显示尺寸录入，保存时会按 原图尺寸 / 网页显示尺寸 缩放到地图原图坐标。分辨率(m/px)对应 ROS map.yaml 中的 resolution，默认 0.05。
        </div>
      </NForm>
    </NModal>
  </div>
</template>
