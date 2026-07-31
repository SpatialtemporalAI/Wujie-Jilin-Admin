<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { Canvas, Circle, Ellipse, FabricImage, Line, Pattern, Point, Polygon, Rect, Text, Triangle } from 'fabric';
import { getFilePreviewUrl } from '@/service/api/file';
import { fetchGetSceneMapList } from '@/service/api';
import { degToRad, pixelToWorld, radToDeg, worldToPixel } from '@/utils/coordinate';
import type { SelectedElement } from '../composables/useMapEditor';
import { extractRobotPoint } from '../utils/robot-location';
interface Props {
  editorData: Api.Scene.EditorMapData | null;
  selectedElement: SelectedElement | null;
  resolution: number;
  loading?: boolean;
  /** 当前地图绑定机器人的实时位置（画布展示用，纯视觉，不落库/不导出/不选中） */
  robotLocations?: Api.Robot.RobotLocationItem[];
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
});

const emit = defineEmits<{
  (e: 'select-element', el: SelectedElement | null): void;
  (e: 'update-element', data: { type: string; id: number; updates: Record<string, any> }): void;
  (e: 'zoom-change', zoom: number): void;
  (e: 'cursor-position', x: number, y: number): void;
  (e: 'undo'): void;
  (e: 'redo'): void;
  (
    e: 'context-menu',
    data: {
      x: number;
      y: number;
      clientX: number;
      clientY: number;
      target: { type: 'annotation' | 'object'; id: number } | null;
    }
  ): void;
  (e: 'request-type-switch', data: { id: number; clientX: number; clientY: number }): void;
  (e: 'rename-element', data: { type: 'annotation' | 'object'; id: number }): void;
  (e: 'blank-click'): void;
  (
    e: 'hover-element',
    data: { type: 'annotation' | 'object' | 'robot'; id: number; clientX: number; clientY: number } | null
  ): void;
}>();

const canvasContainer = ref<HTMLDivElement>();
const canvasEl = ref<HTMLCanvasElement>();
const minimapEl = ref<HTMLDivElement>();
let fabricCanvas: Canvas | null = null;
let backgroundImgObj: FabricImage | null = null;
const elementMap: Map<string, any> = new Map();
const annotationDecorations: Map<number, { text: Text; angleIndicator: Triangle }> = new Map();
const objectLabels: Map<number, Text> = new Map();
// 机器人位置标记：robotId -> { circle, arrow, label }（装饰层，不进 elementMap）
// 用独立对象、各自绝对坐标定位，避免 Group bbox 重算导致圆点与名称错位/坐标偏移
const robotMarkers: Map<number, { circle: Circle; arrow: Triangle | null; label: Text }> = new Map();
let resizeObserver: ResizeObserver | null = null;

const minimapImageUrl = ref('');
const minimapRect = ref({ x: 0, y: 0, w: 0, h: 0 });
const MINIMAP_SIZE = 180;

// 鼠标世界坐标（显示在 minimap 上方）
const cursorWorldX = ref(0);
const cursorWorldY = ref(0);

const minimapScale = computed(() => {
  const mw = canvasWidth.value;
  const mh = canvasHeight.value;
  if (mw === 0 || mh === 0) return { s: 1, w: 0, h: 0, ox: 0, oy: 0 };
  const s = Math.min(MINIMAP_SIZE / mw, MINIMAP_SIZE / mh);
  const w = mw * s;
  const h = mh * s;
  const ox = (MINIMAP_SIZE - w) / 2;
  const oy = (MINIMAP_SIZE - h) / 2;
  return { s, w, h, ox, oy };
});
let start_point_x = 0;
let start_point_y = 0;
async function loadSceneList() {
  try {
    const { data } = await fetchGetSceneMapList({
      page: 1,
      page_size: 999,
      status: null,
      name: null,
      group_id: undefined
    });
    if (data?.records) {
      start_point_x = data?.records[0]?.start_point_x;
      start_point_y = data?.records[0]?.start_point_y;
    }
  } catch { }
}
function updateMinimap() {
  if (!fabricCanvas) return;
  const vpt = fabricCanvas.viewportTransform;
  if (!vpt) return;
  const zoom = vpt[0];
  const { s, ox, oy, w: imgW, h: imgH } = minimapScale.value;

  // Visible area in content coordinates
  const viewLeft = -vpt[4] / zoom;
  const viewTop = -vpt[5] / zoom;
  const viewW = containerWidth.value / zoom;
  const viewH = containerHeight.value / zoom;

  const visibleLeft = Math.max(0, viewLeft);
  const visibleTop = Math.max(0, viewTop);
  const visibleRight = Math.min(canvasWidth.value, viewLeft + viewW);
  const visibleBottom = Math.min(canvasHeight.value, viewTop + viewH);

  if (visibleRight <= visibleLeft || visibleBottom <= visibleTop) {
    minimapRect.value = { x: ox, y: oy, w: 0, h: 0 };
    return;
  }

  minimapRect.value = {
    x: ox + visibleLeft * s,
    y: oy + visibleTop * s,
    w: (visibleRight - visibleLeft) * s,
    h: (visibleBottom - visibleTop) * s
  };
}

// --- Minimap drag-to-navigate ---
let minimapDragging = false;

function minimapClientToContent(clientX: number, clientY: number) {
  if (!minimapEl.value) return null;
  const rect = minimapEl.value.getBoundingClientRect();
  const mx = clientX - rect.left;
  const my = clientY - rect.top;
  const { s, ox, oy } = minimapScale.value;
  // Minimap pixel → content coordinate
  const contentX = (mx - ox) / s;
  const contentY = (my - oy) / s;
  return { x: contentX, y: contentY };
}

function navigateToMinimapPoint(clientX: number, clientY: number) {
  if (!fabricCanvas) return;
  const pt = minimapClientToContent(clientX, clientY);
  if (!pt) return;
  const zoom = fabricCanvas.getZoom();
  // Center the viewport so (pt.x, pt.y) is at the center of the visible area
  const offsetX = containerWidth.value / 2 - pt.x * zoom;
  const offsetY = containerHeight.value / 2 - pt.y * zoom;
  fabricCanvas.setViewportTransform([zoom, 0, 0, zoom, offsetX, offsetY]);
  fabricCanvas.renderAll();
  updateMinimap();
}

function handleMinimapDown(e: MouseEvent) {
  e.preventDefault();
  minimapDragging = true;
  navigateToMinimapPoint(e.clientX, e.clientY);
}

function handleMinimapMove(e: MouseEvent) {
  if (!minimapDragging) return;
  navigateToMinimapPoint(e.clientX, e.clientY);
}

function handleMinimapUp() {
  minimapDragging = false;
}

const MIN_ZOOM = 1;
const MAX_ZOOM = 5;
let currentZoom = 1;
let isPanning = false;
let lastPanPoint = { x: 0, y: 0 };
let spacePressed = false;

let isDraggingObject = false;
let justDragged = false;
let clickTimer: number | null = null;
let lastDblClickTime = 0;
let mouseDownClientPos: { x: number; y: number } | null = null;
let mouseDownTarget: any = null;
let isLocalUpdate = false;
let cursorEmitRafId: number | null = null;
let lastCursorWorld = { x: 0, y: 0 };
let minimapRafId: number | null = null;

