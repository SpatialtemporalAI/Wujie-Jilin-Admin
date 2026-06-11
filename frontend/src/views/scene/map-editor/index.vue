<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue';
import { useMapEditor, type DrawingMode } from './composables/useMapEditor';
import EditorToolbar from './modules/editor-toolbar.vue';
import CanvasEditor from './modules/canvas-editor.vue';
import PropertyPanel from './modules/property-panel.vue';
import { fetchCreateSceneMap } from '@/service/api/scene';

defineOptions({ name: 'SceneMapEditor' });

const editor = useMapEditor();
const canvasRef = ref<InstanceType<typeof CanvasEditor>>();

const zoomLevel = ref(1);
const cursorX = ref(0);
const cursorY = ref(0);

const addDialogVisible = ref(false);
const newMapName = ref('');
const newMapGroupId = ref<number | null>(null);

const importDialogVisible = ref(false);
const importJsonText = ref('');

interface ImportMapPoint {
  label: string;
  position: [number, number, number];
  node?: string;
  description?: string;
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
  addDialogVisible.value = true;
}

async function confirmAddScene() {
  if (!newMapName.value.trim()) {
    window.$message?.warning('请输入场景名称');
    return;
  }
  try {
    const { data } = await fetchCreateSceneMap({
      name: newMapName.value.trim(),
      group_id: newMapGroupId.value,
    });
    if (data) {
      window.$message?.success('创建成功');
      addDialogVisible.value = false;
      await editor.loadSceneList();
      await editor.loadMap((data as any).id);
    }
  } catch (e: any) {
    window.$message?.error(e?.message || '创建失败');
  }
}

async function handleDeleteScene(mapId: number) {
  try {
    await editor.deleteScene(mapId);
  } catch (e: any) {
    window.$message?.error(e?.message || '删除失败');
  }
}

function handleAddAnnotation(data: { x: number; y: number; type: string }) {
  const name = data.type === 'navigation' ? `导航点${(editor.editorData.value?.annotations.length || 0) + 1}` : `接待点${(editor.editorData.value?.annotations.length || 0) + 1}`;
  editor.addAnnotation({ x: data.x, y: data.y, name, angle: 0, type: data.type });
}

function handleAddPath(data: { startId: number; endId: number }) {
  editor.addPath({ start_annotation_id: data.startId, end_annotation_id: data.endId });
}

function handleAddObject(data: { type: string; x: number; y: number; width: number; height: number; points?: string }) {
  editor.addObject({
    type: data.type,
    x: data.x,
    y: data.y,
    width: data.width,
    height: data.height,
    points: data.points || null,
  });
}

function handleUpdateElement(data: { type: string; id: number; updates: Record<string, any> }) {
  editor.updateElement(data.type as any, data.id, data.updates);
}

function handleImportJson() {
  importJsonText.value = '';
  importDialogVisible.value = true;
}

function confirmImportJson() {
  if (!editor.editorData.value) {
    window.$message?.warning('请先选择场景地图');
    return false;
  }

  let points: ImportMapPoint[];
  try {
    const parsed = JSON.parse(importJsonText.value);
    if (!Array.isArray(parsed)) {
      window.$message?.error('JSON 必须是数组');
      return false;
    }
    points = parsed;
  } catch {
    window.$message?.error('JSON 格式错误');
    return false;
  }

  try {
    const existingNames = new Set(editor.editorData.value.annotations.map(item => item.name));
    const importNames = new Set<string>();
    const annotations = points.map((point, index) => {
      const [x, y, angle] = point.position || [];
      if (!point.label || !Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(angle)) {
        throw new Error(`第 ${index + 1} 条数据缺少 label 或有效 position`);
      }

      const baseName = point.label.trim();
      let name = baseName;
      if (existingNames.has(name) || importNames.has(name)) {
        name = point.description?.trim() || `${baseName}${index + 1}`;
      }
      if (existingNames.has(name) || importNames.has(name)) {
        name = `${name}${index + 1}`;
      }
      existingNames.add(name);
      importNames.add(name);

      return { x, y, angle, name, type: 'reception' };
    });

    editor.addAnnotations(annotations);
    window.$message?.success(`已导入 ${annotations.length} 个点位，请保存地图`);
    importDialogVisible.value = false;
    return true;
  } catch (e: any) {
    window.$message?.error(e?.message || '导入失败');
    return false;
  }
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
  canvasRef.value?.locateMeterPoint(data.x, data.y);
}

function handleCursorPosition(x: number, y: number) {
  cursorX.value = x;
  cursorY.value = y;
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col">
    <EditorToolbar
      :drawing-mode="editor.drawingMode.value"
      :can-undo="editor.canUndo.value"
      :can-redo="editor.canRedo.value"
      :is-dirty="editor.isDirty.value"
      :saving="editor.saving.value"
      @update:drawing-mode="(m: DrawingMode) => (editor.drawingMode.value = m)"
      @undo="editor.undo()"
      @redo="editor.redo()"
      @save="editor.saveMap()"
      @import-json="handleImportJson"
      @export="handleExport"
    />

    <div class="flex min-h-0 flex-1 overflow-hidden">
      <div class="relative min-w-0 flex-1">
        <CanvasEditor
          ref="canvasRef"
          :editor-data="editor.editorData.value"
          :selected-element="editor.selectedElement.value"
          :drawing-mode="editor.drawingMode.value"
          :grid-spacing="editor.gridSpacing.value"
          :resolution="editor.resolution.value"
          :loading="editor.loading.value"
          @select-element="el => (editor.selectedElement.value = el)"
          @add-annotation="handleAddAnnotation"
          @add-path="handleAddPath"
          @add-object="handleAddObject"
          @update-element="handleUpdateElement"
          @zoom-change="handleZoomChange"
          @cursor-position="handleCursorPosition"
        />
        <div class="absolute bottom-8px left-8px rounded bg-black/50 px-8px py-4px text-xs text-white">
          坐标: {{ cursorX.toFixed(2) }}m, {{ cursorY.toFixed(2) }}m
        </div>
      </div>

      <PropertyPanel
        class="w-380px flex-shrink-0"
        :editor-data="editor.editorData.value"
        :selected-element="editor.selectedElement.value"
        :resolution="editor.resolution.value"
        :scene-list="editor.sceneList.value"
        :selected-map-id="editor.selectedMapId.value"
        @update-element="handleUpdateElement"
        @remove-element="editor.removeElement"
        @select-scene="handleSelectMap"
        @add-scene="handleAddScene"
        @delete-scene="handleDeleteScene"
        @locate-robot="handleLocateRobot"
      />
    </div>

    <!-- Add scene dialog -->
    <NModal v-model:show="addDialogVisible" preset="dialog" title="新增场景" positive-text="确定" negative-text="取消" @positive-click="confirmAddScene">
      <NForm label-placement="left" label-width="80">
        <NFormItem label="场景名称">
          <NInput v-model:value="newMapName" placeholder="请输入场景名称" />
        </NFormItem>
      </NForm>
    </NModal>

    <NModal v-model:show="importDialogVisible" preset="dialog" title="导入JSON点位" positive-text="导入" negative-text="取消" @positive-click="confirmImportJson">
      <NInput
        v-model:value="importJsonText"
        type="textarea"
        :autosize="{ minRows: 12, maxRows: 18 }"
        placeholder="请粘贴包含 label、position、node、description 的 JSON 数组"
      />
      <div class="mt-8px text-xs text-gray-500">position 将按 [x, y, angle] 导入为接待点标注，导入后需点击保存。</div>
    </NModal>
  </div>
</template>
