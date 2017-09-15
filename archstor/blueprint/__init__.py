"""
archstor
"""
import logging
from os import makedirs, remove
from abc import ABCMeta, abstractmethod
from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from flask import Blueprint, jsonify, Response, stream_with_context
from flask_restful import Resource, Api, reqparse

try:
    import boto3
    import botocore
except:
    # Hope we're not using the s3 backend
    pass

try:
    from pymongo import MongoClient, ASCENDING
    from gridfs import GridFS
except:
    # Hope we're not using a mongo backend
    pass

try:
    from pypairtree.utils import identifier_to_path
except:
    # Hope we're not using a file system backend
    pass

try:
    import swiftclient
    import swiftclient.service
    from swiftclient.exceptions import ClientException
except:
    # Hope we're not using a swift backend
    pass

from .exceptions import Error, ServerError, NotFoundError, ObjectNotFoundError, \
    ObjectAlreadyExistsError, FunctionalityOmittedError, UserError


__author__ = "Brian Balsamo"
__email__ = "brian@brianbalsamo.com"
__version__ = "0.0.1"


BLUEPRINT = Blueprint('archstor', __name__)

BLUEPRINT.config = {
    'BUFF': 1024 * 1000
}

API = Api(BLUEPRINT)

log = logging.getLogger(__name__)


