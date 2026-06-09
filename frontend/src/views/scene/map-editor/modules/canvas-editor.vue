<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { Canvas, Circle, Rect, Polygon, Line, Group, Text, FabricImage, Triangle, Point } from 'fabric';
import { getFilePreviewUrl } from '@/service/api/file';
import type { SelectedElement, DrawingMode } from '../composables/useMapEditor';

interface Props {
  editorData: Api.Scene.EditorMapData | null;
  selectedElement: SelectedElement | null;
  drawingMode: DrawingMode;
  gridSpacing: number;
  resolution: number;
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
});

const emit = defineEmits<{
  (e: 'select-element', el: SelectedElement | null): void;
  (e: 'add-annotation', data: { x: number; y: number; type: string }): void;
  (e: 'add-path', data: { startId: number; endId: number }): void;
  (e: 'add-object', data: { type: string; x: number; y: number; width: number; height: number; points?: string }): void;
  (e: 'update-element', data: { type: string; id: number; updates: Record<string, any> }): void;
  (e: 'zoom-change', zoom: number): void;
  (e: 'cursor-position', x: number, y: number): void;
}>();

const canvasContainer = ref<HTMLDivElement>();
const canvasEl = ref<HTMLCanvasElement>();
let fabricCanvas: Canvas | null = null;
let gridGroup: Group | null = null;
let elementMap: Map<string, any> = new Map();

const MIN_ZOOM = 0.1;
const MAX_ZOOM = 5;
let currentZoom = 1;
let isPanning = false;
let lastPanPoint = { x: 0, y: 0 };
let spacePressed = false;

let pathStartAnnotationId: number | null = null;

let drawingState: {
  type: 'rect' | 'polygon' | null;
  startX: number;
  startY: number;
  tempObj: any;
  polygonPoints: { x: number; y: number }[];
} | null = null;

const canvasWidth = ref(800);
const canvasHeight = ref(600);

function setElementData(obj: any, data: { type: string; id: number }) {
  (obj as any)._elementData = data;
}

function getElementData(obj: any): { type: string; id: number } | null {
  return (obj as any)._elementData || null;
}

function getElementKey(type: string, id: number) {
  return `${type}-${id}`;
}

