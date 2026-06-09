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
let backgroundImgObj: FabricImage | null = null;
let elementMap: Map<string, any> = new Map();
let resizeObserver: ResizeObserver | null = null;

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
const containerWidth = ref(0);
const containerHeight = ref(0);

const sliderZoomValue = ref(50);

const sliderThemeOverrides = {
  fillColor: '#3b82f6',
  fillColorHover: '#2563eb',
  dotColor: '#3b82f6',
  dotBorder: '2px solid #fff',
  dotBoxShadow: '0 1px 4px rgba(0,0,0,0.2)',
};

function zoomToSliderValue(sliderVal: number): number {
  const minLog = Math.log(MIN_ZOOM);
  const maxLog = Math.log(MAX_ZOOM);
  const scale = (maxLog - minLog) / 100;
  return Math.exp(minLog + scale * sliderVal);
}

function sliderValueToZoom(zoom: number): number {
  const minLog = Math.log(MIN_ZOOM);
  const maxLog = Math.log(MAX_ZOOM);
  return Math.round(((Math.log(zoom) - minLog) / (maxLog - minLog)) * 100);
}

function setElementData(obj: any, data: { type: string; id: number }) {
  (obj as any)._elementData = data;
}

function getElementData(obj: any): { type: string; id: number } | null {
  return (obj as any)._elementData || null;
}

function getElementKey(type: string, id: number) {
  return `${type}-${id}`;
}

