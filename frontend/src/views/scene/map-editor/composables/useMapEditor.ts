import { reactive, ref, computed } from 'vue';
import { fetchGetEditorMapData, fetchSaveEditorData, fetchGetSceneMapList, fetchDeleteSceneMap } from '@/service/api/scene';
import { pixelToWorld, worldToPixel, pixelsDeltaToMeters, metersDeltaToPixels } from '@/utils/coordinate';

export type DrawingMode = 'select' | 'point-nav' | 'point-recv' | 'path' | 'rect-obstacle' | 'polygon-restricted';

export interface SelectedElement {
  type: 'annotation' | 'path' | 'object';
  id: number;
}

export interface HistoryEntry {
  key: string;
  type: 'undo' | 'redo' | 'current';
  index: number;
  description: string;
  timestamp: number;
}

const MAX_UNDO_LEVELS = 50;

export function useMapEditor() {
  const editorData = ref<Api.Scene.EditorMapData | null>(null);
  const selectedMapId = ref<number | null>(null);
  const selectedElement = ref<SelectedElement | null>(null);
  const drawingMode = ref<DrawingMode>('select');
  const gridSpacing = ref(5);
  const isDirty = ref(false);
  const loading = ref(false);
  const saving = ref(false);
  const sceneList = ref<Api.Scene.SceneMap[]>([]);

  const undoStack = ref<Array<{ snapshot: string; description: string; timestamp: number }>>([]);
  const redoStack = ref<Array<{ snapshot: string; description: string; timestamp: number }>>([]);

  const deletedAnnotationIds: Set<number> = new Set();
  const deletedPathIds: Set<number> = new Set();
  const deletedObjectIds: Set<number> = new Set();

  const resolution = computed(() => editorData.value?.map.resolution ?? 0.2);

  function pixelToMeterDelta(px: number): number {
    return pixelsDeltaToMeters(px, resolution.value);
  }

  function meterToPixelDelta(m: number): number {
    return metersDeltaToPixels(m, resolution.value);
  }

  function pixelToWorldCoords(px: number, py: number) {
    const map = editorData.value?.map;
    return pixelToWorld(px, py, map?.start_point_x ?? 0, map?.start_point_y ?? 0, resolution.value);
  }

  function worldToPixelCoords(wx: number, wy: number) {
    const map = editorData.value?.map;
    return worldToPixel(wx, wy, map?.start_point_x ?? 0, map?.start_point_y ?? 0, resolution.value);
  }

  async function loadSceneList() {
    try {
      const { data } = await fetchGetSceneMapList({ page: 1, page_size: 999, status: null, name: null, group_id: undefined });
      if (data) {
        sceneList.value = (data as any).records || data || [];
      }
    } catch {
      sceneList.value = [];
    }
  }

  async function loadMap(mapId: number) {
    loading.value = true;
    try {
      const { data } = await fetchGetEditorMapData(mapId);
      if (data) {
        editorData.value = data;
        selectedMapId.value = mapId;
        selectedElement.value = null;
        isDirty.value = false;
        undoStack.value = [];
        redoStack.value = [];
        deletedAnnotationIds.clear();
        deletedPathIds.clear();
        deletedObjectIds.clear();
      }
    } finally {
      loading.value = false;
    }
  }

  function snapshotCurrent() {
    return JSON.stringify({
      annotations: editorData.value?.annotations ?? [],
      paths: editorData.value?.paths ?? [],
      objects: editorData.value?.objects ?? [],
    });
  }

  function pushUndoSnapshot(description = '编辑操作') {
    if (!editorData.value) return;
    undoStack.value.push({
      snapshot: snapshotCurrent(),
      description,
      timestamp: Date.now(),
    });
    if (undoStack.value.length > MAX_UNDO_LEVELS) {
      undoStack.value.shift();
    }
    redoStack.value = [];
    isDirty.value = true;
  }

  function applySnapshot(entry: { snapshot: string; description: string; timestamp: number }) {
    const parsed = JSON.parse(entry.snapshot);
    editorData.value!.annotations = parsed.annotations;
    editorData.value!.paths = parsed.paths;
    editorData.value!.objects = parsed.objects;
    selectedElement.value = null;
    isDirty.value = true;
  }

  function undo() {
    if (!editorData.value || undoStack.value.length === 0) return;
    const entry = undoStack.value.pop()!;
    redoStack.value.push({
      snapshot: snapshotCurrent(),
      description: entry.description,
      timestamp: Date.now(),
    });
    applySnapshot(entry);
  }

  function redo() {
    if (!editorData.value || redoStack.value.length === 0) return;
    const entry = redoStack.value.pop()!;
    undoStack.value.push({
      snapshot: snapshotCurrent(),
      description: entry.description,
      timestamp: Date.now(),
    });
    applySnapshot(entry);
  }

  function jumpToHistoryStep(type: 'undo' | 'redo', index: number) {
    if (!editorData.value) return;
    const now = Date.now();
    type SnapshotEntry = { snapshot: string; description: string; timestamp: number };

    if (type === 'undo') {
      if (index < 0 || index >= undoStack.value.length) return;
      const oldUndo = undoStack.value;
      const target = oldUndo[index];
      const newRedoTop: SnapshotEntry[] = [];
      let currentSnap = snapshotCurrent();
      for (let i = oldUndo.length - 1; i >= index; i--) {
        newRedoTop.push({
          snapshot: currentSnap,
          description: oldUndo[i].description,
          timestamp: now,
        });
        currentSnap = oldUndo[i].snapshot;
      }
      undoStack.value = oldUndo.slice(0, index);
      redoStack.value = [...newRedoTop, ...redoStack.value];
      applySnapshot(target);
    } else {
      if (index < 0 || index >= redoStack.value.length) return;
      const oldRedo = redoStack.value;
      const target = oldRedo[index];
      const newUndoTop: SnapshotEntry[] = [];
      let currentSnap = snapshotCurrent();
      for (let i = oldRedo.length - 1; i >= index; i--) {
        newUndoTop.push({
          snapshot: currentSnap,
          description: oldRedo[i].description,
          timestamp: now,
        });
        currentSnap = oldRedo[i].snapshot;
      }
      undoStack.value = [...undoStack.value, ...newUndoTop];
      redoStack.value = oldRedo.slice(0, index);
      applySnapshot(target);
    }
  }

  const canUndo = computed(() => undoStack.value.length > 0);
  const canRedo = computed(() => redoStack.value.length > 0);
  const hasHistory = computed(() => undoStack.value.length > 0 || redoStack.value.length > 0);

  const historyList = computed(() => {
    const currentEntry = {
      key: 'current',
      type: 'current' as const,
      index: -1,
      description: '当前状态',
      timestamp: 0,
    };
    const undoItems = [...undoStack.value].reverse().map((entry, idx) => {
      const index = undoStack.value.length - 1 - idx;
      return {
        key: `undo-${index}`,
        type: 'undo' as const,
        index,
        description: entry.description,
        timestamp: entry.timestamp,
      };
    });
    const redoItems = redoStack.value.map((entry, index) => ({
      key: `redo-${index}`,
      type: 'redo' as const,
      index,
      description: entry.description,
      timestamp: entry.timestamp,
    }));
    return [...undoItems, currentEntry, ...redoItems];
  });

  function validateBeforeSave(): string[] {
    const errors: string[] = [];
    if (!editorData.value) {
      errors.push('未加载地图数据');
      return errors;
    }
    const annotations = editorData.value.annotations;
    if (annotations.length === 0) {
      return errors;
    }
    const hasNav = annotations.some(a => a.type === 'navigation' || a.type === '导航点');
    if (!hasNav) {
      errors.push('地图至少需要包含1个导航点');
    }
    const minDist = 0.5;
    for (let i = 0; i < annotations.length; i++) {
      for (let j = i + 1; j < annotations.length; j++) {
        const dx = Math.abs(annotations[i].x - annotations[j].x);
        const dy = Math.abs(annotations[i].y - annotations[j].y);
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < minDist) {
          errors.push(`标注 "${annotations[i].name}" 和 "${annotations[j].name}" 间距小于 ${minDist}m`);
          break;
        }
      }
      if (errors.length > 5) break;
    }
    return errors;
  }

  async function saveMap(options?: { silent?: boolean }): Promise<boolean> {
    if (!editorData.value || !selectedMapId.value) return false;
    const errors = validateBeforeSave();
    if (errors.length > 0) {
      window.$message?.error(errors[0]);
      return false;
    }
    saving.value = true;
    try {
      const existingIds = new Set([
        ...editorData.value.annotations.map(a => a.id),
        ...editorData.value.paths.map(p => p.id),
        ...editorData.value.objects.map(o => o.id),
      ]);

      await fetchSaveEditorData(selectedMapId.value, {
        annotations: editorData.value.annotations.map(a => ({
          id: a.id > 0 ? a.id : null,
          x: a.x,
          y: a.y,
          name: a.name,
          angle: a.angle,
          type: a.type,
        })),
        paths: editorData.value.paths.map(p => ({
          id: p.id > 0 ? p.id : null,
          start_annotation_id: p.start_annotation_id,
          end_annotation_id: p.end_annotation_id,
          name: p.name,
          points: p.points,
        })),
        objects: editorData.value.objects.map(o => ({
          id: o.id > 0 ? o.id : null,
          type: o.type,
          x: o.x,
          y: o.y,
          width: o.width,
          height: o.height,
          points: o.points,
        })),
        deleted_annotation_ids: [...deletedAnnotationIds],
        deleted_path_ids: [...deletedPathIds],
        deleted_object_ids: [...deletedObjectIds],
      });

      deletedAnnotationIds.clear();
      deletedPathIds.clear();
      deletedObjectIds.clear();

      isDirty.value = false;
      if (!options?.silent) {
        window.$message?.success('保存成功');
      }
      return true;
    } catch (e: any) {
      window.$message?.error(e?.message || '保存失败');
      return false;
    } finally {
      saving.value = false;
    }
  }

  async function deleteScene(id: number) {
    await fetchDeleteSceneMap(id);
    if (selectedMapId.value === id) {
      editorData.value = null;
      selectedMapId.value = null;
      selectedElement.value = null;
    }
    await loadSceneList();
    window.$message?.success('删除成功');
  }

  function createAnnotation(annotation: { x: number; y: number; name: string; angle: number; type: string }, id: number) {
    return {
      id,
      map_id: selectedMapId.value!,
      x: annotation.x,
      y: annotation.y,
      name: annotation.name,
      angle: annotation.angle,
      type: annotation.type,
      created_by: '',
      updated_by: '',
      status: null,
      created_at: null,
      updated_at: null,
    } as unknown as Api.Scene.SceneMapAnnotation;
  }

  function addAnnotation(annotation: { x: number; y: number; name: string; angle: number; type: string }) {
    if (!editorData.value) return;
    const label = annotation.type === 'navigation' ? '导航点' : '接待点';
    pushUndoSnapshot(`添加${label}「${annotation.name}」`);
    const newId = -(Date.now());
    editorData.value.annotations.push(createAnnotation(annotation, newId));
    return newId;
  }

  function addAnnotations(annotations: { x: number; y: number; name: string; angle: number; type: string }[]) {
    if (!editorData.value || annotations.length === 0) return;
    pushUndoSnapshot(`批量添加${annotations.length}个点位`);
    const baseId = Date.now();
    editorData.value.annotations.push(...annotations.map((annotation, index) => createAnnotation(annotation, -(baseId + index))));
  }

  function addPath(path: { start_annotation_id: number; end_annotation_id: number; name?: string; points?: string | null }) {
    if (!editorData.value) return;
    pushUndoSnapshot('添加路径');
    const newId = -(Date.now());
    const newItem = {
      id: newId,
      map_id: selectedMapId.value!,
      start_annotation_id: path.start_annotation_id,
      end_annotation_id: path.end_annotation_id,
      name: path.name ?? null,
      points: path.points ?? null,
      created_by: '',
      updated_by: '',
      status: null,
      created_at: null,
      updated_at: null,
    } as unknown as Api.Scene.SceneMapPath;
    editorData.value.paths.push(newItem);
    return newId;
  }

  function addObject(obj: { type: string; x: number; y: number; width: number; height: number; points: string | null }) {
    if (!editorData.value) return;
    const label = obj.type === 'restricted' ? '禁区' : '障碍物';
    pushUndoSnapshot(`添加${label}`);
    const newId = -(Date.now());
    const newItem = {
      id: newId,
      map_id: selectedMapId.value!,
      type: obj.type,
      x: obj.x,
      y: obj.y,
      width: obj.width,
      height: obj.height,
      points: obj.points,
      created_by: '',
      updated_by: '',
      status: null,
      created_at: null,
      updated_at: null,
    } as unknown as Api.Scene.SceneMapObject;
    editorData.value.objects.push(newItem);
    return newId;
  }

  function removeElement(type: 'annotation' | 'path' | 'object', id: number) {
    if (!editorData.value) return;
    const typeLabel = type === 'annotation' ? '点位' : type === 'path' ? '路径' : '物体';
    pushUndoSnapshot(`删除${typeLabel}`);
    if (type === 'annotation') {
      if (id > 0) deletedAnnotationIds.add(id);
      const removedPaths = editorData.value.paths.filter(
        p => p.start_annotation_id === id || p.end_annotation_id === id
      );
      removedPaths.forEach(p => { if (p.id > 0) deletedPathIds.add(p.id); });
      editorData.value.annotations = editorData.value.annotations.filter(a => a.id !== id);
      editorData.value.paths = editorData.value.paths.filter(
        p => p.start_annotation_id !== id && p.end_annotation_id !== id
      );
    } else if (type === 'path') {
      if (id > 0) deletedPathIds.add(id);
      editorData.value.paths = editorData.value.paths.filter(p => p.id !== id);
    } else if (type === 'object') {
      if (id > 0) deletedObjectIds.add(id);
      editorData.value.objects = editorData.value.objects.filter(o => o.id !== id);
    }
    if (selectedElement.value?.id === id) {
      selectedElement.value = null;
    }
  }

  function updateElement(type: 'annotation' | 'path' | 'object', id: number, data: Record<string, any>) {
    if (!editorData.value) return;
    let list: any[];
    if (type === 'annotation') {
      list = editorData.value.annotations;
    } else if (type === 'path') {
      list = editorData.value.paths;
    } else {
      list = editorData.value.objects;
    }
    const item = list.find((i: any) => i.id === id);
    if (!item) return;

    // 仅名称修改不单独记录历史（避免每次按键都产生一条）
    const isNameOnlyEdit = Object.keys(data).length === 1 && 'name' in data;
    if (!isNameOnlyEdit) {
      const typeLabel = type === 'annotation' ? '点位' : type === 'path' ? '路径' : '物体';
      const name = (item as any).name;
      const suffix = name ? `「${name}」` : '';
      const moved = 'x' in data && 'y' in data;
      const resized = type === 'object' && ('width' in data || 'height' in data);
      let action = '修改属性';
      if (moved) action = '移动';
      else if (resized) action = '调整尺寸';
      else if ('type' in data && type === 'annotation') action = '修改类型';
      pushUndoSnapshot(`${action}${typeLabel}${suffix}`);
    }
    Object.assign(item, data);
  }

  return {
    editorData,
    selectedMapId,
    selectedElement,
    drawingMode,
    gridSpacing,
    isDirty,
    loading,
    saving,
    sceneList,
    resolution,
    canUndo,
    canRedo,
    hasHistory,
    historyList,
    pixelToMeterDelta,
    meterToPixelDelta,
    pixelToWorldCoords,
    worldToPixelCoords,
    loadSceneList,
    loadMap,
    undo,
    redo,
    jumpToHistoryStep,
    saveMap,
    deleteScene,
    addAnnotation,
    addAnnotations,
    addPath,
    addObject,
    removeElement,
    updateElement,
    pushUndoSnapshot,
    validateBeforeSave,
  };
}