function renderElements() {
  if (!fabricCanvas || !props.editorData) return;

  const existingKeys = new Set<string>();

  for (const ann of props.editorData.annotations) {
    const key = getElementKey('annotation', ann.id);
    existingKeys.add(key);

    if (elementMap.has(key)) {
      const group = elementMap.get(key);
      group.set({ left: ann.x, top: ann.y });
      const circle = group.getObjects()[0] as Circle;
      circle.set('fill', ann.type === 'navigation' || ann.type === '导航点' ? '#3b82f6' : '#22c55e');
      const text = group.getObjects()[2] as Text;
      text.set('text', ann.name);
      const angleIndicator = group.getObjects()[1] as Triangle;
      angleIndicator.set('angle', ann.angle);
    } else {
      const isNav = ann.type === 'navigation' || ann.type === '导航点';
      const color = isNav ? '#3b82f6' : '#22c55e';

      const circle = new Circle({
        radius: 8,
        fill: color,
        stroke: '#fff',
        strokeWidth: 2,
        originX: 'center',
        originY: 'center',
      });

      const angleIndicator = new Triangle({
        width: 8,
        height: 12,
        fill: color,
        originX: 'center',
        originY: 'center',
        top: -16,
        angle: ann.angle || 0,
      });

      const text = new Text(ann.name, {
        fontSize: 10,
        fill: '#333',
        originX: 'center',
        originY: 'center',
        top: 18,
        fontFamily: 'sans-serif',
      });

      const group = new Group([circle, angleIndicator, text], {
        left: ann.x,
        top: ann.y,
        originX: 'center',
        originY: 'center',
        hasControls: false,
      });
      setElementData(group, { type: 'annotation', id: ann.id });

      fabricCanvas.add(group);
      elementMap.set(key, group);
    }
  }

  for (const path of props.editorData.paths) {
    const key = getElementKey('path', path.id);
    existingKeys.add(key);

    const startAnn = props.editorData.annotations.find(a => a.id === path.start_annotation_id);
    const endAnn = props.editorData.annotations.find(a => a.id === path.end_annotation_id);
    if (!startAnn || !endAnn) continue;

    if (elementMap.has(key)) {
      const line = elementMap.get(key);
      line.set({ x1: startAnn.x, y1: startAnn.y, x2: endAnn.x, y2: endAnn.y });
    } else {
      const line = new Line([startAnn.x, startAnn.y, endAnn.x, endAnn.y], {
        stroke: '#f97316',
        strokeWidth: 3,
        selectable: false,
        evented: false,
      });
      setElementData(line, { type: 'path', id: path.id });
      fabricCanvas.add(line);
      fabricCanvas.sendObjectToBack(line);
      elementMap.set(key, line);
    }
  }

  for (const obj of props.editorData.objects) {
    const key = getElementKey('object', obj.id);
    existingKeys.add(key);

    const isRestricted = obj.type === 'restricted' || obj.type === '禁区';
    const fillColor = isRestricted ? 'rgba(234, 179, 8, 0.3)' : 'rgba(239, 68, 68, 0.3)';
    const strokeColor = isRestricted ? '#eab308' : '#ef4444';

    if (elementMap.has(key)) {
      const fabricObj = elementMap.get(key);
      fabricObj.set({ left: obj.x, top: obj.y });
      if (fabricObj instanceof Rect) {
        fabricObj.set({ width: obj.width, height: obj.height });
      }
    } else {
      if (obj.points) {
        try {
          const pts = JSON.parse(obj.points);
          const polygon = new Polygon(pts, {
            left: obj.x, top: obj.y,
            fill: fillColor, stroke: strokeColor, strokeWidth: 2,
          });
          setElementData(polygon, { type: 'object', id: obj.id });
          fabricCanvas.add(polygon);
          elementMap.set(key, polygon);
        } catch { /* skip invalid polygon */ }
      } else {
        const rect = new Rect({
          left: obj.x, top: obj.y,
          width: obj.width || 40, height: obj.height || 40,
          fill: fillColor, stroke: strokeColor, strokeWidth: 2,
        });
        setElementData(rect, { type: 'object', id: obj.id });
        fabricCanvas.add(rect);
        elementMap.set(key, rect);
      }
    }
  }

  for (const [key, obj] of elementMap) {
    if (!existingKeys.has(key)) {
      fabricCanvas.remove(obj);
      elementMap.delete(key);
    }
  }

  updateSelection();
  fabricCanvas.renderAll();
}

function updateSelection() {
  if (!fabricCanvas) return;
  fabricCanvas.discardActiveObject();
  if (props.selectedElement) {
    const key = getElementKey(props.selectedElement.type, props.selectedElement.id);
    const obj = elementMap.get(key);
    if (obj) fabricCanvas.setActiveObject(obj);
  }
  fabricCanvas.renderAll();
}

function renderGrid() {
  if (!fabricCanvas) return;
  if (gridGroup) fabricCanvas.remove(gridGroup);

  const allLines: Line[] = [];
  const w = canvasWidth.value;
  const h = canvasHeight.value;
  const spacingPx = props.gridSpacing / props.resolution;
  if (spacingPx <= 0) return;

  for (let x = spacingPx; x < w; x += spacingPx) {
    allLines.push(new Line([x, 0, x, h], { stroke: 'rgba(0,0,0,0.08)', strokeWidth: 1, selectable: false, evented: false }));
  }
  for (let y = spacingPx; y < h; y += spacingPx) {
    allLines.push(new Line([0, y, w, y], { stroke: 'rgba(0,0,0,0.08)', strokeWidth: 1, selectable: false, evented: false }));
  }

  gridGroup = new Group(allLines, { selectable: false, evented: false, objectCaching: false });
  fabricCanvas.add(gridGroup);
  fabricCanvas.sendObjectToBack(gridGroup);
  fabricCanvas.renderAll();
}

