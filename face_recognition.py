import os
import coloredlogs
from dotenv import load_dotenv
from alibabacloud_facebody20191230.models import (
    AddFaceEntityRequest,
    CreateFaceDbRequest,
    AddFaceRequest,
    DeleteFaceEntityRequest,
    DeleteFaceRequest,
    DetectFaceRequest,
    ListFaceDbsRequest,
    SearchFaceRequest,
)
from alibabacloud_tea_openapi.models import Config
from alibabacloud_facebody20191230.client import Client
from alibabacloud_tea_util.models import RuntimeOptions
from pydantic import PostgresDsn
from viapi.fileutils import FileUtils
import logging

logger = logging.getLogger()
coloredlogs.install(level='INFO', logger=logger)

# Aliyun ACCESS_KEY AND ACCESS_KEY_SECRET
load_dotenv("aliyun.env")

# Aliyun Face Recognition
config = Config(
    access_key_id=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
    access_key_secret=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
    endpoint="facebody.cn-shanghai.aliyuncs.com",
    region_id="cn-shanghai"
)
runtime_options = RuntimeOptions()
file_utils = FileUtils(os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"), os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"))

def aliyun_oss_url(file_path: str, is_local: bool = False, file_type: str = "jpg") -> str:
    return file_utils.get_oss_url(file_path, file_type, is_local)
    
def create_face_db(db_name: str) -> bool:
    """
    Create a new face database in Aliyun Face Recognition service.
    
    Args:
        db_name: Name of the database to create
        
    Returns:
        bool: True if database creation succeeded, False otherwise
    """
    try:
        client = Client(config)
        request = CreateFaceDbRequest(
            name=db_name
        )
        response = client.create_face_db_with_options(request, runtime_options)
        logger.info(response.body)
        return True
    except Exception as error:
        logger.error(error)
        logger.error(error.code)
        return False
    
def list_face_dbs() -> list:
    """
    List all face databases created in Aliyun Face Recognition service.
    
    Returns:
        list: List of database names
    """
    try:
        client = Client(config)
        request = ListFaceDbsRequest()
        response = client.list_face_dbs_with_options(request, runtime_options)
        logger.info(response.body)
        results = []
        for db in response.body.data.db_list:
            results.append(db.name)
        return results
    except Exception as error:
        logger.error(error)
        return []

def add_face_entity(db_name: str, entity_id: str) -> bool:
    """
    Add a new face entity (person) to the specified face database.
    An entity represents a unique person and can have multiple face images associated with it.
    
    Args:
        db_name: Name of the database to add the entity to
        entity_id: Unique identifier for the entity (person name or ID)
        
    Returns:
        bool: True if entity was added successfully, False otherwise
    """
    try:
        client = Client(config)
        request = AddFaceEntityRequest(
            db_name=db_name,
            entity_id=entity_id
        )
        response = client.add_face_entity_with_options(request, runtime_options)
        logger.info(response.body)
        return True
    except Exception as error:
        logger.error(error)
        logger.error(error.code)
        return False
    
def delete_face_entity(db_name: str, entity_id: str) -> bool:
    """
    Delete a face entity and all associated face images from the database.

    Args:
        db_name: Name of the database containing the entity
        entity_id: ID of the entity to delete

    Returns:
        bool: True if deletion succeeded, False otherwise
    """
    try:
        client = Client(config)
        request = DeleteFaceEntityRequest(
            db_name=db_name,
            entity_id=entity_id,
        )
        response = client.delete_face_entity_with_options(request, runtime_options)
        logger.info(response.body)
        return True
    except Exception as error:
        logger.error(error)
        if hasattr(error, "code"):
            logger.error(error.code)
        return False


def delete_face(db_name: str, face_id: str) -> bool:
    """
    Delete a single face image from the face database.

    Args:
        db_name: Name of the database containing the face image
        face_id: Aliyun face image ID returned by add_face_image

    Returns:
        bool: True if deletion succeeded, False otherwise
    """
    try:
        client = Client(config)
        request = DeleteFaceRequest(
            db_name=db_name,
            face_id=face_id,
        )
        response = client.delete_face_with_options(request, runtime_options)
        logger.info(response.body)
        return True
    except Exception as error:
        logger.error(error)
        if hasattr(error, "code"):
            logger.error(error.code)
        return False


def add_face_image(db_name: str, entity_id: str, url: str, is_local: bool = False, file_type: str = None) -> str | None:
    """
    Add a face image to an existing entity in the face database.
    Multiple face images can be added to the same entity for better recognition accuracy.
    
    Args:
        db_name: Name of the database containing the entity
        entity_id: ID of the entity to add the face image to
        url: Path to the image file (local path or OSS URL)
        is_local: If True, treats url as a local file path. If False, treats as OSS URL
        file_type: Image file type (e.g., 'jpg', 'png'). Auto-detected from file extension if None
        
    Returns:
        str | None: Aliyun face_id on success, None on failure
    """
    if is_local and not os.path.exists(url):
        logger.error(f"File not found: {url}")
        return None
    if file_type is None:
        _, ext = os.path.splitext(url)
        file_type = ext.lstrip('.') or 'png'
    try:
        client = Client(config)
        oss_url = aliyun_oss_url(url, is_local, file_type)
        request = AddFaceRequest(
            db_name=db_name,
            entity_id=entity_id,
            image_url=oss_url
        )
        response = client.add_face_with_options(request, runtime_options)
        logger.info(response.body)
        if response.body and response.body.data:
            return response.body.data.face_id
        return None
    except Exception as error:
        logger.error(error)
        if hasattr(error, "code"):
            logger.error(error.code)
        return None
    
