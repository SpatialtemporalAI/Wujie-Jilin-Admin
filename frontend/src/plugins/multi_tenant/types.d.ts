declare namespace App.I18n {
  interface PluginI18nSchema {
    page: {
      manage: {
        tenant: {
          title: string;
          tenantName: string;
          tenantCode: string;
          contactName: string;
          maxUsers: string;
          description: string;
          contactEmail: string;
          contactPhone: string;
          maxUsersLabel: string;
          selectTenant: string;
          addTenant: string;
          editTenant: string;
          deleteTenant: string;
          confirmDelete: string;
          deleteSuccess: string;
          createSuccess: string;
          updateSuccess: string;
          statusUpdateSuccess: string;
          switchedTenant: string;
          form: {
            tenantName: string;
            tenantCode: string;
            tenantCodeRule: string;
            tenantCodePlaceholder: string;
            description: string;
            contactName: string;
            contactEmail: string;
            contactPhone: string;
          };
          search: {
            name: string;
            code: string;
            namePlaceholder: string;
            codePlaceholder: string;
          };
        };
      };
    };
  }
}