async function loadBackgroundImage(imageId: number) {
  if (!fabricCanvas) return;
  const url = getFilePreviewUrl(imageId);
  try {
    const img = await FabricImage.fromURL(url, { crossOrigin: 'anonymous' });
    canvasWidth.value = img.width || 800;
    canvasHeight.value = img.height || 600;
    fabricCanvas.setDimensions({ width: canvasWidth.value, height: canvasHeight.value });
    fabricCanvas.backgroundImage = img;
    fabricCanvas.renderAll();
    renderGrid();
  } catch (e) {
    console.error('Failed to load background image:', e);
  }
}

function handleMouseDown(opt: any) {
  if (!fabricCanvas) return;
  const evt = opt.e as MouseEvent;

  if (spacePressed || evt.button === 1) {
    isPanning = true;
    lastPanPoint = { x: evt.clientX, y: evt.clientY };
    fabricCanvas.selection = false;
    return;
  }

  if (props.drawingMode === 'select') return;

  const pointer = fabricCanvas.getViewportPoint(evt);
  const x = pointer.x;
  const y = pointer.y;

  if (props.drawingMode === 'point-nav') {
    emit('add-annotation', { x, y, type: 'navigation' });
    return;
  }
  if (props.drawingMode === 'point-recv') {
    emit('add-annotation', { x, y, type: 'reception' });
    return;
  }
  if (props.drawingMode === 'path') {
    const clickedAnnotation = findAnnotationAtPoint(x, y);
    if (clickedAnnotation) {
      if (pathStartAnnotationId === null) {
        pathStartAnnotationId = clickedAnnotation.id;
        window.$message?.info('已选择起始点位，请点击终点');
      } else if (clickedAnnotation.id !== pathStartAnnotationId) {
        emit('add-path', { startId: pathStartAnnotationId, endId: clickedAnnotation.id });
        pathStartAnnotationId = null;
      }
    }
    return;
  }
  if (props.drawingMode === 'rect-obstacle') {
    drawingState = { type: 'rect', startX: x, startY: y, tempObj: null, polygonPoints: [] };
    return;
  }
  if (props.drawingMode === 'polygon-restricted') {
    if (!drawingState || drawingState.type !== 'polygon') {
      drawingState = { type: 'polygon', startX: 0, startY: 0, tempObj: null, polygonPoints: [{ x, y }] };
      window.$message?.info('单击添加顶点，双击闭合多边形');
    } else {
      drawingState.polygonPoints.push({ x, y });
    }
    return;
  }
}

function handleMouseMove(opt: any) {
  if (!fabricCanvas) return;
  const evt = opt.e as MouseEvent;
  const pointer = fabricCanvas.getViewportPoint(evt);
  emit('cursor-position', pointer.x * props.resolution, pointer.y * props.resolution);

  if (isPanning) {
    const dx = evt.clientX - lastPanPoint.x;
    const dy = evt.clientY - lastPanPoint.y;
    fabricCanvas.relativePan(new Point(dx, dy));
    lastPanPoint = { x: evt.clientX, y: evt.clientY };
    return;
  }

  if (drawingState?.type === 'rect' && drawingState.tempObj) {
    const w = pointer.x - drawingState.startX;
    const h = pointer.y - drawingState.startY;
    drawingState.tempObj.set({
      width: Math.abs(w), height: Math.abs(h),
      left: Math.min(drawingState.startX, pointer.x),
      top: Math.min(drawingState.startY, pointer.y),
    });
    fabricCanvas.renderAll();
  }
}

