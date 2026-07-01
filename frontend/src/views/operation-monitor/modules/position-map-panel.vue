<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { Canvas, Circle, Rect, Polygon, Line, Group, Text, FabricImage, Triangle, Ellipse, Pattern, Point } from 'fabric';
import { fetchGetEditorMapData } from '@/service/api/scene';
import { getFilePreviewUrl } from '@/service/api/file';
import { worldToPixel, radToDeg } from '@/utils/coordinate';
import type { ParsedLocation } from '../composables/useRobotMonitor';

interface Props {
  mapId: number | null;
  location: ParsedLocation | null;
  robotName: string;
}

const props = defineProps<Props>();

const canvasContainer = ref<HTMLDivElement>();
const canvasEl = ref<HTMLCanvasElement>();
let fabricCanvas: Canvas | null = null;
let backgroundImgObj: FabricImage | null = null;
let robotMarker: Group | null = null;
let elementMap: Map<string, any> = new Map();
let resizeObserver: ResizeObserver | null = null;
let restrictedPattern: Pattern | null = null;

const OBSTACLE_FILL = 'rgba(59, 130, 246, 0.3)';
const OBSTACLE_STROKE = '#3b82f6';
const RESTRICTED_STROKE = '#6b7280';
const POINT_FILL = '#22c55e';
const RETURN_POINT_FILL = '#047857';
// 点位圆形半径、方向箭头尺寸、名称垂直偏移（与地图编辑器保持一致）
const ANN_RADIUS = 8;
const ARROW_WIDTH = 6;
const ARROW_HEIGHT = 8;
const ANN_LABEL_OFFSET = 18;
// 机器人实时位置标记（红色圆点，与地图编辑器/图例保持一致）
const ROBOT_FILL = '#ef4444';
const ROBOT_STROKE = '#ffffff';

/**
 * 计算点位方向箭头的位置和旋转角度（ROS 弧度 → Fabric）
 * - ROS 弧度：0 朝东（右），π/2 朝北（上），逆时针为正
 * - Fabric Triangle 默认顶点朝上、顺时针为正
 * - 箭头底部贴合圆形边缘、顶点指向角度方向
 */
function getAnnotationArrowTransform(annX: number, annY: number, rosRad: number, radius: number) {
  const dist = radius + ARROW_HEIGHT / 2;
  return {
    x: annX + dist * Math.cos(rosRad),
    y: annY - dist * Math.sin(rosRad),
    angle: -radToDeg(rosRad) + 90,
  };
}

const canvasWidth = ref(800);
const canvasHeight = ref(600);
const containerWidth = ref(0);
const containerHeight = ref(0);
const mapLoading = ref(false);
const mapData = ref<Api.Scene.EditorMapData | null>(null);

const MIN_ZOOM = 0.5;
const MAX_ZOOM = 5;
const currentZoom = ref(1);
const sliderZoomValue = ref(0);

// 缩放滑块主题（与地图编辑器一致）
const sliderThemeOverrides = {
  fillColor: '#3b82f6',
  fillColorHover: '#2563eb',
  dotColor: '#3b82f6',
  dotBorder: '2px solid #fff',
  dotBoxShadow: '0 1px 4px rgba(0,0,0,0.2)',
};

/** 滑块值（0-100，对数刻度）→ 实际缩放倍率 */
function sliderToZoom(sliderVal: number): number {
  const minLog = Math.log(MIN_ZOOM);
  const maxLog = Math.log(MAX_ZOOM);
  const scale = (maxLog - minLog) / 100;
  return Math.exp(minLog + scale * sliderVal);
}

/** 实际缩放倍率 → 滑块值（0-100，对数刻度） */
function zoomToSlider(zoom: number): number {
  const minLog = Math.log(MIN_ZOOM);
  const maxLog = Math.log(MAX_ZOOM);
  return Math.round(((Math.log(zoom) - minLog) / (maxLog - minLog)) * 100);
}

function centerContent() {
  if (!fabricCanvas) return;
  const cw = containerWidth.value;
  const ch = containerHeight.value;
  if (cw === 0 || ch === 0) return;
  const zoom = fabricCanvas.getZoom();
  const offsetX = (cw - canvasWidth.value * zoom) / 2;
  const offsetY = (ch - canvasHeight.value * zoom) / 2;
  fabricCanvas.setViewportTransform([zoom, 0, 0, zoom, Math.max(0, offsetX), Math.max(0, offsetY)]);
}