def search_face(db_name: str, url: str, limit: int = 3, is_local: bool = False, file_type: str = None) -> list:
    """
    Search for matching faces in the database and return ranked results.
    Compares the input face image against all entities in the database and returns top matches.
    
    Args:
        db_name: Name of the database to search in
        url: Path to the face image to search for (local path or OSS URL)
        limit: Maximum number of top matches to return (default: 3)
        is_local: If True, treats url as a local file path. If False, treats as OSS URL
        file_type: Image file type (e.g., 'jpg', 'png'). Auto-detected from file extension if None
        
    Returns:
        list: List of dictionaries containing matching entities, each with:
              - entity_id (str): ID of the matched entity
              - confidence (float): Confidence score of the match
              Returns empty list if no matches found or on error
    """
    if is_local and not os.path.exists(url):
        logger.error(f"File not found: {url}")
        return []
    if file_type is None:
        _, ext = os.path.splitext(url)
        file_type = ext.lstrip('.') or 'png'
    try:
        client = Client(config)
        oss_url = aliyun_oss_url(url, is_local, file_type)
        request = SearchFaceRequest(
            db_name=db_name,
            image_url=oss_url, 
            limit=limit
        )
        response = client.search_face_with_options(request, runtime_options)
        logger.info(response.body)
        if response.body.data.match_list:
            results = []
            for face_item in response.body.data.match_list[0].face_items[:limit]:
                results.append({
                    "entity_id": face_item.entity_id,
                    "confidence": face_item.confidence
                })
            return results        
        else:
            return []
    except Exception as error:
        logger.error(error)
        logger.error(error.code)
        return []

def detect_face(url: str, max_face_num: int = 10, is_local: bool = False, file_type: str = None) -> list:
    """
    Detect faces in an image and return the bounding boxes of the faces.
    
    Args:
        url: Path to the image to detect faces in (local path or OSS URL)
        max_face_num: Maximum number of faces to detect (default: 10)
        is_local: If True, treats url as a local file path. If False, treats as OSS URL
        file_type: Image file type (e.g., 'jpg', 'png'). Auto-detected from file extension if None
    """
    if is_local and not os.path.exists(url):
        logger.error(f"File not found: {url}")
        return []
    if file_type is None:
        _, ext = os.path.splitext(url)
        file_type = ext.lstrip('.') or 'png'
    try:
        client = Client(config)
        oss_url = aliyun_oss_url(url, is_local, file_type)
        request = DetectFaceRequest(
            image_url=oss_url,
            landmark=False,
            quality=False,
            pose=False,
            max_face_number=max_face_num
        )
        response = client.detect_face_with_options(request, runtime_options)
        logger.info(response.body)
        results = []
        for i in range(response.body.data.face_count):
            results.append({
                "face_rect": response.body.data.face_rectangles[i],
                "face_probability": response.body.data.face_probability_list[i]
            })
        return results
    except Exception as error:
        logger.error(error)
        logger.error(error.code)
        return []

if __name__ == "__main__":
    # create_face_db("db_test")
    import argparse
    from entity_mapper import get_entity_mapper
    
    parser = argparse.ArgumentParser(description="Face Recognition CLI Tool")
    parser.add_argument("--db_name", type=str, default="db_test", help="Database name (default: db_test)")
    parser.add_argument("--use-mapper", action="store_true", help="Use entity name-to-ID mapping")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # add_entity subcommand
    add_entity_parser = subparsers.add_parser("add_entity", help="Add a new face entity")
    add_entity_parser.add_argument("name", type=str, help="Entity name/ID")
    
    # add_face subcommand
    add_face_parser = subparsers.add_parser("add_face", help="Add a face image to an entity")
    add_face_parser.add_argument("entity_name", type=str, help="Entity name/ID")
    add_face_parser.add_argument("path", type=str, help="Path to the face image")
    
    # search_face subcommand
    search_face_parser = subparsers.add_parser("search_face", help="Search for a face in the database")
    search_face_parser.add_argument("path", type=str, help="Path to the face image to search")
    search_face_parser.add_argument("--limit", type=int, default=3, help="Maximum number of results (default: 3)")
    
    args = parser.parse_args()
    
    # Initialize entity mapper if needed
    entity_mapper = None
    if args.use_mapper:
        entity_mapper = get_entity_mapper()
    
    if args.command == "add_entity":
        entity_id = args.name
        if entity_mapper:
            entity_id = entity_mapper.get_or_create_id(args.name)
            logger.info(f"Mapped entity name '{args.name}' to ID '{entity_id}'")
        
        success = add_face_entity(args.db_name, entity_id)
        if success:
            logger.info(f"Successfully added entity: {args.name}")
        else:
            logger.error(f"Failed to add entity: {args.name}")
    
    elif args.command == "add_face":
        entity_id = args.entity_name
        if entity_mapper:
            entity_id = entity_mapper.get_or_create_id(args.entity_name)
            logger.info(f"Mapped entity name '{args.entity_name}' to ID '{entity_id}'")
        
        success = add_face_image(args.db_name, entity_id, args.path, is_local=True)
        if success:
            logger.info(f"Successfully added face image for entity: {args.entity_name}")
        else:
            logger.error(f"Failed to add face image for entity: {args.entity_name}")
    
    elif args.command == "search_face":
        results = search_face(args.db_name, args.path, limit=args.limit, is_local=True)
        if results:
            # Convert entity IDs back to names if using mapper
            if entity_mapper:
                for result in results:
                    entity_name = entity_mapper.get_name(result['entity_id'])
                    if entity_name:
                        result['entity_name'] = entity_name
                        logger.info(f"Converted entity ID '{result['entity_id']}' to name '{entity_name}'")
            
            logger.info(f"Found matching entities: {results}")
            print(f"Match found: {results}")
        else:
            logger.info("No matching entities found")
            print("No match found")  
    
    else:
        parser.print_help()
