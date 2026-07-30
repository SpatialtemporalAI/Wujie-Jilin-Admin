<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue';
import { NModal, NScrollbar } from 'naive-ui';
import { marked } from 'marked';
import ButtonIcon from '@/components/custom/button-icon.vue';
import manualContent from '@/assets/manual-files/机器人管理系统用户手册.md?raw';
import wifiGuide from '@/assets/manual-files/机器人WIFI配网指南.md?raw';
import apiDoc from '@/assets/manual-files/商户开放API接入文档.md?raw';
import backpackWifiGuide from '@/assets/manual-files/语音背包wifi配网操作指南.md?raw';

defineOptions({ name: 'UserManual' });

interface HeadingItem {
  level: number;
  text: string;
  id: string;
}

const showModal = ref(false);
const activeDoc = ref('main');
const contentRef = ref<HTMLElement | null>(null);
const mainScrollTop = ref(0);
const activeHeadingId = ref('');

const docContents: Record<string, string> = {
  main: manualContent,
  wifi: wifiGuide,
  api: apiDoc,
  backpack: backpackWifiGuide
};

const docTitles: Record<string, string> = {
  main: '机器人管理系统用户手册',
  wifi: '机器人 WiFi 配网指南',
  api: '商户开放 API 接入文档',
  backpack: '语音背包 WiFi 配网操作指南'
};

const mdLinkMap: Record<string, string> = {
  '机器人WIFI配网指南.md': 'wifi',
  '语音背包wifi配网操作指南.md': 'backpack',
  '商户开放API接入文档.md': 'api'
};

/** 预处理 Markdown 内容，修复转义和列表问题 */
function preprocessMarkdown(content: string): string {
  let processed = content;

  // 1. 处理标题行中的转义点号（如 ### 3\.2\.1 → ### 3.2.1）
  processed = processed.replace(/^(#{1,6}\s+)([\d\.\\]+)(\s.*)$/gm, (_match, prefix, numbers, suffix) => {
    return prefix + numbers.replace(/\\\./g, '.') + suffix;
  });

  // 2. 处理图片和链接中的转义（alt text 和 href 都要处理）
  processed = processed.replace(/(!?\[)([^\]]*?)(\]\()([^)]+)(\))/g, (_match, bang, alt, mid, href, end) => {
    const cleanAlt = alt.replace(/\\\./g, '.');
    const cleanHref = href.replace(/\\\./g, '.');
    return bang + cleanAlt + mid + cleanHref + end;
  });

  return processed;
}

/** 渲染 markdown，生成带 id 的标题 */
function renderContent(docKey: string): string {
  const content = preprocessMarkdown(docContents[docKey] || '');
  let headingIndex = 0;
  const renderer = new marked.Renderer();

  renderer.heading = ({ text, depth }) => {
    const id = `heading-${headingIndex++}`;
    const cleanText = text.replace(/\\\./g, '.');
    return `<h${depth} id="${id}">${cleanText}</h${depth}>`;
  };

  renderer.link = ({ href, title, text }) => {
    // 检查是否为 md 文件链接（href 可能是 "图片和附件/机器人WIFI配网指南.md"）
    if (href.endsWith('.md')) {
      // 从路径中提取文件名
      const filename = href.split('/').pop() || '';
      const mdKey = mdLinkMap[filename];
      if (mdKey) {
        return `<span class="md-view-link" data-doc="${mdKey}" title="${title || ''}">📄 查看详情：${text}</span>`;
      }
    }
    // 视频链接处理（支持带查询参数的 URL）
    if (/\.mp4(\?|$)/.test(href)) {
      // 远程 URL 直接使用，本地路径添加前缀
      const videoSrc = href.startsWith('http') ? href : `/manual-files/${href}`;
      return `<video controls style="max-width:100%;border-radius:8px;margin:12px 0;"><source src="${videoSrc}" type="video/mp4">您的浏览器不支持视频播放</video>`;
    }
    return `<a href="${href}" title="${title || ''}" target="_blank" rel="noopener noreferrer">${text}</a>`;
  };

  renderer.image = ({ href, title, text }) => {
    return `<img src="/manual-files/${href}" alt="${text}" title="${title || ''}" style="max-width:100%;border-radius:6px;margin:12px 0;" />`;
  };

  let html = marked.parse(content, { renderer, gfm: true, breaks: true }) as string;

  // 后处理：确保粗体和斜体语法被正确转换（防止 marked 遗漏）
  // 注意：只匹配文本内容中的粗体/斜体，避免破坏 URL 等属性
  // 粗体：**text**（要求 text 不包含特殊字符）
  html = html.replace(/\*\*([^*\n]+?)\*\*/g, (match, text) => {
    // 跳过包含 URL 或 HTML 标签的情况
    if (text.includes('http') || text.includes('<') || text.includes('>')) {
      return match;
    }
    return `<strong>${text}</strong>`;
  });
  // 斜体：*text*（单星号，要求前后无星号）
  html = html.replace(/(?<![<*])\*(?!\*)([^*\n]+?)\*(?![*>])/g, (match, text) => {
    // 跳过包含 URL 或 HTML 标签的情况
    if (text.includes('http') || text.includes('<') || text.includes('>')) {
      return match;
    }
    return `<em>${text}</em>`;
  });

  // 兼容旧版 md 中直接出现的文件名
  html = html.replace(/<strong>\[([^\]]+\.md)\]<\/strong>/g, (_match, filename: string) => {
    const key = mdLinkMap[filename];
    if (key) {
      return `<span class="md-view-link" data-doc="${key}">📄 ${docTitles[key]}</span>`;
    }
    return `<strong>[${filename}]</strong>`;
  });

  return html;
}