function handleMouseUp(opt: any) {
  if (isPanning) {
    isPanning = false;
    if (fabricCanvas) fabricCanvas.selection = true;
    return;
  }
  if (drawingState?.type === 'rect' && fabricCanvas) {
    const pointer = fabricCanvas.getViewportPoint(opt.e);
    const x = Math.min(drawingState.startX, pointer.x);
    const y = Math.min(drawingState.startY, pointer.y);
    const w = Math.abs(pointer.x - drawingState.startX);
    const h = Math.abs(pointer.y - drawingState.startY);
    if (drawingState.tempObj) fabricCanvas.remove(drawingState.tempObj);
    if (w > 5 && h > 5) {
      emit('add-object', { type: 'obstacle', x, y, width: w, height: h });
    }
    drawingState = null;
  }
}

function handleDoubleClick() {
  if (drawingState?.type === 'polygon' && fabricCanvas) {
    const pts = drawingState.polygonPoints;
    if (pts.length >= 3) {
      if (drawingState.tempObj) fabricCanvas.remove(drawingState.tempObj);
      const minX = Math.min(...pts.map(p => p.x));
      const minY = Math.min(...pts.map(p => p.y));
      emit('add-object', { type: 'restricted', x: minX, y: minY, width: 0, height: 0, points: JSON.stringify(pts) });
    }
    drawingState = null;
  }
}

function handleObjectMoved(opt: any) {
  const obj = opt.target;
  if (!obj) return;
  const data = getElementData(obj);
  if (!data) return;
  const updates: Record<string, any> = { x: obj.left, y: obj.top };
  if (data.type === 'object' && obj instanceof Rect) {
    updates.width = obj.width * obj.scaleX;
    updates.height = obj.height * obj.scaleY;
    obj.set({ scaleX: 1, scaleY: 1 });
  }
  emit('update-element', { type: data.type, id: data.id, updates });
}

function handleObjectSelected(opt: any) {
  if (opt.selected && opt.selected.length > 0) {
    const data = getElementData(opt.selected[0]);
    if (data) emit('select-element', { type: data.type as 'annotation' | 'path' | 'object', id: data.id });
  }
}

function handleSelectionCleared() {
  emit('select-element', null);
}

function handleMouseWheel(opt: any) {
  if (!fabricCanvas) return;
  const evt = opt.e as WheelEvent;
  evt.preventDefault();
  evt.stopPropagation();

  const delta = evt.deltaY;
  let zoom = fabricCanvas.getZoom();
  zoom *= 0.999 ** delta;
  zoom = Math.min(Math.max(zoom, MIN_ZOOM), MAX_ZOOM);
  fabricCanvas.zoomToPoint(new Point(evt.clientX, evt.clientY), zoom);
  currentZoom = zoom;
  emit('zoom-change', zoom);
}

function findAnnotationAtPoint(x: number, y: number): Api.Scene.SceneMapAnnotation | null {
  if (!props.editorData) return null;
  const threshold = 15;
  for (const ann of props.editorData.annotations) {
    if (Math.abs(ann.x - x) < threshold && Math.abs(ann.y - y) < threshold) return ann;
  }
  return null;
}

function handleKeyDown(evt: KeyboardEvent) {
  if (evt.code === 'Space') { spacePressed = true; evt.preventDefault(); }
}

function handleKeyUp(evt: KeyboardEvent) {
  if (evt.code === 'Space') spacePressed = false;
}

function setupCanvas() {
  if (!canvasEl.value) return;
  fabricCanvas = new Canvas(canvasEl.value, {
    selection: true,
    preserveObjectStacking: true,
    width: canvasWidth.value,
    height: canvasHeight.value,
  });
  fabricCanvas.on('mouse:down', handleMouseDown);
  fabricCanvas.on('mouse:move', handleMouseMove);
  fabricCanvas.on('mouse:up', handleMouseUp);
  fabricCanvas.on('mouse:dblclick', handleDoubleClick);
  fabricCanvas.on('mouse:wheel', handleMouseWheel);
  fabricCanvas.on('object:moving', handleObjectMoved);
  fabricCanvas.on('selection:created', handleObjectSelected);
  fabricCanvas.on('selection:updated', handleObjectSelected);
  fabricCanvas.on('selection:cleared', handleSelectionCleared);
}