function clearMapState() {
  mapData.value = null;
  for (const [, obj] of elementMap) {
    fabricCanvas?.remove(obj);
  }
  elementMap.clear();
  if (robotMarker) {
    fabricCanvas?.remove(robotMarker);
    robotMarker = null;
  }
  if (backgroundImgObj) {
    fabricCanvas?.remove(backgroundImgObj);
    backgroundImgObj = null;
  }
  fabricCanvas?.renderAll();
}

function createRestrictedPattern(): Pattern {
  const size = 8;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d')!;
  ctx.fillStyle = 'rgba(107, 114, 128, 0.12)';
  ctx.fillRect(0, 0, size, size);
  ctx.strokeStyle = 'rgba(107, 114, 128, 0.6)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, size);
  ctx.lineTo(size, 0);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(-size, size);
  ctx.lineTo(size, -size);
  ctx.stroke();
  return new Pattern({ source: canvas, repeat: 'repeat' });
}

function getRestrictedPattern(): Pattern {
  if (!restrictedPattern) restrictedPattern = createRestrictedPattern();
  return restrictedPattern;
}

function worldToCanvasPoint(wx: number, wy: number) {
  const mMap = mapData.value?.map;
  const h = mMap?.height ?? canvasHeight.value;
  const px = worldToPixel(wx, wy, mMap?.start_point_x ?? 0, mMap?.start_point_y ?? 0, mMap?.resolution ?? 0.2);
  return { x: px.x, y: h - px.y };
}

function renderElements() {
  if (!fabricCanvas || !mapData.value) return;
  const existingKeys = new Set<string>();

  for (const path of mapData.value.paths) {
    const key = `path-${path.id}`;
    existingKeys.add(key);
    const startAnn = mapData.value.annotations.find(a => a.id === path.start_annotation_id);
    const endAnn = mapData.value.annotations.find(a => a.id === path.end_annotation_id);
    if (!startAnn || !endAnn) continue;
    if (elementMap.has(key)) continue;
    const line = new Line([startAnn.x, startAnn.y, endAnn.x, endAnn.y], {
      stroke: '#f97316',
      strokeWidth: 3,
      selectable: false,
      evented: false
    });
    fabricCanvas.add(line);
    fabricCanvas.sendObjectToBack(line);
    elementMap.set(key, line);
  }

  for (const ann of mapData.value.annotations) {
    const circleKey = `ann-${ann.id}`;
    const arrowKey = `ann-arrow-${ann.id}`;
    const textKey = `ann-text-${ann.id}`;
    existingKeys.add(circleKey);
    existingKeys.add(arrowKey);
    existingKeys.add(textKey);

    const isReturnPoint = ann.type === 'navigation' || ann.type === '返回点';
    const color = isReturnPoint ? RETURN_POINT_FILL : POINT_FILL;
    const arrowTransform = getAnnotationArrowTransform(ann.x, ann.y, ann.angle || 0, ANN_RADIUS);

    // 圆点
    if (elementMap.has(circleKey)) {
      elementMap.get(circleKey).set({ left: ann.x, top: ann.y, fill: color });
    } else {
      const circle = new Circle({
        radius: ANN_RADIUS,
        fill: color,
        stroke: '#fff',
        strokeWidth: 2,
        originX: 'center',
        originY: 'center',
        left: ann.x,
        top: ann.y,
        selectable: false,
        evented: false
      });
      fabricCanvas.add(circle);
      elementMap.set(circleKey, circle);
    }

    // 角度方向箭头（顶点指向点位朝向）
    if (elementMap.has(arrowKey)) {
      elementMap.get(arrowKey).set({
        left: arrowTransform.x,
        top: arrowTransform.y,
        angle: arrowTransform.angle,
        fill: color
      });
    } else {
      const arrow = new Triangle({
        width: ARROW_WIDTH,
        height: ARROW_HEIGHT,
        fill: color,
        originX: 'center',
        originY: 'center',
        left: arrowTransform.x,
        top: arrowTransform.y,
        angle: arrowTransform.angle,
        selectable: false,
        evented: false
      });
      fabricCanvas.add(arrow);
      elementMap.set(arrowKey, arrow);
    }

    // 名称
    if (elementMap.has(textKey)) {
      const text = elementMap.get(textKey) as Text;
      text.set({ text: ann.name, fill: color, left: ann.x, top: ann.y + ANN_LABEL_OFFSET });
    } else {
      const text = new Text(ann.name, {
        fontSize: 10,
        fill: color,
        originX: 'center',
        originY: 'center',
        left: ann.x,
        top: ann.y + ANN_LABEL_OFFSET,
        fontFamily: 'sans-serif',
        fontWeight: 'bold',
        selectable: false,
        evented: false
      });
      fabricCanvas.add(text);
      elementMap.set(textKey, text);
    }
  }

  for (const obj of mapData.value.objects) {
    const key = `obj-${obj.id}`;
    existingKeys.add(key);
    const isRestricted = obj.type === 'restricted' || obj.type === '禁区';
    const fill = isRestricted ? getRestrictedPattern() : OBSTACLE_FILL;
    const stroke = isRestricted ? RESTRICTED_STROKE : OBSTACLE_STROKE;
    if (elementMap.has(key)) {
      const fabricObj = elementMap.get(key);
      fabricObj.set({ left: obj.x, top: obj.y, angle: obj.angle ?? 0 });
    } else {
      let fabricObj: Rect | Polygon | Triangle | Ellipse | null = null;
      if (obj.points) {
        try {
          fabricObj = new Polygon(JSON.parse(obj.points), {
            left: obj.x,
            top: obj.y,
            angle: obj.angle ?? 0,
            fill,
            stroke,
            strokeWidth: 2
          });
        } catch { /* skip */ }
      } else if (obj.type === 'obstacle-circle') {
        fabricObj = new Ellipse({
          left: obj.x,
          top: obj.y,
          angle: obj.angle ?? 0,
          rx: (obj.width || 10) / 2,
          ry: (obj.height || 10) / 2,
          fill,
          stroke,
          strokeWidth: 2
        });
      } else if (obj.type === 'obstacle-triangle') {
        fabricObj = new Triangle({
          left: obj.x,
          top: obj.y,
          angle: obj.angle ?? 0,
          width: obj.width || 10,
          height: obj.height || 10,
          fill,
          stroke,
          strokeWidth: 2
        });
      } else {
        const isSquare = obj.type === 'obstacle-square';
        fabricObj = new Rect({
          left: obj.x,
          top: obj.y,
          angle: obj.angle ?? 0,
          width: obj.width || 10,
          height: isSquare ? (obj.width || 10) : (obj.height || 10),
          fill,
          stroke,
          strokeWidth: 2
        });
      }
      if (fabricObj) {
        fabricObj.set({ selectable: false, evented: false });
        fabricCanvas.add(fabricObj);
        elementMap.set(key, fabricObj);
      }
    }
  }

  // Remove stale elements
  for (const [key, obj] of elementMap) {
    if (!existingKeys.has(key)) {
      fabricCanvas.remove(obj);
      elementMap.delete(key);
    }
  }

  fabricCanvas.renderAll();
}

