export default {
  route: {
    tenant: '租户管理',
    tenant_list: '租户列表'
  },
  page: {
    manage: {
      tenant: {
        title: '租户管理',
        tenantName: '租户名称',
        tenantCode: '租户编码',
        contactName: '联系人',
        maxUsers: '用户上限',
        description: '描述',
        contactEmail: '联系邮箱',
        contactPhone: '联系手机',
        maxUsersLabel: '最大用户数',
        selectTenant: '选择租户',
        addTenant: '新增租户',
        editTenant: '编辑租户',
        deleteTenant: '删除租户',
        confirmDelete: '确认删除该租户？',
        deleteSuccess: '删除成功',
        createSuccess: '创建成功',
        updateSuccess: '更新成功',
        statusUpdateSuccess: '状态更新成功',
        switchedTenant: '已切换到租户',
        form: {
          tenantName: '请输入租户名称',
          tenantCode: '请输入租户编码',
          tenantCodeRule: '仅支持小写字母、数字、下划线和连字符',
          tenantCodePlaceholder: '仅限小写字母、数字',
          description: '租户描述（可选）',
          contactName: '联系人姓名',
          contactEmail: '联系邮箱',
          contactPhone: '联系手机号'
        },
        search: {
          name: '名称',
          code: '编码',
          namePlaceholder: '租户名称',
          codePlaceholder: '租户编码'
        }
      }
    }
  }
};