function disposeCanvas() {
  if (fabricCanvas) { fabricCanvas.dispose(); fabricCanvas = null; }
  elementMap.clear();
}

watch(() => props.editorData, (newData) => {
  if (!newData) return;
  if (newData.map.image_id) {
    loadBackgroundImage(newData.map.image_id);
  } else {
    canvasWidth.value = newData.map.width || 800;
    canvasHeight.value = newData.map.height || 600;
    if (fabricCanvas) fabricCanvas.setDimensions({ width: canvasWidth.value, height: canvasHeight.value });
  }
  nextTick(() => renderElements());
}, { deep: false });

watch(() => props.editorData?.annotations, () => renderElements(), { deep: true });
watch(() => props.editorData?.paths, () => renderElements(), { deep: true });
watch(() => props.editorData?.objects, () => renderElements(), { deep: true });
watch(() => props.selectedElement, () => updateSelection());
watch(() => props.gridSpacing, () => renderGrid());
watch(() => props.drawingMode, (mode) => {
  pathStartAnnotationId = null;
  drawingState = null;
  if (fabricCanvas) {
    fabricCanvas.selection = mode === 'select';
    fabricCanvas.defaultCursor = mode === 'select' ? 'default' : 'crosshair';
  }
});

onMounted(() => {
  setupCanvas();
  window.addEventListener('keydown', handleKeyDown);
  window.addEventListener('keyup', handleKeyUp);
});

onBeforeUnmount(() => {
  disposeCanvas();
  window.removeEventListener('keydown', handleKeyDown);
  window.removeEventListener('keyup', handleKeyUp);
});

function exportCanvas(format: 'png' | 'jpeg' | 'webp') {
  if (!fabricCanvas) return;
  if (gridGroup) gridGroup.set('visible', false);
  fabricCanvas.renderAll();
  const dataUrl = fabricCanvas.toDataURL({ format, quality: 1, multiplier: 2 });
  if (gridGroup) gridGroup.set('visible', true);
  fabricCanvas.renderAll();
  const link = document.createElement('a');
  link.download = `map-export.${format === 'jpeg' ? 'jpg' : format}`;
  link.href = dataUrl;
  link.click();
}

function zoomIn() {
  if (!fabricCanvas) return;
  let zoom = Math.min(fabricCanvas.getZoom() * 1.2, MAX_ZOOM);
  fabricCanvas.zoomToPoint(fabricCanvas.getCenterPoint(), zoom);
  currentZoom = zoom;
  emit('zoom-change', zoom);
}

function zoomOut() {
  if (!fabricCanvas) return;
  let zoom = Math.max(fabricCanvas.getZoom() / 1.2, MIN_ZOOM);
  fabricCanvas.zoomToPoint(fabricCanvas.getCenterPoint(), zoom);
  currentZoom = zoom;
  emit('zoom-change', zoom);
}

function zoomReset() {
  if (!fabricCanvas) return;
  fabricCanvas.setViewportTransform([1, 0, 0, 1, 0, 0]);
  currentZoom = 1;
  emit('zoom-change', 1);
}

defineExpose({ exportCanvas, zoomIn, zoomOut, zoomReset });
</script>

<template>
  <div ref="canvasContainer" class="relative h-full w-full overflow-hidden bg-gray-100">
    <canvas ref="canvasEl" />
    <div v-if="!editorData" class="absolute inset-0 flex items-center justify-center">
      <NEmpty description="请从左侧选择一个场景" />
    </div>
    <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white/60">
      <NSpin size="large" />
    </div>
  </div>
</template>
