import { reactive, ref, computed } from 'vue';
import { $t } from '@/locales';
import { fetchGetEditorMapData, fetchSaveEditorData, fetchGetSceneMapList, fetchDeleteSceneMap } from '@/service/api/scene';
import { pixelToWorld, worldToPixel, pixelsDeltaToMeters, metersDeltaToPixels } from '@/utils/coordinate';

export type DrawingMode = 'select';

export interface SelectedElement {
  type: 'annotation' | 'path' | 'object';
  id: number;
}

export interface HistoryEntry {
  key: string;
  index: number;
  description: string;
  timestamp: number;
  isCurrent: boolean;
  isFuture: boolean;
}

interface HistorySnapshot {
  snapshot: string;
  description: string;
  timestamp: number;
}

const MAX_HISTORY_LEVELS = 50;

export function useMapEditor() {
  const editorData = ref<Api.Scene.EditorMapData | null>(null);
  const selectedMapId = ref<number | null>(null);
  const selectedElement = ref<SelectedElement | null>(null);
  const drawingMode = ref<DrawingMode>('select');
  const isDirty = ref(false);
  const loading = ref(false);
  const saving = ref(false);
  const switching = ref(false);
  const sceneList = ref<Api.Scene.SceneMap[]>([]);

  const historyTimeline = ref<HistorySnapshot[]>([]);
  const currentStep = ref(-1);

  // 最近一次加载/保存后，服务端实际存在的真实 id 集合。
  // 保存时按 diff 计算删除列表、并据此判定新建/更新，使 undo/redo 还原的结果能正确落库。
  const serverAnnotationIds: Set<number> = new Set();
  const serverObjectIds: Set<number> = new Set();
  // 路径暂沿用显式删除集合（前端无路径新建入口）
  const deletedPathIds: Set<number> = new Set();

  const resolution = computed(() => editorData.value?.map.resolution ?? 0.2);

  function pixelToMeterDelta(px: number): number {
    return pixelsDeltaToMeters(px, resolution.value);
  }

  function meterToPixelDelta(m: number): number {
    return metersDeltaToPixels(m, resolution.value);
  }

  function pixelToWorldCoords(px: number, py: number) {
    const map = editorData.value?.map;
    const h = map?.height ?? 0;
    return pixelToWorld(px, h - py, map?.start_point_x ?? 0, map?.start_point_y ?? 0, resolution.value);
  }

  function worldToPixelCoords(wx: number, wy: number) {
    const map = editorData.value?.map;
    const h = map?.height ?? 0;
    const px = worldToPixel(wx, wy, map?.start_point_x ?? 0, map?.start_point_y ?? 0, resolution.value);
    return { x: px.x, y: h - px.y };
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

  async function loadMap(mapId: number): Promise<boolean> {
    loading.value = true;
    try {
      const { data, error } = await fetchGetEditorMapData(mapId);
      if (error || !data) {
        window.$message?.error($t('page.sceneMapEditor.loadMapFailed'));
        return false;
      }
      editorData.value = data;
      for (const ann of data.annotations) {
        const p = worldToPixelCoords(ann.x, ann.y);
        ann.x = p.x;
        ann.y = p.y;
      }
      selectedMapId.value = mapId;
      selectedElement.value = null;
      isDirty.value = false;
      historyTimeline.value = [{
        snapshot: snapshotCurrent(),
        description: '初始状态',
        timestamp: Date.now(),
      }];
      currentStep.value = 0;
      serverAnnotationIds.clear();
      serverObjectIds.clear();
      deletedPathIds.clear();
      for (const ann of data.annotations) {
        if (ann.id > 0) serverAnnotationIds.add(ann.id);
      }
      for (const obj of data.objects) {
        if (obj.id > 0) serverObjectIds.add(obj.id);
      }
      return true;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '';
      window.$message?.error(msg || $t('page.sceneMapEditor.loadMapFailed'));
      return false;
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

  function applySnapshot(entry: HistorySnapshot) {
    if (!editorData.value) return;
    const parsed = JSON.parse(entry.snapshot);
    editorData.value.annotations = parsed.annotations;
    editorData.value.paths = parsed.paths;
    editorData.value.objects = parsed.objects;
    const sel = selectedElement.value;
    if (sel) {
      const list = sel.type === 'annotation' ? editorData.value.annotations
        : sel.type === 'path' ? editorData.value.paths
        : editorData.value.objects;
      if (!list.some((i: any) => i.id === sel.id)) {
        selectedElement.value = null;
      }
    }
    isDirty.value = true;
  }

  function recordHistory(description: string) {
    if (!editorData.value) return;
    if (currentStep.value < historyTimeline.value.length - 1) {
      historyTimeline.value = historyTimeline.value.slice(0, currentStep.value + 1);
    }
    historyTimeline.value.push({
      snapshot: snapshotCurrent(),
      description,
      timestamp: Date.now(),
    });
    currentStep.value = historyTimeline.value.length - 1;
    while (historyTimeline.value.length > MAX_HISTORY_LEVELS + 1) {
      historyTimeline.value.shift();
      currentStep.value--;
    }
    isDirty.value = true;
  }

  /**
   * 保存回填真实 id 后，把历史快照里的临时 id 同步替换为真实 id。
   * 否则 undo/redo 会重新引入临时 id，再次保存时被当作新建 → 产生重复点位。
   */
  function remapHistoryIds(tempToReal: Map<number, number>) {
    if (tempToReal.size === 0) return;
    for (const entry of historyTimeline.value) {
      let parsed: any;
      try {
        parsed = JSON.parse(entry.snapshot);
      } catch {
        continue;
      }
      let changed = false;
      const mapIds = (list: any[] | undefined) => {
        if (!Array.isArray(list)) return list;
        return list.map((it: any) => {
          if (it && typeof it.id === 'number' && tempToReal.has(it.id)) {
            changed = true;
            return { ...it, id: tempToReal.get(it.id) };
          }
          return it;
        });
      };
      const annotations = mapIds(parsed.annotations);
      const objects = mapIds(parsed.objects);
      if (changed) {
        entry.snapshot = JSON.stringify({
          annotations,
          paths: parsed.paths ?? [],
          objects,
        });
      }
    }
  }

  function undo() {
    if (currentStep.value <= 0) return;
    currentStep.value--;
    applySnapshot(historyTimeline.value[currentStep.value]);
  }

  function redo() {
    if (currentStep.value >= historyTimeline.value.length - 1) return;
    currentStep.value++;
    applySnapshot(historyTimeline.value[currentStep.value]);
  }

  function jumpToStep(step: number) {
    if (step < 0 || step >= historyTimeline.value.length) return;
    if (step === currentStep.value) return;
    currentStep.value = step;
    applySnapshot(historyTimeline.value[step]);
  }

  const canUndo = computed(() => currentStep.value > 0);
  const canRedo = computed(() => currentStep.value < historyTimeline.value.length - 1);
  const hasHistory = computed(() => historyTimeline.value.length > 1);

  const historyList = computed(() =>
    historyTimeline.value.map((entry, index) => ({
      key: `step-${index}`,
      index,
      description: entry.description,
      timestamp: entry.timestamp,
      isCurrent: index === currentStep.value,
      isFuture: index > currentStep.value,
    }))
  );

  function validateBeforeSave(): { errors: string[]; warnings: string[] } {
    const errors: string[] = [];
    const warnings: string[] = [];
    if (!editorData.value) {
      errors.push('未加载地图数据');
      return { errors, warnings };
    }
    const annotations = editorData.value.annotations;
    if (annotations.length === 0) {
      return { errors, warnings };
    }
    const hasNav = annotations.some(a => a.type === 'navigation' || a.type === '返回点');
    if (!hasNav) {
      errors.push('地图至少需要包含1个返回点');
    }
    const minDist = 0.5;
    for (let i = 0; i < annotations.length; i++) {
      for (let j = i + 1; j < annotations.length; j++) {
        const dxPx = Math.abs(annotations[i].x - annotations[j].x);
        const dyPx = Math.abs(annotations[i].y - annotations[j].y);
        const distM = Math.sqrt(dxPx * dxPx + dyPx * dyPx) * resolution.value;
        if (distM < minDist) {
          warnings.push(`标注 "${annotations[i].name}" 和 "${annotations[j].name}" 间距小于 ${minDist}m`);
          break;
        }
      }
      if (warnings.length > 5) break;
    }
    return { errors, warnings };
  }

  async function saveMap(options?: { silent?: boolean }): Promise<boolean> {
    if (!editorData.value || !selectedMapId.value) return false;
    const { errors, warnings } = validateBeforeSave();
    if (errors.length > 0) {
      window.$message?.error(errors[0]);
      return false;
    }
    // 间距不足仅警告，不阻断保存
    if (!options?.silent) {
      warnings.forEach(w => window.$message?.warning(w));
    }
    saving.value = true;
    try {
      // 以"服务端已知真实 id"为基准判定新建/更新：id 在集合内 → 更新，否则 → 新建。
      // 这样被 undo 还原（已从服务端删除）或 redo 重新引入的元素都会被正确重建，而非静默丢失。
      const annotationPayload = editorData.value.annotations.map(a => {
        const w = pixelToWorldCoords(a.x, a.y);
        const isExisting = a.id > 0 && serverAnnotationIds.has(a.id);
        return {
          id: isExisting ? a.id : null,
          client_temp_id: isExisting ? null : a.id,
          x: w.x,
          y: w.y,
          name: a.name,
          angle: a.angle,
          type: a.type,
        };
      });
      const objectPayload = editorData.value.objects.map(o => {
        const isExisting = o.id > 0 && serverObjectIds.has(o.id);
        return {
          id: isExisting ? o.id : null,
          client_temp_id: isExisting ? null : o.id,
          type: o.type,
          name: o.name,
          x: o.x,
          y: o.y,
          width: o.width,
          height: o.height,
          points: o.points,
          angle: o.angle ?? 0,
        };
      });
      // 删除按 diff 计算：服务端有、当前编辑数据中没有的即视为删除。
      // 这样 undo（从编辑数据移除点位）后再次保存，才能真正把点位从服务端删除。
      const deletedAnnotationIds = [...serverAnnotationIds].filter(
        id => !editorData.value!.annotations.some(a => a.id === id)
      );
      const deletedObjectIds = [...serverObjectIds].filter(
        id => !editorData.value!.objects.some(o => o.id === id)
      );

      const resp = await fetchSaveEditorData(selectedMapId.value, {
        annotations: annotationPayload,
        paths: [],
        objects: objectPayload,
        deleted_annotation_ids: deletedAnnotationIds,
        deleted_path_ids: [...deletedPathIds],
        deleted_object_ids: deletedObjectIds,
      });

      // 回填新建元素的真实 id，避免再次保存时被当作新建导致重复插入
      const data = resp.data;
      const tempToReal = new Map<number, number>();
      if (data && editorData.value) {
        const selTempId = selectedElement.value?.id ?? null;
        const backfill = <T extends { id: number }>(list: T[], mappings: Api.Scene.CreatedIdMapping[]) => {
          const m = new Map(mappings.map(x => [x.temp_id, x.id]));
          for (const item of list) {
            const real = m.get(item.id);
            if (real !== undefined) {
              tempToReal.set(item.id, real);
              item.id = real;
            }
          }
        };
        backfill(editorData.value.annotations, data.created_annotations);
        backfill(editorData.value.objects, data.created_objects);
        // paths 当前始终提交 []，无需回填
        // 同步 selectedElement 指向的真实 id
        if (selTempId !== null && selTempId < 0 && selectedElement.value && tempToReal.has(selTempId)) {
          selectedElement.value = {
            type: selectedElement.value.type,
            id: tempToReal.get(selTempId)!,
          };
        }
      }

      // 刷新"服务端已知真实 id"集合为当前（回填后）的真实 id，并把历史快照里的临时 id
      // 同步替换为真实 id，保证后续 undo/redo 使用的都是真实 id，再次保存不会重复新建或漏删。
      serverAnnotationIds.clear();
      serverObjectIds.clear();
      deletedPathIds.clear();
      if (editorData.value) {
        for (const a of editorData.value.annotations) {
          if (a.id > 0) serverAnnotationIds.add(a.id);
        }
        for (const o of editorData.value.objects) {
          if (o.id > 0) serverObjectIds.add(o.id);
        }
      }
      remapHistoryIds(tempToReal);

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

  async function deleteScene(id: number): Promise<{ wasSelected: boolean }> {
    await fetchDeleteSceneMap(id);
    const wasSelected = selectedMapId.value === id;
    if (wasSelected) {
      editorData.value = null;
      selectedMapId.value = null;
      selectedElement.value = null;
      isDirty.value = false;
      historyTimeline.value = [];
      currentStep.value = -1;
      serverAnnotationIds.clear();
      serverObjectIds.clear();
      deletedPathIds.clear();
    }
    await loadSceneList();
    window.$message?.success($t('common.deleteSuccess'));
    return { wasSelected };
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
    const newId = -(Date.now());
    editorData.value.annotations.push(createAnnotation(annotation, newId));
    const label = annotation.type === 'navigation' ? '导航点' : '接待点';
    recordHistory(`添加${label}「${annotation.name}」`);
    return newId;
  }

  function addAnnotations(annotations: { x: number; y: number; name: string; angle: number; type: string }[]) {
    if (!editorData.value || annotations.length === 0) return;
    const baseId = Date.now();
    editorData.value.annotations.push(...annotations.map((annotation, index) => createAnnotation(annotation, -(baseId + index))));
    recordHistory(`批量添加${annotations.length}个点位`);
  }

  function addObject(obj: { type: string; name?: string | null; x: number; y: number; width: number; height: number; points: string | null; angle?: number }) {
    if (!editorData.value) return;
    const newId = -(Date.now());
    const newItem = {
      id: newId,
      map_id: selectedMapId.value!,
      type: obj.type,
      name: obj.name ?? null,
      x: obj.x,
      y: obj.y,
      width: obj.width,
      height: obj.height,
      points: obj.points,
      angle: obj.angle ?? 0,
      created_by: '',
      updated_by: '',
      status: null,
      created_at: null,
      updated_at: null,
    } as unknown as Api.Scene.SceneMapObject;
    editorData.value.objects.push(newItem);
    const label = obj.type === 'restricted' ? '禁区' : '障碍物';
    recordHistory(`添加${label}`);
    return newId;
  }

  function removeElement(type: 'annotation' | 'path' | 'object', id: number) {
    if (!editorData.value) return;
    const typeLabel = type === 'annotation' ? '点位' : type === 'path' ? '路径' : '物体';
    if (type === 'annotation') {
      // 点位的删除由保存时按 diff 计算（serverAnnotationIds - 当前），无需在此显式记录
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
      // 物体的删除同样由保存时按 diff 计算
      editorData.value.objects = editorData.value.objects.filter(o => o.id !== id);
    }
    if (selectedElement.value?.id === id) {
      selectedElement.value = null;
    }
    recordHistory(`删除${typeLabel}`);
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

    Object.assign(item, data);

    const typeLabel = type === 'annotation' ? '点位' : type === 'path' ? '路径' : '物体';
    const name = (item as any).name;
    const suffix = name ? `「${name}」` : '';
    const moved = 'x' in data && 'y' in data;
    const resized = type === 'object' && ('width' in data || 'height' in data);
    const renamed = Object.keys(data).length === 1 && 'name' in data;
    let action = '修改属性';
    if (renamed) action = '重命名';
    else if (moved) action = '移动';
    else if (resized) action = '调整尺寸';
    else if ('type' in data && type === 'annotation') action = '修改类型';
    recordHistory(`${action}${typeLabel}${suffix}`);
  }

  return {
    editorData,
    selectedMapId,
    selectedElement,
    drawingMode,
    isDirty,
    loading,
    saving,
    switching,
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
    jumpToStep,
    saveMap,
    deleteScene,
    addAnnotation,
    addAnnotations,
    addObject,
    removeElement,
    updateElement,
    recordHistory,
    validateBeforeSave,
  };
}
