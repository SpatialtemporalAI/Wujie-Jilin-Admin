import { ref } from 'vue';
import { useMessage } from 'naive-ui';
import { fetchSubmitExportTask } from '@/service/api';
import { $t } from '@/locales';

/**
 * 导出提交 hook
 * 仅负责提交异步导出任务并提示用户，文件下载由顶栏「下载箱」统一处理。
 */
export function useExportSubmit() {
  const message = useMessage();
  const submitting = ref(false);

  /**
   * 提交当前查询条件下的导出任务
   * @param moduleKey 后端 export 注册的 module_key
   * @param searchParams 页面 reactive 查询条件（自动剔除 page / page_size）
   */
  async function submitExport(moduleKey: string, searchParams: Record<string, any>) {
    if (submitting.value) return;
    submitting.value = true;
    try {
      // 导出为全量，剔除分页参数
      const queryParams = Object.fromEntries(
        Object.entries(searchParams).filter(([k]) => k !== 'page' && k !== 'page_size')
      );
      const { error } = await fetchSubmitExportTask({
        module_key: moduleKey,
        query_params: queryParams
      });
      if (!error) {
        message.success($t('common.exportTaskSubmitted'));
        // 通知顶栏下载箱立即刷新
        window.dispatchEvent(new CustomEvent('export:task-submitted'));
      }
    } catch (e) {
      console.error('提交导出任务失败:', e);
    } finally {
      submitting.value = false;
    }
  }

  return {
    submitting,
    submitExport
  };
}