function renderRobotMarker() {
  if (!fabricCanvas) return;

  if (robotMarker) {
    fabricCanvas.remove(robotMarker);
    robotMarker = null;
  }

  if (!props.location) return;

  const robotPx = worldToCanvasPoint(props.location.x, props.location.y);

  const body = new Circle({
    radius: 12,
    fill: ROBOT_FILL,
    stroke: ROBOT_STROKE,
    strokeWidth: 3,
    originX: 'center',
    originY: 'center'
  });

  const arrow = new Triangle({
    width: 10,
    height: 14,
    fill: '#fff',
    originX: 'center',
    originY: 'center',
    top: -20,
    angle: 0
  });

  const label = new Text(props.robotName || '机器人', {
    fontSize: 10,
    fill: ROBOT_FILL,
    originX: 'center',
    originY: 'center',
    top: 22,
    fontFamily: 'sans-serif',
    fontWeight: 'bold'
  });

  robotMarker = new Group([body, arrow, label], {
    left: robotPx.x,
    top: robotPx.y,
    originX: 'center',
    originY: 'center',
    angle: props.location.angle || 0,
    hasControls: false,
    selectable: false,
    evented: false
  });

  fabricCanvas.add(robotMarker);
  fabricCanvas.renderAll();
}

async function loadBackgroundImage(imageId: number) {
  if (!fabricCanvas) return;
  const url = getFilePreviewUrl(imageId);
  try {
    const img = await FabricImage.fromURL(url, { crossOrigin: 'anonymous' });
    canvasWidth.value = img.width || 800;
    canvasHeight.value = img.height || 600;

    if (backgroundImgObj) {
      fabricCanvas.remove(backgroundImgObj);
    }

    img.set({ left: 0, top: 0, originX: 'left', originY: 'top', selectable: false, evented: false });
    backgroundImgObj = img;
    fabricCanvas.add(img);
    fabricCanvas.sendObjectToBack(img);

    fabricCanvas.setDimensions({
      width: containerWidth.value || canvasContainer.value!.clientWidth,
      height: containerHeight.value || canvasContainer.value!.clientHeight
    });
    centerContent();
    fabricCanvas.renderAll();
    currentZoom.value = 1;
    sliderZoomValue.value = zoomToSlider(1);
  } catch (e) {
    console.error('Failed to load background image:', e);
  }
}