const MIN_OBJECT_SIZE = 1;
const CLICK_MOVE_THRESHOLD = 5;
// 点位 / 机器人位置标记整体等比缩小至 80%（视觉尺寸 ×0.8）
const POINT_MARKER_SCALE = 0.8;
// 点位圆形半径（未选中 / 选中）
const ANN_RADIUS = 8 * POINT_MARKER_SCALE;
const ANN_RADIUS_SELECTED = 10 * POINT_MARKER_SCALE;
// 点位名称：字号与距圆心的垂直偏移
const ANN_LABEL_FONT_SIZE = 12 * POINT_MARKER_SCALE;
const ANN_LABEL_OFFSET = 18 * POINT_MARKER_SCALE;
// 障碍物/禁行区域/电子围栏名称标签字号（不随 POINT_MARKER_SCALE 收缩，保持 12px）
const OBJECT_LABEL_FONT_SIZE = 12;
// 机器人实时位置圆形半径与名称字号
const ROBOT_RADIUS = 9 * POINT_MARKER_SCALE;
const ROBOT_LABEL_FONT_SIZE = 11 * POINT_MARKER_SCALE;
// 方向箭头尺寸（点位与机器人共用）
const ARROW_WIDTH = 6 * POINT_MARKER_SCALE;
const ARROW_HEIGHT = 8 * POINT_MARKER_SCALE;

/**
 * 计算点位方向箭头的位置和旋转角度（ROS 弧度 → Fabric）
 * - ROS 弧度：0 朝东（右），π/2 朝北（上），π 朝西（左），逆时针为正
 * - Fabric Triangle 默认顶点朝上、顺时针为正
 * - 箭头底部贴合圆形边缘、顶点指向角度方向
 */
function getAnnotationArrowTransform(annX: number, annY: number, rosRad: number, radius: number, zoom = 1) {
  // 「半径 + 箭头半高」的屏幕距离换算成当前 zoom 下的场景距离，
  // 配合外部对箭头做 1/zoom 反向缩放，保证缩放后箭头底部仍贴合圆点边缘
  const sceneDist = (radius + ARROW_HEIGHT / 2) / zoom;
  return {
    x: annX + sceneDist * Math.cos(rosRad),
    y: annY - sceneDist * Math.sin(rosRad),
    angle: -radToDeg(rosRad) + 90
  };
}

/**
 * Fabric 圆形旋转角度（度） → ROS 弧度
 * 反推公式：rosRad = (90 - fabricAngle) * π / 180
 */
function fabricAngleToAnnotationRad(fabricAngle: number): number {
  return degToRad(90 - fabricAngle);
}

// 障碍物 / 禁区 / 点位 / 电子围栏 颜色
const OBSTACLE_FILL = 'rgba(59, 130, 246, 0.3)';
const OBSTACLE_STROKE = '#3b82f6';
const RESTRICTED_STROKE = '#6b7280';
const FENCE_FILL = 'rgba(239, 68, 68, 0.15)';
const FENCE_STROKE = '#ef4444';
const POINT_FILL = '#22c55e';
const POINT_SELECTED_FILL = '#16a34a';
const RETURN_POINT_FILL = '#047857';
const RETURN_POINT_SELECTED_FILL = '#065f46';
// 机器人实时位置标记（红色圆点，区别于绿色点位）
const ROBOT_FILL = '#ef4444';
const ROBOT_STROKE = '#ffffff';

