import { registerPluginI18n } from '@/plugins/plugin-registry';
import zhCN from './locale/zh-CN';
import enUS from './locale/en-US';

registerPluginI18n('scheduler', { 'zh-CN': zhCN, 'en-US': enUS });