/** 从主手册提取标题树 */
function extractHeadings(): HeadingItem[] {
  const headings: HeadingItem[] = [];
  const processed = preprocessMarkdown(manualContent);
  const lines = processed.split('\n');
  const regex = /^(#{1,6})\s+(.+)$/;
  let index = 0;

  for (const line of lines) {
    const match = line.match(regex);
    if (match) {
      const level = match[1].length;
      const text = match[2].trim().replace(/\*\*/g, '');
      headings.push({ level, text, id: `heading-${index++}` });
    }
  }
  return headings;
}

const headings = computed(() => extractHeadings());
const renderedContent = computed(() => renderContent(activeDoc.value));

function scrollToHeading(id: string) {
  activeDoc.value = 'main';
  nextTick(() => {
    const el = document.getElementById(id);
    if (el && contentRef.value) {
      const containerRect = contentRef.value.getBoundingClientRect();
      const elRect = el.getBoundingClientRect();
      const offset = elRect.top - containerRect.top + contentRef.value.scrollTop - 16;
      contentRef.value.scrollTo({ top: offset, behavior: 'smooth' });
    }
  });
}

function backToMain() {
  activeDoc.value = 'main';
  nextTick(() => {
    contentRef.value?.scrollTo({ top: mainScrollTop.value, behavior: 'instant' });
  });
}

function handleContentClick(e: MouseEvent) {
  const target = e.target as HTMLElement;
  const link = target.closest('.md-view-link') as HTMLElement | null;
  if (link) {
    const docKey = link.dataset.doc;
    if (docKey && docContents[docKey]) {
      mainScrollTop.value = contentRef.value?.scrollTop || 0;
      activeDoc.value = docKey;
      nextTick(() => {
        contentRef.value?.scrollTo({ top: 0, behavior: 'instant' });
      });
    }
  }
}

/** 滚动时高亮目录 */
function updateActiveHeadingOnScroll() {
  if (!contentRef.value || activeDoc.value !== 'main') return;

  const container = contentRef.value;
  const containerRect = container.getBoundingClientRect();
  const threshold = containerRect.top + 120;

  let currentId = '';
  for (const heading of headings.value) {
    const el = document.getElementById(heading.id);
    if (!el) continue;

    const elRect = el.getBoundingClientRect();
    if (elRect.top <= threshold) {
      currentId = heading.id;
    } else {
      break;
    }
  }

  if (currentId) {
    activeHeadingId.value = currentId;
  }
}

watch(showModal, visible => {
  if (visible) {
    activeDoc.value = 'main';
    mainScrollTop.value = 0;
    activeHeadingId.value = '';
  }
});

watch(
  () => [contentRef.value, activeDoc.value, showModal.value],
  () => {
    if (contentRef.value && activeDoc.value === 'main' && showModal.value) {
      contentRef.value.addEventListener('scroll', updateActiveHeadingOnScroll);
    }
  },
  { immediate: true }
);
</script>

<template>
  <div>
    <ButtonIcon icon="mdi:book-open-outline" tooltip-content="用户手册" @click="showModal = true" />

    <NModal v-model:show="showModal" preset="card" title="用户手册" style="width: 90vw; max-width: 1200px;"
      body-style="padding: 0;" :bordered="false" :segmented="{ content: true }">
      <div class="manual-container">
        <div class="manual-sidebar">
          <NScrollbar class="sidebar-scroll">
            <div class="sidebar-content">
              <div class="sidebar-title">机器人管理系统用户手册</div>
              <div class="toc-divider"></div>
              <div class="toc-list">
                <div v-for="heading in headings" :key="heading.id" class="toc-item"
                  :class="[`toc-level-${heading.level}`, { 'toc-active': activeHeadingId === heading.id }]"
                  @click="scrollToHeading(heading.id)">
                  {{ heading.text }}
                </div>
              </div>
            </div>
          </NScrollbar>
        </div>
        <div ref="contentRef" class="manual-body" @click="handleContentClick">
          <div v-if="activeDoc !== 'main'" class="back-bar" @click="backToMain">← 返回用户手册</div>
          <div class="markdown-body" v-html="renderedContent"></div>
        </div>
      </div>
    </NModal>
  </div>
</template>

<style scoped>
.manual-container {
  display: flex;
  height: 70vh;
  overflow: hidden;
}

.manual-sidebar {
  width: 280px;
  flex-shrink: 0;
  border-right: 1px solid rgba(156, 163, 175, 0.25);
  background-color: #f9fafb;
}

.dark .manual-sidebar {
  background-color: #111827;
  border-right-color: rgba(75, 85, 99, 0.5);
}

.sidebar-scroll {
  height: 100%;
}

.sidebar-content {
  padding: 16px;
}

.sidebar-title {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  line-height: 1.5;
  padding: 4px 10px 10px;
}

.dark .sidebar-title {
  color: #f3f4f6;
}

.toc-divider {
  height: 1px;
  background-color: rgba(156, 163, 175, 0.25);
  margin: 4px 0 12px;
}

.dark .toc-divider {
  background-color: rgba(75, 85, 99, 0.5);
}

.toc-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.toc-item {
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 13px;
  color: #4b5563;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dark .toc-item {
  color: #9ca3af;
}

.toc-item:hover {
  background-color: #e5e7eb;
  color: #2563eb;
}

.dark .toc-item:hover {
  background-color: #374151;
  color: #60a5fa;
}

.toc-item.toc-active {
  background-color: #eff6ff;
  color: #2563eb;
  font-weight: 500;
}

.dark .toc-item.toc-active {
  background-color: rgba(37, 99, 235, 0.15);
  color: #60a5fa;
}

.toc-level-1 {
  font-weight: 600;
  color: #111827;
  margin-top: 6px;
}

.toc-level-1:first-child {
  margin-top: 0;
}

.dark .toc-level-1 {
  color: #f3f4f6;
}

.toc-level-2 {
  padding-left: 22px;
}

.toc-level-3 {
  padding-left: 34px;
  font-size: 12px;
}

.toc-level-4,
.toc-level-5,
.toc-level-6 {
  padding-left: 44px;
  font-size: 12px;
  color: #6b7280;
}

.manual-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  background-color: #fff;
}