async function loadMapData(mapId: number) {
  mapLoading.value = true;
  try {
    const { data } = await fetchGetEditorMapData(mapId);
    if (!data) {
      clearMapState();
      return;
    }
    for (const ann of data.annotations) {
      const p = worldToPixel(ann.x, ann.y, data.map.start_point_x ?? 0, data.map.start_point_y ?? 0, data.map.resolution ?? 0.2);
      ann.x = p.x;
      ann.y = (data.map.height ?? canvasHeight.value) - p.y;
    }

    clearMapState();
    mapData.value = data;

    if (data.map.image_id) {
      await loadBackgroundImage(data.map.image_id);
    } else {
      canvasWidth.value = data.map.width || 800;
      canvasHeight.value = data.map.height || 600;
    }

    await nextTick();
    renderElements();
    renderRobotMarker();
  } catch (e) {
    console.error('Failed to load map data:', e);
  } finally {
    mapLoading.value = false;
  }
}

function handleMouseWheel(opt: any) {
  if (!fabricCanvas) return;
  const evt = opt.e as WheelEvent;
  evt.preventDefault();
  evt.stopPropagation();
  let zoom = fabricCanvas.getZoom();
  zoom *= 0.999 ** evt.deltaY;
  zoom = Math.min(Math.max(zoom, MIN_ZOOM), MAX_ZOOM);
  // offsetX/offsetY 是相对画布元素的坐标，clientX/clientY 是视口坐标；
  // 监控画布嵌在卡片内（有头部/内边距偏移），必须用画布相对坐标才能按鼠标位置缩放
  fabricCanvas.zoomToPoint(new Point(evt.offsetX, evt.offsetY), zoom);
  currentZoom.value = zoom;
  sliderZoomValue.value = zoomToSlider(zoom);
}

let isPanning = false;
let lastPanPoint = { x: 0, y: 0 };

function handleMouseDown(opt: any) {
  const evt = opt.e as MouseEvent;
  isPanning = true;
  lastPanPoint = { x: evt.clientX, y: evt.clientY };
  if (fabricCanvas) fabricCanvas.selection = false;
}

function handleMouseMove(opt: any) {
  if (!isPanning || !fabricCanvas) return;
  const evt = opt.e as MouseEvent;
  const dx = evt.clientX - lastPanPoint.x;
  const dy = evt.clientY - lastPanPoint.y;
  fabricCanvas.relativePan(new Point(dx, dy));
  lastPanPoint = { x: evt.clientX, y: evt.clientY };
}

function handleMouseUp() {
  isPanning = false;
  if (fabricCanvas) fabricCanvas.selection = true;
}

