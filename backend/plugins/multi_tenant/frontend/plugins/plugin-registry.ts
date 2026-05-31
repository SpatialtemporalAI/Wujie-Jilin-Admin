import type { Component } from 'vue';

type HeaderPlugin = Component;

const _headerPlugins: HeaderPlugin[] = [];

export function registerHeaderPlugin(component: HeaderPlugin) {
  _headerPlugins.push(component);
}

export function getHeaderPlugins(): HeaderPlugin[] {
  return _headerPlugins;
}
