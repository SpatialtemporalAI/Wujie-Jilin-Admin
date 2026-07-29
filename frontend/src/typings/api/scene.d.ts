declare namespace Api {
  namespace Scene {
    type CommonSearchParams = Pick<Common.PaginatingCommonParams, 'page' | 'page_size'>;

    /** scene group */
    type SceneGroup = Common.CommonRecord<{
      /** group name */
      name: string;
      /** parent group id */
      parent_id: number | null;
      /** parent group name (joined from parent group) */
      parent_name?: string | null;
      /** sort order */
      sort: number;
    }>;

    /** scene group search params */
    type SceneGroupSearchParams = CommonType.RecordNullable<Pick<SceneGroup, 'name' | 'status'> & CommonSearchParams>;

    /** scene group list */
    type SceneGroupList = Common.PaginatingQueryRecord<SceneGroup>;

    /** scene group create */
    type SceneGroupCreate = Pick<SceneGroup, 'name'> & {
      parent_id?: number | null;
      sort?: number;
      status?: Common.EnableStatus;
    };

    /** scene group update */
    type SceneGroupUpdate = Partial<SceneGroupCreate>;

    /** all scene group (for dropdown) */
    type AllSceneGroup = Pick<SceneGroup, 'id' | 'name'>;

    /** scene group tree node */
    type SceneGroupTreeNode = {
      id: number;
      name: string;
      parent_id: number | null;
      sort: number;
      status: Common.EnableStatus;
      children?: SceneGroupTreeNode[];
    };

    /** scene map */
    type SceneMap = Common.CommonRecord<{
      /** map name */
      name: string;
      /** group id */
      group_id: number | null;
      /** group name (joined) */
      group_name?: string;
      /** image file id */
      image_id: number | null;
      /** navigation image file id (image with obstacles drawn for navigation) */
      nav_image_id: number | null;
      /** map width */
      width: number | null;
      /** map height */
      height: number | null;
      /** mapping resolution */
      resolution: number;
      /** start point x */
      start_point_x: number;
      /** start point y */
      start_point_y: number;
      /** map content version, +1 per editor save */
      version: number;
      /** version synced in navigation service, backfilled by scheduler */
      target_version?: number | null;
    }>;

    /** scene map search params */
    type SceneMapSearchParams = CommonType.RecordNullable<
      Pick<SceneMap, 'name' | 'status'> & { group_id?: number } & CommonSearchParams
    >;

    /** scene map list */
    type SceneMapList = Common.PaginatingQueryRecord<SceneMap>;

    /** scene map create */
    type SceneMapCreate = {
      name: string;
      image_id: number;
      nav_image_id?: number | null;
      width: number;
      height: number;
      resolution: number;
      start_point_x: number;
      start_point_y: number;
      group_id?: number | null;
      group_name?: string | null;
      status?: Common.EnableStatus;
    };

    /** scene map update */
    type SceneMapUpdate = {
      name: string;
      image_id: number;
      nav_image_id?: number | null;
      width: number;
      height: number;
      resolution: number;
      start_point_x: number;
      start_point_y: number;
      group_id?: number | null;
      status?: Common.EnableStatus;
    };

    /** scene map annotation */
    type SceneMapAnnotation = Common.CommonRecord<{
      /** map id */
      map_id: number;
      /** x coordinate */
      x: number;
      /** y coordinate */
      y: number;
      /** annotation name */
      name: string;
      /** angle */
      angle: number;
      /** type (dict value) */
      type: string;
      /** number of active tasks referencing this annotation (only populated by editor data endpoint) */
      task_count?: number;
    }>;

    /** scene map annotation list */
    type SceneMapAnnotationList = Common.PaginatingQueryRecord<SceneMapAnnotation>;

    /** scene map annotation create */
    type SceneMapAnnotationCreate = {
      map_id: number;
      x: number;
      y: number;
      name: string;
      angle?: number;
      type: string;
    };

    /** scene map annotation update */
    type SceneMapAnnotationUpdate = Partial<Omit<SceneMapAnnotationCreate, 'map_id'>>;

    /** scene map object */
    type SceneMapObject = Common.CommonRecord<{
      /** map id */
      map_id: number;
      /** object type (dict value) */
      type: string;
      /** object name */
      name: string | null;
      /** x coordinate */
      x: number;
      /** y coordinate */
      y: number;
      /** width */
      width: number;
      /** height */
      height: number;
      /** polygon points (JSON) */
      points: string | null;
      /** rotation angle (degrees) */
      angle: number;
    }>;

    /** scene map object list */
    type SceneMapObjectList = Common.PaginatingQueryRecord<SceneMapObject>;

    /** scene map object create */
    type SceneMapObjectCreate = {
      map_id: number;
      type: string;
      name?: string | null;
      x: number;
      y: number;
      width?: number;
      height?: number;
      points?: string | null;
      angle?: number;
    };

    /** scene map object update */
    type SceneMapObjectUpdate = Partial<Omit<SceneMapObjectCreate, 'map_id'>>;

    /** scene map path */
    type SceneMapPath = Common.CommonRecord<{
      /** map id */
      map_id: number;
      /** start annotation id */
      start_annotation_id: number;
      /** end annotation id */
      end_annotation_id: number;
      /** path name */
      name: string | null;
      /** intermediate points (JSON) */
      points: string | null;
    }>;

    /** scene map path list */
    type SceneMapPathList = Common.PaginatingQueryRecord<SceneMapPath>;

    /** scene map path create */
    type SceneMapPathCreate = {
      map_id: number;
      start_annotation_id: number;
      end_annotation_id: number;
      name?: string | null;
      points?: string | null;
    };

    /** scene map path update */
    type SceneMapPathUpdate = Partial<Omit<SceneMapPathCreate, 'map_id'>>;

    /** editor annotation item */
    type EditorAnnotationItem = {
      id?: number | null;
      client_temp_id?: number | null;
      x: number;
      y: number;
      name: string;
      angle: number;
      type: string;
    };

    /** editor path item */
    type EditorPathItem = {
      id?: number | null;
      client_temp_id?: number | null;
      start_annotation_id: number;
      end_annotation_id: number;
      name?: string | null;
      points?: string | null;
    };

    /** editor object item */
    type EditorObjectItem = {
      id?: number | null;
      client_temp_id?: number | null;
      type: string;
      name?: string | null;
      x: number;
      y: number;
      width: number;
      height: number;
      points?: string | null;
      angle?: number;
    };

    /** editor save request */
    type EditorSaveRequest = {
      annotations: EditorAnnotationItem[];
      paths: EditorPathItem[];
      objects: EditorObjectItem[];
      deleted_annotation_ids: number[];
      deleted_path_ids: number[];
      deleted_object_ids: number[];
    };

    /** created id mapping (temp_id -> real id) */
    type CreatedIdMapping = {
      temp_id: number;
      id: number;
    };

    /** editor save response */
    type EditorSaveResponse = {
      created_annotations: CreatedIdMapping[];
      created_objects: CreatedIdMapping[];
      created_paths: CreatedIdMapping[];
    };

    /** editor map data */
    type EditorMapData = {
      map: SceneMap;
      annotations: SceneMapAnnotation[];
      paths: SceneMapPath[];
      objects: SceneMapObject[];
    };

    /** ROS 地图配置文件(yaml)解析结果 */
    type SceneMapConfigParseResult = {
      /** 分辨率(m/px) */
      resolution: number;
      /** 扫图起始点X坐标(origin[0]) */
      start_point_x: number;
      /** 扫图起始点Y坐标(origin[1]) */
      start_point_y: number;
    };
  }
}
