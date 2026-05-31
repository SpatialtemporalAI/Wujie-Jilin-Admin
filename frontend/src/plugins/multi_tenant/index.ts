import { registerHeaderPlugin, registerPluginI18n } from '../plugin-registry';
import TenantSwitcher from './components/TenantSwitcher.vue';
import zhCN from './locale/zh-CN';
import enUS from './locale/en-US';

export { useTenantStore } from './store/tenant';

registerHeaderPlugin(TenantSwitcher);
registerPluginI18n('multi_tenant', { 'zh-CN': zhCN, 'en-US': enUS });