function createRestrictedPattern(): Pattern {
  const size = 8;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d')!;
  // 浅灰底
  ctx.fillStyle = 'rgba(107, 114, 128, 0.12)';
  ctx.fillRect(0, 0, size, size);
  // 灰色斜线
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

let restrictedPattern: Pattern | null = null;
function getRestrictedPattern(): Pattern {
  if (!restrictedPattern) restrictedPattern = createRestrictedPattern();
  return restrictedPattern;
}

const canvasWidth = ref(800);
const canvasHeight = ref(600);
const containerWidth = ref(0);
const containerHeight = ref(0);

const sliderZoomValue = ref(0);

const sliderThemeOverrides = {
  fillColor: '#3b82f6',
  fillColorHover: '#2563eb',
  dotColor: '#3b82f6',
  dotBorder: '2px solid #fff',
  dotBoxShadow: '0 1px 4px rgba(0,0,0,0.2)'
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

function getEffectiveOrigin() {
  if (!props.editorData) return { x: 0, y: 0 };
  const map = props.editorData.map;
  const storedW = map.width || canvasWidth.value;
  const storedH = map.height || canvasHeight.value;
  const sx = canvasWidth.value / storedW;
  const sy = canvasHeight.value / storedH;
  return {
    x: map.start_point_x ?? 0,
    y: map.start_point_y ?? 0
  };
}

function canvasPointToWorld(px: number, py: number) {
  // 网格按"左上角 (0,0)，向右向下递增"显示，鼠标坐标也按此口径
  return { x: px * props.resolution, y: py * props.resolution };
}

function worldToCanvasPoint(wx: number, wy: number) {
  const { x: originX, y: originY } = getEffectiveOrigin();
  const px = worldToPixel(wx, wy, originX, originY, props.resolution);
  return { x: px.x, y: canvasHeight.value - px.y };
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
  updateMinimap();
}

// 同步结构：仅在 annotations/paths/objects 的 id 集合变化时新增/删除 fabric 对象
function syncStructure() {
  if (!fabricCanvas || !props.editorData) return;
  const existingKeys = new Set<string>();

  // paths 最底层
  for (const path of props.editorData.paths) {
    const key = getElementKey('path', path.id);
    existingKeys.add(key);
    if (elementMap.has(key)) continue;
    const startAnn = props.editorData.annotations.find(a => a.id === path.start_annotation_id);
    const endAnn = props.editorData.annotations.find(a => a.id === path.end_annotation_id);
    if (!startAnn || !endAnn) continue;
    const line = new Line([startAnn.x, startAnn.y, endAnn.x, endAnn.y], {
      stroke: '#f97316',
      strokeWidth: 3,
      selectable: false,
      evented: false
    });
    setElementData(line, { type: 'path', id: path.id });
    fabricCanvas.add(line);
    fabricCanvas.sendObjectToBack(line);
    elementMap.set(key, line);
  }

  // objects 中间层
  for (const obj of props.editorData.objects) {
    const key = getElementKey('object', obj.id);
    existingKeys.add(key);
    if (elementMap.has(key)) continue;

    const isRestricted = obj.type === 'restricted' || obj.type === '禁区';
    const isFence = obj.type === 'fence' || obj.type === '电子围栏';
    const fillColor: any = isRestricted ? getRestrictedPattern() : isFence ? FENCE_FILL : OBSTACLE_FILL;
    const strokeColor = isRestricted ? RESTRICTED_STROKE : isFence ? FENCE_STROKE : OBSTACLE_STROKE;
    const baseStrokeWidth = isFence ? 3 : 2;
    const commonOpts = {
      left: obj.x,
      top: obj.y,
      originX: 'left' as const,
      originY: 'top' as const,
      angle: obj.angle ?? 0,
      fill: fillColor,
      stroke: strokeColor,
      strokeWidth: baseStrokeWidth,
      hasControls: true,
      // 边框宽度按屏幕像素渲染，不随图形/视口缩放变化
      strokeUniform: true,
      // 禁用对象缓存，确保 strokeUniform 在缩放过程中实时生效，
      // 避免缓存拉伸导致边框先变粗后恢复
      objectCaching: false,
      noScaleCache: true
    };

    let fabricObj: any = null;

    if (obj.points) {
      try {
        const pts = JSON.parse(obj.points);
        fabricObj = new Polygon(pts, commonOpts);
      } catch {
        /* skip invalid polygon */
      }
    } else if (obj.type === 'obstacle-circle') {
      const w = obj.width || 10;
      const h = obj.height || 10;
      fabricObj = new Ellipse({
        ...commonOpts,
        rx: w / 2,
        ry: h / 2
      });
    } else if (obj.type === 'obstacle-triangle') {
      fabricObj = new Triangle({
        ...commonOpts,
        width: obj.width || 5,
        height: obj.height || 5
      });
    } else if (isFence) {
      fabricObj = new Rect({
        ...commonOpts,
        width: obj.width || 10,
        height: obj.height || 10
      });
    } else {
      const isSquare = obj.type === 'obstacle-square';
      fabricObj = new Rect({
        ...commonOpts,
        width: obj.width || 5,
        height: isSquare ? obj.width || 5 : obj.height || 5
      });
    }

    if (fabricObj) {
      setElementData(fabricObj, { type: 'object', id: obj.id });
      fabricCanvas.add(fabricObj);
      elementMap.set(key, fabricObj);

      // 名称标签（不可交互，跟随图形位置，字体大小与接待点保持一致并再放大两个像素）
      const labelText = new Text(obj.name || '', {
        fontSize: OBJECT_LABEL_FONT_SIZE,
        fill: strokeColor,
        originX: 'center',
        originY: 'center',
        fontFamily: 'sans-serif',
        fontWeight: 'bold',
        evented: false,
        selectable: false,
        hasControls: false,
        hoverCursor: 'default'
      });
      fabricCanvas.add(labelText);
      objectLabels.set(obj.id, labelText);
    }
  }

  // annotations 最顶层
  for (const ann of props.editorData.annotations) {
    const key = getElementKey('annotation', ann.id);
    existingKeys.add(key);
    if (elementMap.has(key)) continue;

    const isSelected = props.selectedElement?.type === 'annotation' && props.selectedElement?.id === ann.id;
    const isReturnPoint = ann.type === 'navigation' || ann.type === '返回点';
    const annColor = isReturnPoint
      ? isSelected
        ? RETURN_POINT_SELECTED_FILL
        : RETURN_POINT_FILL
      : isSelected
        ? POINT_SELECTED_FILL
        : POINT_FILL;

    // 可交互的 circle（拖动 + 旋转入口）
    const circle = new Circle({
      radius: isSelected ? ANN_RADIUS_SELECTED : ANN_RADIUS,
      fill: annColor,
      stroke: '#fff',
      strokeWidth: 2,
      originX: 'center',
      originY: 'center',
      hasControls: true,
      hasRotatingPoint: true,
      lockScalingX: true,
      lockScalingY: true,
      lockUniScaling: true
    });
    // 只保留旋转控制点，禁用所有缩放控制点
    circle.setControlsVisibility({
      ml: false,
      mr: false,
      mt: false,
      mb: false,
      tl: false,
      tr: false,
      bl: false,
      br: false,
      mtr: true
    });
    setElementData(circle, { type: 'annotation', id: ann.id });
    fabricCanvas.add(circle);
    elementMap.set(key, circle);

    // 装饰：角度指示器与文字（不可交互，纯渲染）
    const arrowRadius = isSelected ? ANN_RADIUS_SELECTED : ANN_RADIUS;
    const arrowTransform = getAnnotationArrowTransform(ann.x, ann.y, ann.angle || 0, arrowRadius);
    const angleIndicator = new Triangle({
      width: ARROW_WIDTH,
      height: ARROW_HEIGHT,
      fill: annColor,
      originX: 'center',
      originY: 'center',
      left: arrowTransform.x,
      top: arrowTransform.y,
      angle: arrowTransform.angle,
      visible: true,
      evented: false,
      selectable: false,
      hasControls: false,
      hoverCursor: 'default'
    });
    fabricCanvas.add(angleIndicator);

    const text = new Text(ann.name, {
      fontSize: ANN_LABEL_FONT_SIZE,
      fill: annColor,
      originX: 'center',
      originY: 'center',
      top: ANN_LABEL_OFFSET,
      fontFamily: 'sans-serif',
      fontWeight: 'bold',
      evented: false,
      selectable: false,
      hasControls: false,
      hoverCursor: 'default'
    });
    fabricCanvas.add(text);

    annotationDecorations.set(ann.id, { text, angleIndicator });
  }

  // 移除不再存在的元素
  for (const [key, obj] of elementMap) {
    if (!existingKeys.has(key)) {
      fabricCanvas.remove(obj);
      elementMap.delete(key);
      // key 形如 'object--1699876543210'（id 为负数），不能用 split('-')
      const dashIdx = key.indexOf('-');
      const type = key.substring(0, dashIdx);
      const idStr = key.substring(dashIdx + 1);
      const elemId = Number(idStr);
      if (type === 'annotation') {
        const deco = annotationDecorations.get(elemId);
        if (deco) {
          fabricCanvas.remove(deco.text);
          fabricCanvas.remove(deco.angleIndicator);
          annotationDecorations.delete(elemId);
        }
      } else if (type === 'object') {
        const label = objectLabels.get(elemId);
        if (label) {
          fabricCanvas.remove(label);
          objectLabels.delete(elemId);
        }
      }
    }
  }
}

// 仅更新位置和尺寸（拖动结束、undo/redo、loadMap）
function updatePositions() {
  if (!fabricCanvas || !props.editorData) return;

  for (const ann of props.editorData.annotations) {
    const key = getElementKey('annotation', ann.id);
    const circle = elementMap.get(key);
    if (!circle) continue;
    circle.set({ left: ann.x, top: ann.y });
    circle.setCoords();
    const deco = annotationDecorations.get(ann.id);
    if (deco) {
      deco.text.set({ left: ann.x, top: ann.y + ANN_LABEL_OFFSET });
      deco.text.setCoords();
      const isSelected = props.selectedElement?.type === 'annotation' && props.selectedElement?.id === ann.id;
      const arrowTransform = getAnnotationArrowTransform(
        ann.x,
        ann.y,
        ann.angle || 0,
        isSelected ? ANN_RADIUS_SELECTED : ANN_RADIUS
      );
      deco.angleIndicator.set({
        left: arrowTransform.x,
        top: arrowTransform.y,
        angle: arrowTransform.angle
      });
      deco.angleIndicator.setCoords();
    }
  }

  for (const path of props.editorData.paths) {
    const key = getElementKey('path', path.id);
    const line = elementMap.get(key);
    if (!line) continue;
    const startAnn = props.editorData.annotations.find(a => a.id === path.start_annotation_id);
    const endAnn = props.editorData.annotations.find(a => a.id === path.end_annotation_id);
    if (!startAnn || !endAnn) continue;
    line.set({ x1: startAnn.x, y1: startAnn.y, x2: endAnn.x, y2: endAnn.y });
    line.setCoords();
  }

  for (const obj of props.editorData.objects) {
    const key = getElementKey('object', obj.id);
    const fabricObj = elementMap.get(key);
    if (!fabricObj) continue;
    fabricObj.set({ left: obj.x, top: obj.y, angle: obj.angle ?? 0 });
    if (fabricObj instanceof Ellipse) {
      fabricObj.set({ rx: (obj.width || 10) / 2, ry: (obj.height || 10) / 2 });
    } else if (fabricObj instanceof Rect || fabricObj instanceof Triangle) {
      // 与 syncStructure 创建时的兜底口径一致，避免 obj.width/height 缺失（为 0）时
      // 图形塌缩成细线；同时与运行监控 position-map-panel 的渲染保持一致。
      fabricObj.set({ width: obj.width || 5, height: obj.height || 5 });
    }
    fabricObj.setCoords();
    const label = objectLabels.get(obj.id);
    if (label) {
      syncObjectLabelTransform(label, fabricObj);
    }
  }
  applyMarkerZoom();
}

/**
 * 渲染/更新机器人实时位置标记（装饰层，纯视觉）。
 * 机器人世界坐标(米) → 像素，与点位(worldToPixelCoords)同规则：
 *   wp = worldToPixel(wx, wy, start_point_x, start_point_y, resolution)
 *   px = wp.x，py = height - wp.y
 * 标记不进 elementMap、evented/selectable/excludeFromExport 全关，
 * 因此不参与选中、保存（保存只读 editorData）、导出。
 */
function renderRobots() {
  if (!fabricCanvas) return;
  const map = props.editorData?.map;
  const h = map?.height ?? 0;
  const ox = map?.start_point_x ?? 0;
  const oy = map?.start_point_y ?? 0;
  const res = props.resolution || 0.2;

  const seen = new Set<number>();
  for (const robot of props.robotLocations ?? []) {
    const pt = extractRobotPoint(robot);
    if (!pt) continue;
    seen.add(robot.id);
    // 与点位同规则：worldToPixel 后翻转 Y 轴
    const wp = worldToPixel(pt.x, pt.y, ox, oy, res);
    const px = wp.x;
    const py = h - wp.y;

    const radius = ROBOT_RADIUS;
    const labelTop = py + radius + 8;
    const labelText = robot.name || `#${robot.id}`;
    // 朝向角(ROS 弧度)：与点位同约定（0 朝东，π/2 朝北，逆时针为正）
    const hasAngle = pt.angle !== undefined;
    const arrowTransform = hasAngle ? getAnnotationArrowTransform(px, py, pt.angle as number, radius) : null;

    const existing = robotMarkers.get(robot.id);
    if (existing) {
      existing.circle.set({ left: px, top: py });
      existing.circle.setCoords();
      existing.label.set({ left: px, top: labelTop, text: labelText });
      existing.label.setCoords();
      if (existing.arrow) {
        if (arrowTransform) {
          existing.arrow.set({
            left: arrowTransform.x,
            top: arrowTransform.y,
            angle: arrowTransform.angle,
            visible: true
          });
        } else {
          existing.arrow.set({ visible: false });
        }
        existing.arrow.setCoords();
      }
      continue;
    }

    // 圆点与名称各自绝对定位：圆点中心精确落在 (px, py)，名称在其正下方
    const circle = new Circle({
      radius,
      fill: ROBOT_FILL,
      stroke: ROBOT_STROKE,
      strokeWidth: 2,
      originX: 'center',
      originY: 'center',
      left: px,
      top: py,
      selectable: false,
      evented: false,
      hoverCursor: 'default',
      excludeFromExport: true
    });
    // 方向箭头（与点位同一 ROS 弧度 → Fabric 变换）；无角度时不渲染
    const arrow = arrowTransform
      ? new Triangle({
        width: ARROW_WIDTH,
        height: ARROW_HEIGHT,
        fill: ROBOT_FILL,
        originX: 'center',
        originY: 'center',
        left: arrowTransform.x,
        top: arrowTransform.y,
        angle: arrowTransform.angle,
        selectable: false,
        evented: false,
        hoverCursor: 'default',
        excludeFromExport: true
      })
      : null;
    const label = new Text(labelText, {
      fontSize: ROBOT_LABEL_FONT_SIZE,
      fill: ROBOT_FILL,
      fontFamily: 'sans-serif',
      fontWeight: 'bold',
      originX: 'center',
      originY: 'center',
      left: px,
      top: labelTop,
      selectable: false,
      evented: false,
      hoverCursor: 'default',
      excludeFromExport: true
    });
    if (arrow) {
      fabricCanvas.add(circle, arrow, label);
    } else {
      fabricCanvas.add(circle, label);
    }
    robotMarkers.set(robot.id, { circle, arrow, label });
  }

  // 移除不再上报位置的机器人
  for (const [id, marker] of robotMarkers) {
    if (!seen.has(id)) {
      if (marker.arrow) fabricCanvas.remove(marker.circle, marker.arrow, marker.label);
      else fabricCanvas.remove(marker.circle, marker.label);
      robotMarkers.delete(id);
    }
  }
  applyMarkerZoom();
  fabricCanvas.renderAll();
}

function clearRobotMarkers() {
  if (!fabricCanvas) {
    robotMarkers.clear();
    return;
  }
  for (const marker of robotMarkers.values()) {
    if (marker.arrow) fabricCanvas.remove(marker.circle, marker.arrow, marker.label);
    else fabricCanvas.remove(marker.circle, marker.label);
  }
  robotMarkers.clear();
}

/**
 * 缩放变化时让点位/机器人标记保持固定屏幕大小（与运行监控页一致）：
 * - 读视口「真实」zoom（getZoom），对标记做 1/zoom 反向缩放（与视口 zoom 相消 → 屏幕尺寸恒定）
 * - left/top 仍是场景坐标，故位置随地图平移/缩放
 * - 箭头/文字相对圆点的偏移按 1/zoom 收敛，保证屏幕间距恒定
 * annotation circle 虽可交互（拖动/旋转），但仅改 scaleX/scaleY —— 位置、角度、数据模型与保存均不受影响。
 */
function applyMarkerZoom() {
  if (!fabricCanvas || !props.editorData) return;
  const zoom = fabricCanvas.getZoom() || 1;
  const inv = zoom > 0 ? 1 / zoom : 1;
  // 点位：circle（可交互）+ 角度箭头 + 名称
  for (const ann of props.editorData.annotations) {
    const key = getElementKey('annotation', ann.id);
    const circle = elementMap.get(key) as Circle | undefined;
    const deco = annotationDecorations.get(ann.id);
    const r = circle?.radius ?? ANN_RADIUS;
    if (circle) {
      circle.set({ scaleX: inv, scaleY: inv });
      circle.setCoords();
    }
    if (deco) {
      const t = getAnnotationArrowTransform(ann.x, ann.y, ann.angle || 0, r, zoom);
      deco.angleIndicator.set({ left: t.x, top: t.y, angle: t.angle, scaleX: inv, scaleY: inv });
      deco.angleIndicator.setCoords();
      deco.text.set({ left: ann.x, top: ann.y + ANN_LABEL_OFFSET * inv, scaleX: inv, scaleY: inv });
      deco.text.setCoords();
    }
  }
  // 机器人标记：circle + 方向箭头 + 名称
  for (const m of robotMarkers.values()) {
    const px = m.circle.left ?? 0;
    const py = m.circle.top ?? 0;
    m.circle.set({ scaleX: inv, scaleY: inv });
    m.circle.setCoords();
    if (m.arrow) {
      // 由箭头当前角度反推 ROS 弧度：arrow.angle = -radToDeg(rosRad) + 90
      const rosRad = ((90 - (m.arrow.angle ?? 0)) * Math.PI) / 180;
      const t = getAnnotationArrowTransform(px, py, rosRad, ROBOT_RADIUS, zoom);
      m.arrow.set({ left: t.x, top: t.y, angle: t.angle, scaleX: inv, scaleY: inv });
      m.arrow.setCoords();
    }
    m.label.set({ left: px, top: py + (ROBOT_RADIUS + 8) * inv, scaleX: inv, scaleY: inv });
    m.label.setCoords();
  }
  // 障碍物/电子围栏/禁行区域名称标签：与点位名称保持相同的屏幕大小
  for (const [objId, label] of objectLabels) {
    const objKey = getElementKey('object', objId);
    const fabricObj = elementMap.get(objKey);
    if (fabricObj) {
      syncObjectLabelTransform(label, fabricObj);
    }
  }
  fabricCanvas.renderAll();
}

// 仅更新选中样式与文本（轻量路径，不重渲染结构）
function updateSelectionStyle() {
  if (!fabricCanvas || !props.editorData) return;
  const sel = props.selectedElement;

  for (const ann of props.editorData.annotations) {
    const key = getElementKey('annotation', ann.id);
    const circle = elementMap.get(key) as Circle | undefined;
    if (!circle) continue;
    const isSelected = sel?.type === 'annotation' && sel?.id === ann.id;
    const isReturnPoint = ann.type === 'navigation' || ann.type === '返回点';
    const annColor = isReturnPoint
      ? isSelected
        ? RETURN_POINT_SELECTED_FILL
        : RETURN_POINT_FILL
      : isSelected
        ? POINT_SELECTED_FILL
        : POINT_FILL;
    circle.set('fill', annColor);
    circle.set('radius', isSelected ? ANN_RADIUS_SELECTED : ANN_RADIUS);
    circle.setCoords();
    const deco = annotationDecorations.get(ann.id);
    if (deco) {
      deco.text.set('text', ann.name);
      deco.text.set('fill', annColor);
    }
  }

  // 同步 object 的 name 文本（改名后立即刷新）
  for (const obj of props.editorData.objects) {
    const label = objectLabels.get(obj.id);
    if (label) {
      label.set('text', obj.name || '');
    }
  }
}

// 完整渲染：结构 + 位置 + 选中样式 + renderAll
function renderElements() {
  if (!fabricCanvas || !props.editorData) return;
  if (isDraggingObject) return;
  syncStructure();
  updatePositions();
  updateSelectionStyle();
  updateSelection();
  // 机器人标记最后渲染，保证位于所有元素之上
  renderRobots();
  fabricCanvas.renderAll();
}

function updateSelection() {
  if (!fabricCanvas) return;
  if (isDraggingObject) return;
  const sel = props.selectedElement;
  const currentActive = fabricCanvas.getActiveObject();
  if (sel) {
    const key = getElementKey(sel.type, sel.id);
    const targetObj = elementMap.get(key);
    if (currentActive === targetObj) return; // 已选中，不打断 fabric
    fabricCanvas.discardActiveObject();
    if (targetObj) fabricCanvas.setActiveObject(targetObj);
  } else if (currentActive) {
    fabricCanvas.discardActiveObject();
  }
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
    fabricCanvas.sendObjectToBack(img); // 确保背景图片在最底层

    fabricCanvas.setDimensions({
      width: containerWidth.value || canvasContainer.value!.clientWidth,
      height: containerHeight.value || canvasContainer.value!.clientHeight
    });
    // 切换地图时重置视口缩放为 1（与 currentZoom/slider 状态同步），避免标记大小跳变
    fabricCanvas.setZoom(1);
    centerContent();
    fabricCanvas.renderAll();
    renderElements(); // 图片加载完成后渲染元素
    currentZoom = 1;
    sliderZoomValue.value = sliderValueToZoom(1);
    minimapImageUrl.value = url;
    updateMinimap();
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

  // 右键由原生 contextmenu 事件处理
  if (evt.button === 2) return;

  // 记录按下位置和目标，用于 click vs drag 判定
  mouseDownClientPos = { x: evt.clientX, y: evt.clientY };
  mouseDownTarget = opt.target ?? null;
  // 点击空白（无目标）时通知外部关闭浮层
  if (!opt.target) {
    emit('blank-click');
  }
}

function handleMouseMove(opt: any) {
  if (!fabricCanvas) return;
  const evt = opt.e as MouseEvent;
  const pointer = fabricCanvas.getScenePoint(evt);

  if (isPanning) {
    const dx = evt.clientX - lastPanPoint.x;
    const dy = evt.clientY - lastPanPoint.y;
    fabricCanvas.relativePan(new Point(dx, dy));
    lastPanPoint = { x: evt.clientX, y: evt.clientY };
    if (minimapRafId === null) {
      minimapRafId = requestAnimationFrame(() => {
        minimapRafId = null;
        updateMinimap();
      });
    }
    return;
  }

  const world = canvasPointToWorld(pointer.x, pointer.y);
  lastCursorWorld = world;
  if (cursorEmitRafId === null) {
    cursorEmitRafId = requestAnimationFrame(() => {
      cursorEmitRafId = null;
      cursorWorldX.value = lastCursorWorld.x;
      cursorWorldY.value = lastCursorWorld.y;
      emit('cursor-position', lastCursorWorld.x, lastCursorWorld.y);
    });
  }

  // hover tooltip：拖动时不弹出
  if (!isDraggingObject) {
    // 机器人在视觉顶层，优先判定，命中则显示机器人信息
    const robotHit = findRobotAtScenePoint(pointer.x, pointer.y);
    if (robotHit) {
      emit('hover-element', { ...robotHit, clientX: evt.clientX, clientY: evt.clientY });
    } else {
      const hovered = findElementAtScenePoint(pointer.x, pointer.y);
      if (hovered) {
        emit('hover-element', { ...hovered, clientX: evt.clientX, clientY: evt.clientY });
      } else {
        emit('hover-element', null);
      }
    }
  }
}

function handleMouseUp(opt: any) {
  if (isPanning) {
    isPanning = false;
    if (fabricCanvas) {
      fabricCanvas.selection = true;
      updateMinimap();
    }
    return;
  }

  // 点位单击切换类型：用按下/抬起的屏幕距离判定是否为"点击"
  // （fabric 的 object:moving 在 1-2px 抖动时也会触发，单靠 justDragged 不可靠）
  const evt = opt.e as MouseEvent;
  if (mouseDownClientPos && evt && Date.now() - lastDblClickTime > 350) {
    const dx = evt.clientX - mouseDownClientPos.x;
    const dy = evt.clientY - mouseDownClientPos.y;
    const isClick = Math.sqrt(dx * dx + dy * dy) < CLICK_MOVE_THRESHOLD;
    if (isClick && mouseDownTarget) {
      const data = getElementData(mouseDownTarget);
      if (data?.type === 'annotation') {
        if (clickTimer !== null) {
          window.clearTimeout(clickTimer);
          clickTimer = null;
        }
        const annId = data.id;
        const clientX = evt.clientX;
        const clientY = evt.clientY;
        clickTimer = window.setTimeout(() => {
          clickTimer = null;
          emit('request-type-switch', { id: annId, clientX, clientY });
        }, 250);
      }
    }
  }

  mouseDownClientPos = null;
  mouseDownTarget = null;
  justDragged = false;
}

function handleDoubleClick(opt: any) {
  // 取消点位单击切换类型的定时器
  if (clickTimer !== null) {
    window.clearTimeout(clickTimer);
    clickTimer = null;
  }
  lastDblClickTime = Date.now();
  const target = opt.target;
  if (!target) return;
  const data = getElementData(target);
  if (!data) return;
  if (data.type === 'annotation' || data.type === 'object') {
    emit('rename-element', { type: data.type, id: data.id });
  }
}

function syncObjectLabelTransform(label: Text, fabricObj: any) {
  if (!fabricCanvas) return;
  const zoom = fabricCanvas.getZoom() || 1;
  const inv = zoom > 0 ? 1 / zoom : 1;
  const bounds = fabricObj.getBoundingRect();
  label.set({
    left: bounds.left + bounds.width / 2,
    top: bounds.top + bounds.height + 12 * inv,
    scaleX: inv,
    scaleY: inv
  });
  label.setCoords();
}

function updateObjectLabelPosition(obj: any, id: number) {
  const label = objectLabels.get(id);
  if (!label) return;
  syncObjectLabelTransform(label, obj);
}

function handleObjectMoved(opt: any) {
  const obj = opt.target;
  if (!obj) return;
  const data = getElementData(obj);
  if (!data) return;
  isDraggingObject = true;
  justDragged = true;
  if (data.type === 'annotation') {
    const deco = annotationDecorations.get(data.id);
    if (deco) {
      const zoom = fabricCanvas?.getZoom() || 1;
      const inv = zoom > 0 ? 1 / zoom : 1;
      deco.text.set({ left: obj.left, top: (obj.top ?? 0) + ANN_LABEL_OFFSET * inv });
      const ann = props.editorData?.annotations.find(a => a.id === data.id);
      const isSelected = props.selectedElement?.type === 'annotation' && props.selectedElement?.id === data.id;
      const arrowTransform = getAnnotationArrowTransform(
        obj.left ?? 0,
        obj.top ?? 0,
        ann?.angle ?? 0,
        isSelected ? ANN_RADIUS_SELECTED : ANN_RADIUS,
        zoom
      );
      deco.angleIndicator.set({
        left: arrowTransform.x,
        top: arrowTransform.y,
        angle: arrowTransform.angle
      });
    }
  } else if (data.type === 'object') {
    updateObjectLabelPosition(obj, data.id);
  }
}

function handleObjectScaling(opt: any) {
  const obj = opt.target;
  if (!obj) return;
  const data = getElementData(obj);
  if (!data) return;
  if (data.type === 'object') {
    updateObjectLabelPosition(obj, data.id);
    if (fabricCanvas) fabricCanvas.renderAll();
  }
}

function handleObjectRotating(opt: any) {
  const obj = opt.target;
  if (!obj) return;
  const data = getElementData(obj);
  if (!data) return;
  if (data.type === 'object') {
    updateObjectLabelPosition(obj, data.id);
  } else if (data.type === 'annotation') {
    // 点位旋转时实时同步箭头位置和角度
    const deco = annotationDecorations.get(data.id);
    if (deco) {
      const rad = fabricAngleToAnnotationRad(obj.angle ?? 0);
      const zoom = fabricCanvas?.getZoom() || 1;
      const isSelected = props.selectedElement?.type === 'annotation' && props.selectedElement?.id === data.id;
      const transform = getAnnotationArrowTransform(
        obj.left ?? 0,
        obj.top ?? 0,
        rad,
        isSelected ? ANN_RADIUS_SELECTED : ANN_RADIUS,
        zoom
      );
      deco.angleIndicator.set({
        left: transform.x,
        top: transform.y,
        angle: transform.angle
      });
    }
  }
  if (fabricCanvas) fabricCanvas.renderAll();
}

function handleObjectModifiedied(opt: any) {
  const obj = opt.target;
  if (!obj) return;
  const data = getElementData(obj);
  if (!data) return;

  isDraggingObject = false;
  obj.setCoords();

  const updates: Record<string, any> = {};
  updates.x = obj.left;
  updates.y = obj.top;

  if (data.type === 'annotation') {
    // 点位旋转：把 Fabric 角度（度）转回 ROS 弧度；只在确有旋转时更新
    if (Math.abs(obj.angle ?? 0) > 0.01) {
      const rad = fabricAngleToAnnotationRad(obj.angle ?? 0);
      updates.angle = rad;
      // 重置 circle 的 fabric angle 为 0，避免下次旋转累积（点位圆旋转对称，重置无视觉影响）
      obj.set({ angle: 0 });
      obj.setCoords();
    }
  }

  if (data.type === 'object') {
    // 旋转角度始终保存
    updates.angle = obj.angle ?? 0;
    // 应用 scale 到 width/height，并对最小尺寸做 clamp（最小 1×1 px）
    if (obj instanceof Ellipse) {
      const newRx = Math.max(MIN_OBJECT_SIZE / 2, (obj.rx ?? 1) * (obj.scaleX ?? 1));
      const newRy = Math.max(MIN_OBJECT_SIZE / 2, (obj.ry ?? 1) * (obj.scaleY ?? 1));
      obj.set({ rx: newRx, ry: newRy, scaleX: 1, scaleY: 1 });
      updates.width = newRx * 2;
      updates.height = newRy * 2;
    } else if (obj instanceof Polygon) {
      // 多边形禁区：scale 保留在 fabric 对象上，不归一化（points 不动），
      // 仅保证最小可视尺寸
      const minSx = MIN_OBJECT_SIZE / (obj.width || 1);
      const minSy = MIN_OBJECT_SIZE / (obj.height || 1);
      const sx = Math.max(minSx, obj.scaleX ?? 1);
      const sy = Math.max(minSy, obj.scaleY ?? 1);
      obj.set({ scaleX: sx, scaleY: sy });
    } else {
      // Rect / Triangle：归一化 scale 到 width/height
      const newW = Math.max(MIN_OBJECT_SIZE, (obj.width ?? 1) * (obj.scaleX ?? 1));
      const newH = Math.max(MIN_OBJECT_SIZE, (obj.height ?? 1) * (obj.scaleY ?? 1));
      obj.set({ width: newW, height: newH, scaleX: 1, scaleY: 1 });
      updates.width = newW;
      updates.height = newH;
    }
  }

  isLocalUpdate = true;
  emit('update-element', { type: data.type, id: data.id, updates });
  // 拖动/缩放结束后立即同步标签位置（watch 被 isLocalUpdate 短路，不会自动刷新）
  if (data.type === 'object') {
    updateObjectLabelPosition(obj, data.id);
    if (fabricCanvas) fabricCanvas.renderAll();
  }
  nextTick(() => {
    isLocalUpdate = false;
  });
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
  // offsetX/offsetY 是相对画布元素的坐标，clientX/clientY 是视口坐标；
  // 画布不在视口原点时，必须用画布相对坐标才能按鼠标位置缩放
  fabricCanvas.zoomToPoint(new Point(evt.offsetX, evt.offsetY), zoom);
  currentZoom = zoom;
  sliderZoomValue.value = sliderValueToZoom(zoom);
  fabricCanvas.getObjects().forEach((o: any) => {
    if (typeof o.setCoords === 'function') o.setCoords();
  });
  applyMarkerZoom();
  updateMinimap();
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

function findElementAtScenePoint(x: number, y: number): { type: 'annotation' | 'object'; id: number } | null {
  if (!fabricCanvas) return null;
  const point = new Point(x, y);
  // annotation 在视觉顶层，优先匹配；其次 object
  for (const layer of ['annotation', 'object'] as const) {
    for (const [key, obj] of elementMap) {
      if (!key.startsWith(`${layer}-`)) continue;
      if (typeof obj.containsPoint === 'function' && obj.containsPoint(point)) {
        const data = getElementData(obj);
        if (data) return { type: layer, id: data.id };
      }
    }
  }
  return null;
}

// 机器人标记命中检测（仅用于 hover 展示信息；机器人不参与选中/右键/删除）
function findRobotAtScenePoint(x: number, y: number): { type: 'robot'; id: number } | null {
  if (!fabricCanvas) return null;
  const point = new Point(x, y);
  for (const [id, marker] of robotMarkers) {
    if (typeof marker.circle.containsPoint === 'function' && marker.circle.containsPoint(point)) {
      return { type: 'robot', id };
    }
  }
  return null;
}

function handleContextMenu(evt: MouseEvent) {
  if (!fabricCanvas) return;
  evt.preventDefault();
  const pointer = fabricCanvas.getScenePoint(evt);
  const target = findElementAtScenePoint(pointer.x, pointer.y);
  emit('context-menu', {
    x: pointer.x,
    y: pointer.y,
    clientX: evt.clientX,
    clientY: evt.clientY,
    target
  });
}

function handleKeyDown(evt: KeyboardEvent) {
  if (evt.code === 'Space') {
    spacePressed = true;
    evt.preventDefault();
    return;
  }
  const target = evt.target as HTMLElement | null;
  if (target && /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName)) return;
  if (evt.ctrlKey || evt.metaKey) {
    if (evt.code === 'KeyZ' && !evt.shiftKey) {
      evt.preventDefault();
      emit('undo');
    } else if ((evt.code === 'KeyZ' && evt.shiftKey) || evt.code === 'KeyY') {
      evt.preventDefault();
      emit('redo');
    }
  }
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
    targetFindTolerance: 8,
    perPixelTargetFind: false
  });
  fabricCanvas.on('mouse:down', handleMouseDown);
  fabricCanvas.on('mouse:move', handleMouseMove);
  fabricCanvas.on('mouse:up', handleMouseUp);
  fabricCanvas.on('mouse:dblclick', handleDoubleClick);
  fabricCanvas.on('mouse:wheel', handleMouseWheel);
  fabricCanvas.on('mouse:out', () => emit('hover-element', null));
  fabricCanvas.on('object:moving', handleObjectMoved);
  fabricCanvas.on('object:scaling', handleObjectScaling);
  fabricCanvas.on('object:rotating', handleObjectRotating);
  fabricCanvas.on('object:modified', handleObjectModifiedied);
  fabricCanvas.on('selection:created', handleObjectSelected);
  fabricCanvas.on('selection:updated', handleObjectSelected);
  fabricCanvas.on('selection:cleared', handleSelectionCleared);

  const upperCanvas = (fabricCanvas as any).upperCanvasEl as HTMLCanvasElement | undefined;
  if (upperCanvas) {
    upperCanvas.addEventListener('contextmenu', handleContextMenu as EventListener);
  }

  resizeObserver = new ResizeObserver(entries => {
    for (const entry of entries) {
      containerWidth.value = entry.contentRect.width;
      containerHeight.value = entry.contentRect.height;
    }
  });
  resizeObserver.observe(canvasContainer.value);
}

