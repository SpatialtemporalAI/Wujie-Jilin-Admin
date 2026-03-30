declare namespace Api {
  /**
   * namespace SystemManage
   *
   * backend api module: "systemManage"
   */
  namespace SystemManage {
    type CommonSearchParams = Pick<Common.PaginatingCommonParams, 'page' | 'page_size'>;

    /** role */
    type Role = Common.CommonRecord<{
      /** role name */
      name: string;
      /** role code */
      code: string;
      /** role description */
      desc: string;
    }>;

    /** role search params */
    type RoleSearchParams = CommonType.RecordNullable<
      Pick<Api.SystemManage.Role, 'name' | 'code' | 'status'> & CommonSearchParams
    >;

    /** role list */
    type RoleList = Common.PaginatingQueryRecord<Role>;

    /** all role */
    type AllRole = Pick<Role, 'id' | 'name' | 'code'>;

    /**
     * user gender
     *
     * - "1": "male"
     * - "2": "female"
     */
    type UserGender = '1' | '2';

    /** user */
    type User = Common.CommonRecord<{
      /** user name */
      username: string;
      /** user nick name */
      nickname: string;
      /** user phone */
      phone: string;
      /** user email */
      email: string;
      /** is super user */
      is_superuser: boolean;
      /** user role code collection */
      userRoles: string[];
      /** last login time */
      last_login_at?: string;
      /** last login ip */
      last_login_ip?: string;
    }>;

    /** user search params */
    type UserSearchParams = CommonType.RecordNullable<
      Pick<Api.SystemManage.User, 'username' | 'nickname' | 'phone' | 'email' | 'is_superuser' | 'status'> &
        CommonSearchParams
    >;

    /** user list */
    type UserList = Common.PaginatingQueryRecord<User>;

    /** change password request */
    type ChangePasswordRequest = {
      /** new password */
      new_password: string;
    };

    /** user create */
    type UserCreate = Pick<User, 'username' | 'nickname' | 'phone' | 'email' | 'status'> & {
      /** user password */
      password: string;
      /** user role code collection */
      userRoles: string[];
    };

    /** user update */
    type UserUpdate = Pick<User, 'username' | 'nickname' | 'phone' | 'email' | 'status'> & {
      /** user role code collection */
      userRoles: string[];
    };

    /**
     * menu type
     *
     * - "1": directory
     * - "2": menu
     */
    type MenuType = '1' | '2';

    type MenuButton = {
      /**
       * button code
       *
       * it can be used to control the button permission
       */
      code: string;
      /** button description */
      desc: string;
    };

    /**
     * icon type
     *
     * - "1": iconify icon
     * - "2": local icon
     */
    type IconType = '1' | '2';

    type MenuPropsOfRoute = Pick<
      import('vue-router').RouteMeta,
      | 'i18nKey'
      | 'keepAlive'
      | 'constant'
      | 'order'
      | 'href'
      | 'hideInMenu'
      | 'activeMenu'
      | 'multiTab'
      | 'fixedIndexInTab'
      | 'query'
    >;

    type Menu = Common.CommonRecord<{
      /** parent menu id */
      parentId: number;
      /** menu type */
      menuType: MenuType;
      /** menu name */
      menuName: string;
      /** route name */
      routeName: string;
      /** route path */
      routePath: string;
      /** component */
      component?: string;
      /** iconify icon name or local icon name */
      icon: string;
      /** icon type */
      iconType: IconType;
      /** buttons */
      buttons?: MenuButton[] | null;
      /** children menu */
      children?: Menu[] | null;
    }> &
      MenuPropsOfRoute;

    /** menu list */
    type MenuList = Common.PaginatingQueryRecord<Menu>;

    type MenuTree = {
      id: number;
      label: string;
      pId: number;
      children?: MenuTree[];
    };

    /** 字典 */
    type Dict = Common.CommonRecord<{
      /** 字典名称 */
      name: string;
      /** 字典编码 */
      code: string;
      /** 字典描述 */
      description?: string;
      /** 是否启用 */
      status: Common.EnableStatus;
      /** 是否为系统内置字典 */
      is_system: Common.EnableStatus;
      /** 排序号 */
      sort: number;
    }>;

    /** 字典项 */
    type DictItem = Common.CommonRecord<{
      /** 关联字典ID */
      dict_id: number;
      /** 字典项值 */
      value: string;
      /** 字典项文本 */
      label: string;
      /** 字典项描述 */
      description?: string;
      /** 扩展信息(JSON格式) */
      ext_info?: string;
      /** 排序号 */
      sort: number;
    }>;

    /** 字典搜索参数 */
    type DictSearchParams = CommonType.RecordNullable<
      Pick<Dict, 'name' | 'code' | 'is_system' | 'status'> & CommonSearchParams
    >;

    /** 字典列表 */
    type DictList = Common.PaginatingQueryRecord<Dict>;

    /** 字典项搜索参数 */
    type DictItemSearchParams = CommonType.RecordNullable<
      Pick<DictItem, 'dict_id' | 'label' | 'value' | 'status'> & CommonSearchParams
    >;

    /** 字典项列表 */
    type DictItemList = Common.PaginatingQueryRecord<DictItem>;

    /** 带字典项的字典 */
    type DictWithItems = Dict & {
      items: DictItem[];
    };

    /** 字典创建 */
    type DictCreate = {
      /** 字典名称 */
      name: string;
      /** 字典编码 */
      code: string;
      /** 字典描述 */
      description?: string;
      /** 是否启用 */
      status: Common.EnableStatus;
      /** 是否为系统内置字典 */
      is_system: Common.EnableStatus;
      /** 排序号 */
      sort: number;
    };

    /** 字典更新 */
    type DictUpdate = Partial<DictCreate>;

    /** 字典项创建 */
    type DictItemCreate = {
      /** 关联字典ID */
      dict_id: number;
      /** 字典项值 */
      value: string;
      /** 字典项文本 */
      label: string;
      /** 字典项描述 */
      description?: string;
      /** 扩展信息(JSON格式) */
      ext_info?: string;
      /** 是否启用 */
      status: Common.EnableStatus;
      /** 排序号 */
      sort: number;
    };

    /** 字典项更新 */
    type DictItemUpdate = Partial<DictItemCreate>;

    /** 批量更新字典状态 */
    type DictBatchUpdateStatus = {
      ids: number[];
      status: boolean;
    };

    /** 批量更新字典项状态 */
    type DictItemBatchUpdateStatus = {
      ids: number[];
      status: boolean;
    };

    /** 配置类型 */
    type ConfigType = 'string' | 'number' | 'boolean' | 'json' | 'array';

    /** 配置分组 */
    type ConfigGroup = 'system' | 'security' | 'log' | 'network' | 'storage' | 'custom';

    /** 系统配置 */
    type Config = Common.CommonRecord<{
      /** 配置键名 */
      key: string;
      /** 配置值 */
      value: string;
      /** 默认值 */
      default_value?: string;
      /** 校验规则 */
      validation_rule?: string;
      /** 配置描述 */
      description?: string;
      /** 配置类型 */
      type: ConfigType;
      /** 配置分组 */
      group: ConfigGroup;

      /** 是否为系统内置配置 */
      is_system: Common.EnableStatus;
    }>;

    /** 配置搜索参数 */
    type ConfigSearchParams = CommonType.RecordNullable<
      Pick<Config, 'key' | 'description' | 'type' | 'group' | 'is_system'> & CommonSearchParams
    >;

    /** 配置列表 */
    type ConfigList = Common.PaginatingQueryRecord<Config>;

    /** 配置创建 */
    type ConfigCreate = Pick<
      Config,
      'key' | 'value' | 'default_value' | 'validation_rule' | 'description' | 'type' | 'group' | 'is_system'
    >;

    /** 配置更新 */
    type ConfigUpdate = Partial<ConfigCreate>;

    /** 批量更新配置 */
    type ConfigBatchUpdate = {
      configs: Array<{ id: number; value: string }>;
    };

    /** 重置配置 */
    type ConfigReset = {
      ids: string[];
    };
  }
}
