export default {
  route: {
    tenant: 'Tenant Management',
    tenant_list: 'Tenant List'
  },
  page: {
    manage: {
      tenant: {
        title: 'Tenant Management',
        tenantName: 'Tenant Name',
        tenantCode: 'Tenant Code',
        contactName: 'Contact',
        maxUsers: 'Max Users',
        description: 'Description',
        contactEmail: 'Contact Email',
        contactPhone: 'Contact Phone',
        maxUsersLabel: 'Max Users',
        selectTenant: 'Select Tenant',
        addTenant: 'Add Tenant',
        editTenant: 'Edit Tenant',
        deleteTenant: 'Delete Tenant',
        confirmDelete: 'Are you sure to delete this tenant?',
        deleteSuccess: 'Deleted successfully',
        createSuccess: 'Created successfully',
        updateSuccess: 'Updated successfully',
        statusUpdateSuccess: 'Status updated successfully',
        switchedTenant: 'Switched to tenant',
        form: {
          tenantName: 'Please enter tenant name',
          tenantCode: 'Please enter tenant code',
          tenantCodeRule: 'Only lowercase letters, numbers, underscores and hyphens',
          tenantCodePlaceholder: 'Lowercase letters, numbers only',
          description: 'Tenant description (optional)',
          contactName: 'Contact name',
          contactEmail: 'Contact email',
          contactPhone: 'Contact phone'
        },
        search: {
          name: 'Name',
          code: 'Code',
          namePlaceholder: 'Tenant name',
          codePlaceholder: 'Tenant code'
        }
      }
    }
  }
};