.dark .manual-body {
  background-color: #0b0f19;
}

.back-bar {
  display: inline-block;
  font-size: 13px;
  color: #2563eb;
  cursor: pointer;
  margin-bottom: 16px;
  padding: 6px 12px;
  border-radius: 6px;
  background-color: #eff6ff;
  transition: background-color 0.2s;
}

.dark .back-bar {
  color: #60a5fa;
  background-color: rgba(37, 99, 235, 0.12);
}

.back-bar:hover {
  background-color: #dbeafe;
}

.dark .back-bar:hover {
  background-color: rgba(37, 99, 235, 0.2);
}

.markdown-body :deep(.md-view-link) {
  display: inline-block;
  padding: 6px 12px;
  margin: 8px 0;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #2563eb;
  background-color: #eff6ff;
  border: 1px solid #bfdbfe;
  cursor: pointer;
}

.dark .markdown-body :deep(.md-view-link) {
  color: #60a5fa;
  background-color: rgba(37, 99, 235, 0.15);
  border-color: rgba(96, 165, 250, 0.3);
}

.markdown-body :deep(.md-view-link:hover) {
  background-color: #dbeafe;
}

.markdown-body :deep(h1) {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(156, 163, 175, 0.25);
}

.markdown-body :deep(h2) {
  font-size: 20px;
  font-weight: 600;
  margin-top: 28px;
  margin-bottom: 14px;
}

.markdown-body :deep(h3) {
  font-size: 17px;
  font-weight: 600;
  margin-top: 22px;
  margin-bottom: 12px;
}

.markdown-body :deep(h4) {
  font-size: 15px;
  font-weight: 600;
  margin-top: 18px;
  margin-bottom: 10px;
}

.markdown-body :deep(p) {
  margin-bottom: 12px;
  line-height: 1.8;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 24px;
  margin-bottom: 14px;
}

.markdown-body :deep(ol) {
  list-style-type: decimal;
}

.markdown-body :deep(ul) {
  list-style-type: disc;
}

.markdown-body :deep(li) {
  display: list-item;
  margin-bottom: 6px;
  line-height: 1.7;
}

.markdown-body :deep(li > p) {
  margin-bottom: 4px;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 16px;
  font-size: 13px;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid rgba(156, 163, 175, 0.35);
  padding: 8px 12px;
  text-align: left;
}

.markdown-body :deep(th) {
  background-color: #f3f4f6;
  font-weight: 600;
}

.dark .markdown-body :deep(th) {
  background-color: #1f2937;
}

.markdown-body :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
  margin: 12px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.markdown-body :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  background-color: #f3f4f6;
  padding: 2px 5px;
  border-radius: 4px;
  font-size: 13px;
}

.dark .markdown-body :deep(code) {
  background-color: #1f2937;
}

.markdown-body :deep(pre) {
  background-color: #f3f4f6;
  padding: 14px;
  border-radius: 8px;
  overflow-x: auto;
  margin-bottom: 16px;
}

.dark .markdown-body :deep(pre) {
  background-color: #1f2937;
}

.markdown-body :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid #3b82f6;
  padding-left: 14px;
  margin: 14px 0;
  color: #6b7280;
}

.dark .markdown-body :deep(blockquote) {
  color: #9ca3af;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid rgba(156, 163, 175, 0.25);
  margin: 20px 0;
}

.markdown-body :deep(a) {
  color: #2563eb;
  text-decoration: none;
}

.dark .markdown-body :deep(a) {
  color: #60a5fa;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}
</style>
