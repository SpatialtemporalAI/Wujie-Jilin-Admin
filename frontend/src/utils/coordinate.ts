/** 画布像素坐标 → 世界坐标（米） */
export function pixelToWorld(pixelX: number, pixelY: number, originX: number, originY: number, resolution: number) {
  return {
    x: pixelX * resolution + originX,
    y: pixelY * resolution + originY,
  };
}

/** 世界坐标（米）→ 画布像素坐标 */
export function worldToPixel(worldX: number, worldY: number, originX: number, originY: number, resolution: number) {
  return {
    x: (worldX - originX) / resolution,
    y: (worldY - originY) / resolution,
  };
}

/** 像素差值 → 米（用于距离计算，不需要原点偏移） */
export function pixelsDeltaToMeters(deltaPx: number, resolution: number): number {
  return deltaPx * resolution;
}

/** 米 → 像素差值 */
export function metersDeltaToPixels(deltaM: number, resolution: number): number {
  return deltaM / resolution;
}