function disposeCanvas() {
  if (cursorEmitRafId !== null) {
    cancelAnimationFrame(cursorEmitRafId);
    cursorEmitRafId = null;
  }
  if (minimapRafId !== null) {
    cancelAnimationFrame(minimapRafId);
    minimapRafId = null;
  }
  if (clickTimer !== null) {
    window.clearTimeout(clickTimer);
    clickTimer = null;
  }
  if (fabricCanvas) {
    const upperCanvas = (fabricCanvas as any).upperCanvasEl as HTMLCanvasElement | undefined;
    if (upperCanvas) {
      upperCanvas.removeEventListener('contextmenu', handleContextMenu as EventListener);
    }
    fabricCanvas.dispose();
    fabricCanvas = null;
  }
  elementMap.clear();
  annotationDecorations.clear();
  objectLabels.clear();
  robotMarkers.clear();
  isDraggingObject = false;
  justDragged = false;
}

watch([containerWidth, containerHeight], () => {
  if (!fabricCanvas) return;
  fabricCanvas.setDimensions({ width: containerWidth.value, height: containerHeight.value });
  centerContent();
});

let loadSeq = 0;

watch(
  () => props.editorData,
  async newData => {
    if (!newData) return;
    const seq = ++loadSeq;

    for (const [, obj] of elementMap) {
      fabricCanvas?.remove(obj);
    }
    elementMap.clear();
    for (const { text, angleIndicator } of annotationDecorations.values()) {
      fabricCanvas?.remove(text);
      fabricCanvas?.remove(angleIndicator);
    }
    annotationDecorations.clear();
    for (const label of objectLabels.values()) {
      fabricCanvas?.remove(label);
    }
    objectLabels.clear();
    clearRobotMarkers();

    if (newData.map.image_id) {
      await loadBackgroundImage(newData.map.image_id);
      // renderElements 会在 loadBackgroundImage 完成后调用
    } else {
      canvasWidth.value = newData.map.width || 800;
      canvasHeight.value = newData.map.height || 600;
      if (fabricCanvas) {
        fabricCanvas.setDimensions({
          width: containerWidth.value || canvasContainer.value!.clientWidth,
          height: containerHeight.value || canvasContainer.value!.clientHeight
        });
        centerContent();
      }
      nextTick(() => renderElements());
    }

    // if (seq !== loadSeq) return;
    // renderElements();
  },
  { deep: false }
);

