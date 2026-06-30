/**
 * 机器人位置解析工具
 *
 * 机器人实时位置由外部写入 DB（不在本平台代码内），可能落到两个字段之一：
 * - location_info（JSON 列，结构 { x, y, angle, update_at }，优先）
 * - location（Text 列，历史 JSON 字符串，兜底）
 *
 * 这里统一解析出世界坐标（米），供「画布显示机器人位置」与「定位」复用，
 * 消除两处分歧。解析失败返回 null。
 */

interface RobotLocationSource {
  location_info?: { x?: number; y?: number; angle?: number } | null;
  location?: string | null;
}

export interface RobotPoint {
  x: number;
  y: number;
  angle?: number;
}

function isFiniteNumber(v: unknown): v is number {
  return typeof v === 'number' && Number.isFinite(v);
}

/**
 * 从 status/location 数据中解析机器人世界坐标。
 * 优先 location_info.x/y；为空则 JSON.parse(location) 取 x/y；
 * 再失败则从字符串中提取前两个数字（兼容历史脏数据）。
 */
export function extractRobotPoint(src: RobotLocationSource | null | undefined): RobotPoint | null {
  if (!src) return null;

  // 1) location_info
  const info = src.location_info;
  if (info && isFiniteNumber(info.x) && isFiniteNumber(info.y)) {
    return { x: info.x, y: info.y, angle: isFiniteNumber(info.angle) ? info.angle : undefined };
  }

  // 2) location 文本
  const raw = src.location;
  if (raw) {
    let parsed: any = null;
    try {
      parsed = JSON.parse(raw);
    } catch {
      parsed = null;
    }
    if (parsed && typeof parsed === 'object') {
      const px = (parsed as any).x;
      const py = (parsed as any).y;
      if (isFiniteNumber(px) && isFiniteNumber(py)) {
        return { x: px, y: py, angle: isFiniteNumber(parsed.angle) ? parsed.angle : undefined };
      }
    }

    // 3) 字符串里提取前两个数字
    const nums = raw.match(/-?\d+(\.\d+)?/g);
    if (nums && nums.length >= 2) {
      const x = Number(nums[0]);
      const y = Number(nums[1]);
      if (isFiniteNumber(x) && isFiniteNumber(y)) {
        return { x, y };
      }
    }
  }

  return null;
}