function centerContent() {
  if (!fabricCanvas) return;
  const cw = containerWidth.value;
  const ch = containerHeight.value;
  if (cw === 0 || ch === 0) return;

  const zoom = fabricCanvas.getZoom();
  const offsetX = (cw - canvasWidth.value * zoom) / 2;
  const offsetY = (ch - canvasHeight.value * zoom) / 2;

  fabricCanvas.setViewportTransform([
    zoom, 0, 0, zoom,
    Math.max(0, offsetX),
    Math.max(0, offsetY),
  ]);
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

  const allObjects: any[] = [];
  const w = canvasWidth.value;
  const h = canvasHeight.value;
  const spacingPx = props.gridSpacing / props.resolution;
  if (spacingPx <= 0) return;

  // Extend grid to cover the full visible area (beyond map content)
  const extend = 5000;
  const startX = Math.floor(-extend / spacingPx) * spacingPx;
  const startY = Math.floor(-extend / spacingPx) * spacingPx;
  const endX = w + extend;
  const endY = h + extend;

  // Vertical lines
  for (let x = startX; x <= endX; x += spacingPx) {
    const inBounds = x >= 0 && x <= w;
    allObjects.push(new Line([x, startY, x, endY], {
      stroke: inBounds ? 'rgba(0,0,0,0.08)' : 'rgba(0,0,0,0.03)',
      strokeWidth: 1,
      selectable: false,
      evented: false,
    }));
  }
  // Horizontal lines
  for (let y = startY; y <= endY; y += spacingPx) {
    const inBounds = y >= 0 && y <= h;
    allObjects.push(new Line([startX, y, endX, y], {
      stroke: inBounds ? 'rgba(0,0,0,0.08)' : 'rgba(0,0,0,0.03)',
      strokeWidth: 1,
      selectable: false,
      evented: false,
    }));
  }

  // Distance labels: show every N-th grid line to avoid clutter
  const labelInterval = Math.max(1, Math.ceil(80 / spacingPx));
  const labelStyle = {
    fontSize: 10,
    fill: 'rgba(0,0,0,0.35)',
    fontFamily: 'sans-serif',
    selectable: false,
    evented: false,
  };

  // X-axis labels along bottom edge (0 at left, increasing right)
  for (let i = 0; i * spacingPx <= endX; i++) {
    if (i % labelInterval !== 0) continue;
    const x = i * spacingPx;
    const meters = Math.round(x * props.resolution * 10) / 10;
    if (x >= startX && x <= endX) {
      allObjects.push(new Text(`${meters}`, {
        ...labelStyle,
        left: x,
        top: h + 4,
        originX: 'center',
        originY: 'top',
      }));
    }
  }
  // Y-axis labels along left edge (0 at bottom, increasing upward)
  for (let i = 0; i * spacingPx <= endY; i++) {
    if (i % labelInterval !== 0) continue;
    const y = i * spacingPx;
    const meters = Math.round((h - y) * props.resolution * 10) / 10;
    if (y >= startY && y <= endY) {
      allObjects.push(new Text(`${meters}`, {
        ...labelStyle,
        left: -4,
        top: y,
        originX: 'right',
        originY: 'center',
      }));
    }
  }

  gridGroup = new Group(allObjects, { selectable: false, evented: false, objectCaching: false });
  fabricCanvas.add(gridGroup);
  // Grid at the very bottom; image and other elements render above it
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

    // Remove previous background image object
    if (backgroundImgObj) {
      fabricCanvas.remove(backgroundImgObj);
      backgroundImgObj = null;
    }

    // Add image as a regular object at (0,0) so it follows viewport transform
    img.set({ left: 0, top: 0, originX: 'left', originY: 'top', selectable: false, evented: false });
    backgroundImgObj = img;
    fabricCanvas.add(img);

    fabricCanvas.setDimensions({
      width: containerWidth.value || canvasContainer.value!.clientWidth,
      height: containerHeight.value || canvasContainer.value!.clientHeight,
    });
    centerContent();
    fabricCanvas.renderAll();
    renderGrid();
    currentZoom = 1;
    sliderZoomValue.value = sliderValueToZoom(1);
    emit('zoom-change', 1);
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
  emit('cursor-position', pointer.x * props.resolution, (canvasHeight.value - pointer.y) * props.resolution);

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
  sliderZoomValue.value = sliderValueToZoom(zoom);
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
  if (!canvasEl.value || !canvasContainer.value) return;
  const cw = canvasContainer.value.clientWidth;
  const ch = canvasContainer.value.clientHeight;
  containerWidth.value = cw;
  containerHeight.value = ch;

  fabricCanvas = new Canvas(canvasEl.value, {
    selection: true,
    preserveObjectStacking: true,
    width: cw,
    height: ch,
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

  resizeObserver = new ResizeObserver((entries) => {
    for (const entry of entries) {
      containerWidth.value = entry.contentRect.width;
      containerHeight.value = entry.contentRect.height;
    }
  });
  resizeObserver.observe(canvasContainer.value);
}

function disposeCanvas() {
  if (resizeObserver) { resizeObserver.disconnect(); resizeObserver = null; }
  if (fabricCanvas) { fabricCanvas.dispose(); fabricCanvas = null; }
  elementMap.clear();
}

watch([containerWidth, containerHeight], () => {
  if (!fabricCanvas) return;
  fabricCanvas.setDimensions({ width: containerWidth.value, height: containerHeight.value });
  centerContent();
});

watch(() => props.editorData, (newData) => {
  if (!newData) return;
  if (newData.map.image_id) {
    loadBackgroundImage(newData.map.image_id);
  } else {
    canvasWidth.value = newData.map.width || 800;
    canvasHeight.value = newData.map.height || 600;
    if (fabricCanvas) {
      fabricCanvas.setDimensions({
        width: containerWidth.value || canvasContainer.value!.clientWidth,
        height: containerHeight.value || canvasContainer.value!.clientHeight,
      });
      centerContent();
    }
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
  const newZoom = Math.min(currentZoom * 1.2, MAX_ZOOM);
  const center = fabricCanvas.getCenterPoint();
  fabricCanvas.zoomToPoint(center, newZoom);
  currentZoom = newZoom;
  sliderZoomValue.value = sliderValueToZoom(newZoom);
  emit('zoom-change', newZoom);
}

function zoomOut() {
  if (!fabricCanvas) return;
  const newZoom = Math.max(currentZoom / 1.2, MIN_ZOOM);
  const center = fabricCanvas.getCenterPoint();
  fabricCanvas.zoomToPoint(center, newZoom);
  currentZoom = newZoom;
  sliderZoomValue.value = sliderValueToZoom(newZoom);
  emit('zoom-change', newZoom);
}

function zoomReset() {
  if (!fabricCanvas) return;
  const cw = containerWidth.value;
  const ch = containerHeight.value;
  const scaleX = cw / canvasWidth.value;
  const scaleY = ch / canvasHeight.value;
  const fitZoom = Math.min(scaleX, scaleY, 1);
  const offsetX = (cw - canvasWidth.value * fitZoom) / 2;
  const offsetY = (ch - canvasHeight.value * fitZoom) / 2;
  fabricCanvas.setViewportTransform([fitZoom, 0, 0, fitZoom, Math.max(0, offsetX), Math.max(0, offsetY)]);
  currentZoom = fitZoom;
  sliderZoomValue.value = sliderValueToZoom(fitZoom);
  emit('zoom-change', fitZoom);
}

function handleSliderZoom(val: number) {
  if (!fabricCanvas) return;
  const newZoom = zoomToSliderValue(val);
  const center = fabricCanvas.getCenterPoint();
  fabricCanvas.zoomToPoint(center, newZoom);
  currentZoom = newZoom;
  emit('zoom-change', newZoom);
}

defineExpose({ exportCanvas, zoomIn, zoomOut, zoomReset });
</script>

<template>
  <div ref="canvasContainer" class="relative h-full w-full overflow-hidden bg-gray-100">
    <canvas ref="canvasEl" />
    <div v-if="!editorData" class="absolute inset-0 flex items-center justify-center">
      <NEmpty description="请选择一个场景" />
    </div>
    <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white/60">
      <NSpin size="large" />
    </div>

    <!-- Zoom slider control -->
    <div v-if="editorData" class="absolute bottom-12px right-12px z-10 flex flex-col items-center gap-4px rounded-lg bg-white/90 px-6px py-8px shadow-md">
      <button
        class="flex h-24px w-24px items-center justify-center rounded-full text-sm font-bold text-blue-500 transition-colors hover:bg-blue-50"
        @click="zoomIn"
      >
        +
      </button>
      <NSlider
        v-model:value="sliderZoomValue"
        vertical
        :min="0"
        :max="100"
        :step="1"
        :tooltip="false"
        :theme-overrides="sliderThemeOverrides"
        class="!h-160px"
        @update:value="handleSliderZoom"
      />
      <button
        class="flex h-24px w-24px items-center justify-center rounded-full text-sm font-bold text-blue-500 transition-colors hover:bg-blue-50"
        @click="zoomOut"
      >
        -
      </button>
      <div class="text-xs text-gray-500">{{ Math.round(currentZoom * 100) }}%</div>
    </div>
  </div>
</template>
