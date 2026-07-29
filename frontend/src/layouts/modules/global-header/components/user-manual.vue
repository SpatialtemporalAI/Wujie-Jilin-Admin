<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue';
import { NModal, NScrollbar } from 'naive-ui';
import { marked } from 'marked';
import manualContent from '@/assets/files/机器人管理系统用户手册.md?raw';
import wifiGuide from '@/assets/files/机器人WIFI配网指南.md?raw';
import apiDoc from '@/assets/files/商户开放API接入文档.md?raw';
import backpackWifiGuide from '@/assets/files/语音背包wifi配网操作指南.md?raw';
import ButtonIcon from '@/components/custom/button-icon.vue';

defineOptions({ name: 'UserManual' });

interface HeadingItem {
  level: number;
  text: string;
  id: string;
}

const showModal = ref(false);
const activeDoc = ref('main');
const contentRef = ref<HTMLElement | null>(null);

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

// md 文件名 -> doc key 映射
const mdLinkMap: Record<string, string> = {
  '机器人WIFI配网指南.md': 'wifi',
  '语音背包wifi配网操作指南.md': 'backpack',
  '商户开放API接入文档.md': 'api'
};

/** 根据标题文本推断层级 */
function getHeadingLevel(text: string): number {
  if (/^[一二三四五六七八九十]+、/.test(text)) return 1;
  if (text.startsWith('附录')) return 1;
  if (/^\d+\.\d+\.\d+/.test(text)) return 3;
  if (/^\d+\.\d+/.test(text)) return 2;
  return 1;
}

/** 从主手册提取标题树 */
function extractHeadings(): HeadingItem[] {
  const headings: HeadingItem[] = [];
  const lines = manualContent.split('\n');
  // 匹配 <a id="heading_X"></a>__标题__
  const regex = /<a id="heading_(\d+)"><\/a>__(.+)__/;
  for (const line of lines) {
    const match = line.match(regex);
    if (match) {
      const id = `heading_${match[1]}`;
      const text = match[2].replace(/\\\./g, '.').trim();
      headings.push({ level: getHeadingLevel(text), text, id });
    }
  }
  return headings;
}

/** 渲染内容 */
function renderContent(docKey: string): string {
  let content = docContents[docKey] || '';

  // 删除主手册顶部标题行 "__机器人管理系统用户手册 __"
  if (docKey === 'main') {
    content = content.replace(/^__机器人管理系统用户手册 __\n/, '');
  }

  let html = marked.parse(content, { gfm: true, breaks: false }) as string;

  // 图片路径修正
  html = html.replace(/src="manual-images\//g, 'src="/manual-images/');

  // 替换 md 文件引用为可点击链接
  html = html.replace(/<strong>\[([^\]]+\.md)\]<\/strong>/g, (_match, filename: string) => {
    const key = mdLinkMap[filename];
    if (key) {
      return `<span class="md-view-link" data-doc="${key}" style="display:inline-block;padding:6px 12px;margin:8px 0;border-radius:6px;font-size:13px;font-weight:500;color:#2563eb;background-color:#eff6ff;border:1px solid #bfdbfe;cursor:pointer;">📄 查看详情：${docTitles[key]}</span>`;
    }
    return `<strong>[${filename}]</strong>`;
  });

  // 替换视频引用为 HTML video 标签
  html = html.replace(
    /<p>唤醒词唤醒\\?\+多轮对话\\?\.mp4<\/p>/g,
    '<video controls style="max-width:100%;border-radius:8px;margin:12px 0;"><source src="/videos/demo.mp4" type="video/mp4">您的浏览器不支持视频播放</video>'
  );

  return html;
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
    contentRef.value?.scrollTo({ top: 0, behavior: 'instant' });
  });
}

function handleContentClick(e: MouseEvent) {
  const target = e.target as HTMLElement;
  const link = target.closest('.md-view-link') as HTMLElement | null;
  if (link) {
    const docKey = link.dataset.doc;
    if (docKey && docContents[docKey]) {
      activeDoc.value = docKey;
      nextTick(() => {
        contentRef.value?.scrollTo({ top: 0, behavior: 'instant' });
      });
    }
  }
}

watch(showModal, visible => {
  if (visible) {
    activeDoc.value = 'main';
  }
});
</script>

<template>
  <div>
    <ButtonIcon icon="mdi:book-open-outline" tooltip-content="用户手册" @click="showModal = true" />

    <NModal v-model:show="showModal" preset="card" title="用户手册" style="width: 90vw; max-width: 1200px"
      body-style="padding: 0;" :bordered="false" :segmented="{ content: true }">
      <div class="manual-container">
        <div class="manual-sidebar">
          <NScrollbar class="sidebar-scroll">
            <div class="sidebar-content">
              <div class="sidebar-title">机器人管理系统用户手册</div>
              <div class="toc-divider"></div>
              <div class="toc-list">
                <div v-for="heading in headings" :key="heading.id" class="toc-item"
                  :class="`toc-level-${heading.level}`" @click="scrollToHeading(heading.id)">
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
  height: 77vh;
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
  transition:
    background-color 0.2s,
    color 0.2s;
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

.markdown-body :deep(p) {
  margin-bottom: 12px;
  line-height: 1.8;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 24px;
  margin-bottom: 14px;
}

.markdown-body :deep(li) {
  margin-bottom: 6px;
  line-height: 1.7;
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