function setupCanvas() {
  if (!canvasEl.value || !canvasContainer.value) return;
  const cw = canvasContainer.value.clientWidth;
  const ch = canvasContainer.value.clientHeight;
  containerWidth.value = cw;
  containerHeight.value = ch;

  fabricCanvas = new Canvas(canvasEl.value, {
    selection: false,
    preserveObjectStacking: true,
    width: cw,
    height: ch
  });
  fabricCanvas.on('mouse:down', handleMouseDown);
  fabricCanvas.on('mouse:move', handleMouseMove);
  fabricCanvas.on('mouse:up', handleMouseUp);
  fabricCanvas.on('mouse:wheel', handleMouseWheel);

  resizeObserver = new ResizeObserver(entries => {
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
  robotMarker = null;
  backgroundImgObj = null;
}

function zoomIn() {
  if (!fabricCanvas) return;
  const newZoom = Math.min(currentZoom.value * 1.2, MAX_ZOOM);
  const center = fabricCanvas.getCenterPoint();
  fabricCanvas.zoomToPoint(center, newZoom);
  currentZoom.value = newZoom;
  sliderZoomValue.value = zoomToSlider(newZoom);
}

function zoomOut() {
  if (!fabricCanvas) return;
  const newZoom = Math.max(currentZoom.value / 1.2, MIN_ZOOM);
  const center = fabricCanvas.getCenterPoint();
  fabricCanvas.zoomToPoint(center, newZoom);
  currentZoom.value = newZoom;
  sliderZoomValue.value = zoomToSlider(newZoom);
}

function zoomReset() {
  if (!fabricCanvas) return;
  currentZoom.value = 1;
  sliderZoomValue.value = zoomToSlider(1);
  centerContent();
}

function handleSliderZoom(val: number) {
  if (!fabricCanvas) return;
  const newZoom = sliderToZoom(val);
  const center = fabricCanvas.getCenterPoint();
  fabricCanvas.zoomToPoint(center, newZoom);
  currentZoom.value = newZoom;
}

watch([containerWidth, containerHeight], () => {
  if (!fabricCanvas) return;
  fabricCanvas.setDimensions({ width: containerWidth.value, height: containerHeight.value });
  centerContent();
  fabricCanvas.renderAll();
});

watch(() => props.mapId, (newMapId) => {
  if (newMapId) {
    loadMapData(newMapId);
  } else {
    clearMapState();
  }
});

watch(() => props.location, () => {
  renderRobotMarker();
}, { deep: true });

onMounted(() => {
  setupCanvas();
  if (props.mapId) {
    loadMapData(props.mapId);
  }
});

onBeforeUnmount(() => {
  disposeCanvas();
});
</script>

<template>
  <div class="relative h-full min-h-0">
    <NSpin :show="mapLoading" class="h-full" content-class="h-full">
      <div ref="canvasContainer" class="h-full min-h-360px w-full overflow-hidden rounded bg-gray-100">
        <canvas ref="canvasEl" />
        <div v-if="!mapId" class="absolute inset-0 flex items-center justify-center">
          <NEmpty description="该机器人未绑定场景地图" />
        </div>
      </div>
    </NSpin>

    <!-- 图例（与地图编辑器保持一致） -->
    <div v-if="mapData"
      class="absolute left-12px top-12px z-10 flex flex-col gap-6px rounded-lg bg-white/90 px-12px py-8px text-xs shadow-md">
      <div class="max-w-180px truncate text-sm font-medium text-gray-700">{{ mapData.map.name }}</div>
      <div class="my-2px h-1px bg-gray-200"></div>
      <div class="flex items-center gap-6px">
        <span class="inline-block h-10px w-10px" style="background-color: #ffffff; border: 1px solid #d1d5db"></span>
        <span>可行区域</span>
      </div>
      <div class="flex items-center gap-6px">
        <span class="inline-block h-10px w-10px" style="background-color: #000000"></span>
        <span>不可行区域</span>
      </div>
      <div class="my-2px h-1px bg-gray-200"></div>
      <div class="flex items-center gap-6px">
        <span class="inline-block h-10px w-10px rounded-full" style="background-color: #22c55e"></span>
        <span>接待点</span>
      </div>
      <div class="flex items-center gap-6px">
        <span class="inline-block h-10px w-10px rounded-full" style="background-color: #047857"></span>
        <span>返回点</span>
      </div>
      <div class="flex items-center gap-6px">
        <span class="inline-block h-10px w-10px rounded-full" style="background-color: #ef4444; border: 2px solid #ffffff"></span>
        <span>机器人位置</span>
      </div>
      <div class="flex items-center gap-6px">
        <span class="inline-block h-10px w-10px"
          style="background-color: rgba(59, 130, 246, 0.3); border: 1px solid #3b82f6"></span>
        <span>障碍物</span>
      </div>
      <div class="flex items-center gap-6px">
        <span class="inline-block h-10px w-10px"
          style="background-image: linear-gradient(135deg, transparent 45%, #6b7280 45%, #6b7280 55%, transparent 55%); background-color: rgba(107, 114, 128, 0.12); border: 1px solid #6b7280"></span>
        <span>禁行区域/虚拟墙</span>
      </div>
      <div class="flex items-center gap-6px">
        <span class="inline-block h-10px w-10px"
          style="background-color: rgba(239, 68, 68, 0.15); border: 2px solid #ef4444"></span>
        <span>电子围栏</span>
      </div>
    </div>

    <!-- 缩放控制（与地图编辑器保持一致） -->
    <div v-if="mapData"
      class="absolute right-12px top-12px z-10 flex flex-col items-center gap-4px rounded-lg bg-white/90 px-6px py-8px shadow-md">
      <button
        class="flex h-24px w-24px items-center justify-center rounded-full text-sm font-bold text-blue-500 transition-colors hover:bg-blue-50"
        @click="zoomIn">
        +
      </button>
      <NSlider v-model:value="sliderZoomValue" vertical :min="0" :max="100" :step="1" :tooltip="false"
        :theme-overrides="sliderThemeOverrides" class="!h-160px" @update:value="handleSliderZoom" />
      <button
        class="flex h-24px w-24px items-center justify-center rounded-full text-sm font-bold text-blue-500 transition-colors hover:bg-blue-50"
        @click="zoomOut">
        -
      </button>
      <div class="cursor-pointer text-xs text-gray-500" title="点击重置缩放" @click="zoomReset">
        {{ Math.round(currentZoom * 100) }}%
      </div>
    </div>
  </div>
</template>

<style scoped></style>
