/**
 * 解析机器人事件内容并提取 message 字段用于展示。
 *
 * event_content 当前以 JSON 字符串存储（如 {"message": "...", ...}），
 * 此函数安全解析后返回 message；当内容非 JSON 或缺少 message 时回退到原始内容。
 *
 * @param content 原始事件内容
 * @returns 用于展示的 message 文本（无内容时返回空字符串）
 */
export function parseEventContentMessage(content: string | null | undefined): string {
  if (!content) return '';
  try {
    const obj = JSON.parse(content);
    if (obj && typeof obj === 'object' && typeof obj.message === 'string' && obj.message) {
      return obj.message;
    }
  } catch {
    // 非 JSON 格式，回退到原始内容
  }
  return content;
}
