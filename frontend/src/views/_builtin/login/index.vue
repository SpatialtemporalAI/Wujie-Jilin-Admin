<script setup lang="ts">
import { computed } from 'vue';
import type { Component } from 'vue';
import { getPaletteColorByNumber, mixColor } from '@sa/color';
import { loginModuleRecord } from '@/constants/app';
import { useAppStore } from '@/store/modules/app';
import { useThemeStore } from '@/store/modules/theme';
import { $t } from '@/locales';
import PwdLogin from './modules/pwd-login.vue';
import CodeLogin from './modules/code-login.vue';
import Register from './modules/register.vue';
import ResetPwd from './modules/reset-pwd.vue';
import BindWechat from './modules/bind-wechat.vue';

interface Props {
  /** The login module */
  module?: UnionKey.LoginModule;
}

const props = defineProps<Props>();

const appStore = useAppStore();
const themeStore = useThemeStore();

interface LoginModule {
  label: App.I18n.I18nKey;
  component: Component;
}

const moduleMap: Record<UnionKey.LoginModule, LoginModule> = {
  'pwd-login': { label: loginModuleRecord['pwd-login'], component: PwdLogin },
  'code-login': { label: loginModuleRecord['code-login'], component: CodeLogin },
  register: { label: loginModuleRecord.register, component: Register },
  'reset-pwd': { label: loginModuleRecord['reset-pwd'], component: ResetPwd },
  'bind-wechat': { label: loginModuleRecord['bind-wechat'], component: BindWechat }
};

const activeModule = computed(() => moduleMap[props.module || 'pwd-login']);

const bgThemeColor = computed(() =>
  themeStore.darkMode ? getPaletteColorByNumber(themeStore.themeColor, 600) : themeStore.themeColor
);

const bgColor = computed(() => {
  const COLOR_WHITE = '#ffffff';

  const ratio = themeStore.darkMode ? 0.5 : 0.2;

  return mixColor(COLOR_WHITE, themeStore.themeColor, ratio);
});
</script>

<template>
  <div class="relative size-full flex-center overflow-hidden" :style="{ backgroundColor: bgColor }">
    <img src="@/assets/imgs/login-bg.png" alt="" class="l-0 r-0 t-0 absolute h-full w-full b-0 object-cover" />
    <NCard :bordered="false" class="logo-glass absolute z-4 w-auto rd-12px">
      <div class="w-324px lt-sm:w-300px">
        <div class="mb-14px flex items-center justify-center">
          <img src="@/assets/imgs/logo.png" alt="" class="mr-10px h-24px w-24px object-contain" />
          <img src="@/assets/imgs/lvyaText.png" alt="" class="h-24px object-contain" />
        </div>
        <header class="flex-y-center justify-center">
          <h3 class="text-28px font-500 lt-sm:text-24px">{{ $t('system.title') }}</h3>
          <!--
 <div class="i-flex-col">
            <ThemeSchemaSwitch
              :theme-schema="themeStore.themeScheme"
              :show-tooltip="false"
              class="text-20px lt-sm:text-18px"
              @switch="themeStore.toggleThemeScheme"
            />
            <LangSwitch
              v-if="themeStore.header.multilingual.visible"
              :lang="appStore.locale"
              :lang-options="appStore.localeOptions"
              :show-tooltip="false"
              @change-lang="appStore.changeLocale"
            />
          </div> 
-->
        </header>
        <main class="pt-20px">
          <!-- <h3 class="text-18px text-primary font-medium">{{ $t(activeModule.label) }}</h3> -->
          <div class="pt-24px">
            <Transition :name="themeStore.page.animateMode" mode="out-in" appear>
              <component :is="activeModule.component" />
            </Transition>
          </div>
        </main>
      </div>
    </NCard>
  </div>
</template>

<style scoped lang="scss">
.logo-glass {
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px); /* 兼容Safari */
  background-color: rgba(255, 255, 255, 0.33);
  right: 10%;
  transition: all 0.3s;
  transform: scale(1.08);
  &:hover {
    background-color: rgba(255, 255, 255, 0.39);
    backdrop-filter: blur(18px);
  }
}
</style>