watch(
  () => props.editorData?.annotations,
  () => {
    if (isLocalUpdate || isDraggingObject || !fabricCanvas) return;
    syncStructure();
    updatePositions();
    updateSelectionStyle();
    fabricCanvas.renderAll();
  },
  { deep: true }
);
watch(
  () => props.editorData?.paths,
  () => {
    if (isLocalUpdate || isDraggingObject || !fabricCanvas) return;
    syncStructure();
    updatePositions();
    updateSelectionStyle();
    fabricCanvas.renderAll();
  },
  { deep: true }
);
watch(
  () => props.editorData?.objects,
  () => {
    if (isLocalUpdate || isDraggingObject || !fabricCanvas) return;
    syncStructure();
    updatePositions();
    updateSelectionStyle();
    fabricCanvas.renderAll();
  },
  { deep: true }
);
watch(
  () => props.robotLocations,
  () => {
    if (!fabricCanvas) return;
    renderRobots();
  },
  { deep: true }
);
watch(
  () => props.selectedElement,
  () => {
    if (!fabricCanvas) return;
    updateSelectionStyle();
    updateSelection();

    // 选中点位时把它拉到顶层，避免被其他点位遮盖
    const sel = props.selectedElement;
    if (sel?.type === 'annotation') {
      const key = getElementKey('annotation', sel.id);
      const circle = elementMap.get(key);
      const deco = annotationDecorations.get(sel.id);
      if (circle) fabricCanvas.bringObjectToFront(circle);
      if (deco) {
        fabricCanvas.bringObjectToFront(deco.angleIndicator);
        fabricCanvas.bringObjectToFront(deco.text);
      }
    }

    fabricCanvas.renderAll();
  }
);