@BLUEPRINT.errorhandler(Error)
def handle_errors(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def check_limit(x):
    if x > BLUEPRINT.config.get("MAX_LIMIT", 1000):
        return BLUEPRINT.config.get("MAX_LIMIT", 1000)
    return x


def check_id(id):
    if id != secure_filename(id):
        log.critical(
            "Insecure identifier detected! ({})".format(str(id))
        )
        raise UserError("Insecure identifier!")


class IStorageBackend(metaclass=ABCMeta):
    @abstractmethod
    def get_object_id_list(self, cursor, limit):
        # In: offset and limit ints
        # Out: List of strs
        pass

    @abstractmethod
    def check_object_exists(self, id):
        # In: id str
        # Out: bool
        pass

    @abstractmethod
    def get_object(self, id):
        # In: str
        # Out: File like object
        pass

    @abstractmethod
    def set_object(self, id, content):
        # In: str + flask.FileStorage
        # Out: None
        pass

    @abstractmethod
    def del_object(self, id):
        # In: str identifier
        # Out: bool
        pass


class MongoStorageBackend(IStorageBackend):
    def __init__(self, db_host, db_port=None, db_name=None):
        if db_port is None:
            db_port = 27017
        if db_name is None:
            db_name = "lts"

        self.db = MongoClient(db_host, db_port)[db_name]

        self.fs = GridFS(
            MongoClient(db_host, db_port)[db_name]
        )

    def get_object_id_list(self, cursor, limit):
        def peek(cursor, limit):
            if len([x._id for x in self.fs.find().sort('_id', ASCENDING).skip(cursor + limit)]) > 0:
                return str(cursor + limit)
            return None
        cursor = int(cursor)
        results = [x._id for x in self.fs.find().sort('_id', ASCENDING).skip(cursor).limit(limit)]
        next_cursor = peek(cursor, limit)
        return next_cursor, results

    def check_object_exists(self, id):
        if self.fs.find_one({"_id": id}):
            return True
        return False

    def get_object(self, id):
        gr_entry = self.fs.find_one({"_id": id})
        if gr_entry is None:
            raise ObjectNotFoundError(str(id))
        return gr_entry

    def set_object(self, id, content):
        if self.check_object_exists(id):
            raise ObjectAlreadyExistsError(str(id))
        content_target = self.fs.new_file(_id=id)
        content.save(content_target)
        content_target.close()

    def del_object(self, id):
        return self.fs.delete(id)


class FileSystemStorageBackend(IStorageBackend):
    def __init__(self, lts_root):
        self.lts_root = Path(lts_root)

    def get_object_id_list(self, cursor, limit):
        raise FunctionalityOmittedError(
            "This functionality is not available while using this storage backend"
        )

    def get_object(self, id):
        content_path = Path(
            self.lts_root, identifier_to_path(id), "arf", "content.file"
        )
        if not content_path.is_file():
            raise ObjectNotFoundError(str(id))
        return open(str(content_path))

    def check_object_exists(self, id):
        content_path = Path(
            self.lts_root, identifier_to_path(id), "arf", "content.file"
        )
        return content_path.is_file()

    def set_object(self, id, content):
        content_path = Path(
            self.lts_root, identifier_to_path(id), "arf", "content.file"
        )
        if self.check_object_exists(id):
            raise ObjectAlreadyExistsError(str(id))
        makedirs(str(content_path.parent), exist_ok=True)
        content.save(str(content_path))

    def del_object(self, id):
        content_path = Path(
            self.lts_root, identifier_to_path(id), "arf", "content.file"
        )
        if not content_path.exists():
            return True
        remove(str(content_path))
        return True


class S3StorageBackend(IStorageBackend):
    # NOTE: THIS IS ENTIRELY UNTESTED
    # IT IS PRETTY MUCH A ROUGH DRAFT
    def __init__(self, bucket_name, region_name=None, aws_access_key_id=None, aws_secret_access_key=None):
        # Helper init for inheriting classes.
        self.s3 = boto3.client(
            's3', region_name=region_name, aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        self.bucket = bucket_name
        exists = True
        try:
            self.s3.head_bucket(Bucket=bucket_name)
        except botocore.exceptions.ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                exists = False
        if not exists:
            # Init the bucket
            self.s3.create_bucket(Bucket=bucket_name)

    def get_object_id_list(self, offset, limit):
        # TODO: Actually use api implementations of item queries
        return self.s3.list_objects(Bucket=self.bucket)[offset:offset + limit]

    def get_object(self, id):
        obj = self.s3.get_object(Bucket=BLUEPRINT.config['storage'].name, Key=id)
        return obj['Body']

    def check_object_exists(self, id):
        try:
            self.s3.head_object(Bucket=self.bucket)
            return True
        except botocore.exceptions.ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                return False

    def set_object(self, id, content):
        self.s3.Object(BLUEPRINT.config['storage'].name, id).put(Body=content)


class SwiftStorageBackend(IStorageBackend):
    def __init__(self,
                 auth_url,
                 auth_version,
                 user,
                 key,
                 tenant_name,
                 os_options={},
                 container_name="lts"):
        self.auth_url = auth_url
        self.auth_version = auth_version
        self.user = user
        self.key = key
        self.tenant_name = tenant_name
        self.os_options = os_options
        self.container_name = container_name
        self._opts = {'auth': self.auth_url, 'user': self.user, 'key': self.key,
                      'use_slo': True, 'segment_size': BLUEPRINT.config['BUFF'], 'auth_version': self.auth_version}
        self._opts = dict(
            swiftclient.service._default_global_options,
            **dict(swiftclient.service._default_local_options, **self._opts)
        )
        swiftclient.service.process_options(self._opts)
        # Check to be sure our LTS container exists
        conn = self.create_connection()
        try:
            conn.head_container(self.container_name)
        except ClientException as e:
            if e.http_status == 404:
                conn.put_container(self.container_name)
        conn.close()

    def create_connection(self):
        return swiftclient.service.get_conn(self._opts)

    def get_object_id_list(self, cursor, limit):
        if cursor is "0":
            cursor = None
        conn = self.create_connection()
        results = []
        listing = True
        while listing:
            headers, listing = conn.get_container(self.container_name, marker=cursor, limit=limit)
            for x in listing:
                results.append(x['name'])
            if not listing:
                cursor = None
                break
            cursor = listing[-1].get('name', listing[-1].get('subdir'))
            if limit is not None and len(listing) >= limit:
                break
        conn.close()

        return cursor, results

    def get_object(self, id):
        try:
            conn = self.create_connection()
            headers, contents = conn.get_object(self.container_name, id, resp_chunk_size=BLUEPRINT.config['BUFF'])
            conn.close()
            return contents
        except ClientException as e:
            if e.http_status == 404:
                conn.close()
                raise ObjectNotFoundError()
            conn.close()

    def check_object_exists(self, id):
        conn = self.create_connection()
        try:
            conn.head_object(self.container_name, id)
            conn.close()
            return True
        except ClientException as e:
            if e.http_status == 404:
                conn.close()
                return False
            conn.close()
            raise

    def set_object(self, id, content):
        if self.check_object_exists(id):
            raise ObjectAlreadyExistsError()
        conn = self.create_connection()
        conn.put_object(self.container_name, id, contents=content, chunk_size=BLUEPRINT.config['BUFF'])
        conn.close()

    def del_object(self, id):
        try:
            conn = self.create_connection()
            conn.delete_object(self.container_name, id)
            conn.close()
        except ClientException as e:
            if e.http_status == 404:
                conn.close()
                return
            conn.close()
            raise


class Root(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("cursor", type=str, default="0")
        parser.add_argument("limit", type=int, default=1000)
        args = parser.parse_args()
        args['limit'] = check_limit(args['limit'])
        next_cursor, result = BLUEPRINT.config['storage'].get_object_id_list(
            args['cursor'],
            args['limit']
        )
        return {
            "objects": [
                {"identifier": x, "_link": API.url_for(Object, id=x)} for x
                in result
            ],
            "pagination": {
                "limit": args['limit'],
                "cursor": args['cursor'],
                "next_cursor": next_cursor
            },
            "_self": {
                "identifier": None,
                "_link": API.url_for(Root)
            }
        }


class Object(Resource):
    def get(self, id):

        def generate(e):
            data = e.read(BLUEPRINT.config['BUFF'])
            while data:
                yield data
                data = e.read(BLUEPRINT.config['BUFF'])

        check_id(id)
        return Response(
            stream_with_context(
                generate(BLUEPRINT.config['storage'].get_object(id))
            )
        )

    def put(self, id):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "object",
            required=True,
            type=FileStorage,
            location='files'
        )
        args = parser.parse_args()
        check_id(id)

        BLUEPRINT.config['storage'].set_object(id, args['object'])
        return {'identifier': id, "added": True}

    def delete(self, id):
        BLUEPRINT.config['storage'].del_object(id)
        return {"identifier": id, "deleted": True}


class Version(Resource):
    def get(self):
        return {"version": __version__}


@BLUEPRINT.record
def handle_configs(setup_state):
    def configure_mongo(bp):
        mongo_host = bp.config['MONGO_HOST']
        mongo_port = bp.config.get('MONGO_PORT')
        mongo_db = bp.config.get("MONGO_DB")
        bp.config['storage'] = MongoStorageBackend(mongo_host, mongo_port, mongo_db)

    def configure_fs(bp):
        root = bp.config['LTS_ROOT']
        bp.config['storage'] = FileSystemStorageBackend(root)

    def configure_swift(bp):
        bp.config['storage'] = SwiftStorageBackend(
            bp.config['SWIFT_AUTH_URL'],
            bp.config['SWIFT_AUTH_VERSION'],
            bp.config['SWIFT_USER'],
            bp.config['SWIFT_KEY'],
            bp.config['SWIFT_TENANT_NAME'],
            os_options=bp.config.get('SWIFT_OS_OPTIONS', {}),
            container_name=bp.config.get('SWIFT_CONTAINER_NAME', 'lts')
        )

    def configure_s3(bp):
        # TODO
        raise NotImplemented("Yet")

    app = setup_state.app
    BLUEPRINT.config.update(app.config)
    if BLUEPRINT.config.get('DEFER_CONFIG'):
        log.debug("DEFER_CONFIG set, skipping configuration")
        return

    storage_options = {
        "mongo": configure_mongo,
        "filesystem": configure_fs,
        "s3": configure_s3,
        "swift": configure_swift
    }

    if BLUEPRINT.config.get('STORAGE_BACKEND'):
        storage_choice = BLUEPRINT.config['STORAGE_BACKEND'].lower()

        if storage_choice is "noerror":
            # Assume the user knows what they're doing, and will set
            # the config['storage'] option somewhere else
            pass
        else:
            storage_options[storage_choice](BLUEPRINT)

    if BLUEPRINT.config.get("VERBOSITY"):
        log.debug("Setting verbosity to {}".format(str(BLUEPRINT.config['VERBOSITY'])))
        logging.basicConfig(level=BLUEPRINT.config['VERBOSITY'])
    else:
        log.debug("No verbosity option set, defaulting to WARN")
        logging.basicConfig(level="WARN")


API.add_resource(Root, "/")
API.add_resource(Object, "/<string:id>")
API.add_resource(Version, "/version")
