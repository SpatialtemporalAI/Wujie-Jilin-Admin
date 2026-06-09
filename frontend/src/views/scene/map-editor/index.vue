<script setup lang="ts">
import { onMounted, ref } from 'vue';
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

function handleExport(format: 'png' | 'jpeg' | 'webp') {
  canvasRef.value?.exportCanvas(format);
}

function handleZoomChange(zoom: number) {
  zoomLevel.value = zoom;
}

function handleCursorPosition(x: number, y: number) {
  cursorX.value = x;
  cursorY.value = y;
}
</script>

<template>
  <div class="flex h-full flex-col">
    <EditorToolbar
      :drawing-mode="editor.drawingMode.value"
      :can-undo="editor.canUndo.value"
      :can-redo="editor.canRedo.value"
      :is-dirty="editor.isDirty.value"
      :saving="editor.saving.value"
      :zoom-level="zoomLevel"
      @update:drawing-mode="(m: DrawingMode) => (editor.drawingMode.value = m)"
      @undo="editor.undo()"
      @redo="editor.redo()"
      @save="editor.saveMap()"
      @export="handleExport"
      @zoom-in="canvasRef?.zoomIn()"
      @zoom-out="canvasRef?.zoomOut()"
      @zoom-reset="canvasRef?.zoomReset()"
    />

    <div class="flex flex-1 overflow-hidden">
      <div class="relative flex-1">
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
        class="w-320px flex-shrink-0"
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
  </div>
</template>