onMounted(async () => {
  await loadSceneList();
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
  const dataUrl = fabricCanvas.toDataURL({ format, quality: 1, multiplier: 2 });
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
  applyMarkerZoom();
  emit('zoom-change', newZoom);
}

function zoomOut() {
  if (!fabricCanvas) return;
  const newZoom = Math.max(currentZoom / 1.2, MIN_ZOOM);
  const center = fabricCanvas.getCenterPoint();
  fabricCanvas.zoomToPoint(center, newZoom);
  currentZoom = newZoom;
  sliderZoomValue.value = sliderValueToZoom(newZoom);
  applyMarkerZoom();
  emit('zoom-change', newZoom);
}

function zoomReset() {
  if (!fabricCanvas) return;
  currentZoom = 1;
  sliderZoomValue.value = sliderValueToZoom(1);
  centerContent();
  applyMarkerZoom();
  emit('zoom-change', 1);
}

function locatePixelPoint(x: number, y: number) {
  if (!fabricCanvas) return;
  const zoom = Math.max(currentZoom, MIN_ZOOM);
  const offsetX = containerWidth.value / 2 - x * zoom;
  const offsetY = containerHeight.value / 2 - y * zoom;
  fabricCanvas.setViewportTransform([zoom, 0, 0, zoom, offsetX, offsetY]);
  fabricCanvas.renderAll();
  updateMinimap();
}

function handleSliderZoom(val: number) {
  if (!fabricCanvas) return;
  const newZoom = zoomToSliderValue(val);
  const center = fabricCanvas.getCenterPoint();
  fabricCanvas.zoomToPoint(center, newZoom);
  currentZoom = newZoom;
  applyMarkerZoom();
  emit('zoom-change', newZoom);
}

defineExpose({ exportCanvas, zoomIn, zoomOut, zoomReset, locatePixelPoint });
</script>

<template>
  <div ref="canvasContainer" class="relative h-full w-full overflow-hidden bg-gray-100">
    <canvas ref="canvasEl" />

    <!-- Legend -->
    <div v-if="editorData"
      class="absolute left-12px top-12px z-10 flex flex-col gap-6px rounded-lg bg-white/90 px-12px py-8px text-xs shadow-md">
      <div class="max-w-180px truncate text-sm text-gray-700 font-medium">{{ editorData.map.name }}</div>
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
        <span class="inline-block h-10px w-10px rounded-full" style="background-color: #ef4444"></span>
        <span>机器人位置</span>
      </div>
      <div class="flex items-center gap-6px">
        <span class="inline-block h-10px w-10px"
          style="background-color: rgba(59, 130, 246, 0.3); border: 1px solid #3b82f6"></span>
        <span>障碍物</span>
      </div>
      <div class="flex items-center gap-6px">
        <span class="inline-block h-10px w-10px" style="
            background-image: linear-gradient(135deg, transparent 45%, #6b7280 45%, #6b7280 55%, transparent 55%);
            background-color: rgba(107, 114, 128, 0.12);
            border: 1px solid #6b7280;
          "></span>
        <span>禁行区域/虚拟墙</span>
      </div>
      <div class="flex items-center gap-6px">
        <span class="inline-block h-10px w-10px"
          style="background-color: rgba(239, 68, 68, 0.15); border: 2px solid #ef4444"></span>
        <span>电子围栏</span>
      </div>
    </div>
    <div v-if="!editorData" class="absolute inset-0 flex items-center justify-center">
      <NEmpty description="请选择一个场景" />
    </div>
    <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white/60">
      <NSpin size="large" />
    </div>

    <!-- Zoom slider control -->
    <div v-if="editorData"
      class="absolute right-12px top-12px z-10 flex flex-col items-center gap-4px rounded-lg bg-white/90 px-6px py-8px shadow-md">
      <button
        class="h-24px w-24px flex items-center justify-center rounded-full text-sm text-blue-500 font-bold transition-colors hover:bg-blue-50"
        @click="zoomIn">
        +
      </button>
      <NSlider v-model:value="sliderZoomValue" vertical :min="0" :max="100" :step="1" :tooltip="false"
        :theme-overrides="sliderThemeOverrides" class="!h-160px" @update:value="handleSliderZoom" />
      <button
        class="h-24px w-24px flex items-center justify-center rounded-full text-sm text-blue-500 font-bold transition-colors hover:bg-blue-50"
        @click="zoomOut">
        -
      </button>
      <div class="text-xs text-gray-500">{{ Math.round(currentZoom * 100) }}%</div>
    </div>

    <!-- Cursor coordinates (placed above minimap) -->
    <div v-if="editorData" class="absolute left-12px z-10 rounded bg-black/50 px-8px py-4px text-xs text-white"
      :style="{ bottom: minimapImageUrl ? `${MINIMAP_SIZE + 24}px` : '12px' }">
      坐标: {{ cursorWorldX.toFixed(2) }}m, {{ cursorWorldY.toFixed(2) }}m
    </div>

    <!-- Minimap navigator -->
    <div v-if="editorData && minimapImageUrl" ref="minimapEl"
      class="absolute bottom-12px left-12px z-10 cursor-pointer overflow-hidden border border-gray-300 rounded-lg bg-white shadow-md"
      :style="{ width: `${MINIMAP_SIZE}px`, height: `${MINIMAP_SIZE}px` }" @mousedown="handleMinimapDown"
      @mousemove="handleMinimapMove" @mouseup="handleMinimapUp" @mouseleave="handleMinimapUp">
      <img :src="minimapImageUrl" :style="{
        position: 'absolute',
        left: `${minimapScale.ox}px`,
        top: `${minimapScale.oy}px`,
        width: `${minimapScale.w}px`,
        height: `${minimapScale.h}px`,
        objectFit: 'fill',
        pointerEvents: 'none'
      }" />
      <!-- Viewport rect: blue border + massive box-shadow as outer mask -->
      <div :style="{
        position: 'absolute',
        left: `${minimapRect.x}px`,
        top: `${minimapRect.y}px`,
        width: `${minimapRect.w}px`,
        height: `${minimapRect.h}px`,
        border: '2px solid #3b82f6',
        backgroundColor: 'transparent',
        boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.45)',
        pointerEvents: 'none'
      }" />
    </div>
  </div>
</template>
