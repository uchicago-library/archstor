from os import makedirs
import logging
from abc import ABCMeta, abstractmethod
from pathlib import Path

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

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from flask import Blueprint, abort, Response, stream_with_context, request
from flask_restful import Resource, Api, reqparse


BLUEPRINT = Blueprint('archstor', __name__)


BLUEPRINT.config = {'BUFF': 1024*16}


API = Api(BLUEPRINT)


log = logging.getLogger(__name__)


def check_limit(x):
    if x > BLUEPRINT.config.get("MAX_LIMIT", 1000):
        return BLUEPRINT.config.get("MAX_LIMIT", 1000)
    return x


class IStorageBackend(metaclass=ABCMeta):
    @abstractmethod
    def get_object_id_list(self, offset, limit):
        pass

    @abstractmethod
    def check_object_exists(self, id):
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

    def get_object_id_list(self, offset, limit):
        return self.fs.find().sort('_id', ASCENDING).skip(offset).limit(limit)

    def check_object_exists(self, id):
        if self.fs.find_one({"_id": id}):
            return True
        return False

    def get_object(self, id):
        gr_entry = self.fs.find_one({"_id": id})
        return gr_entry

        if self.fs.find_one({"_id": id}):
            return True
        return False

    def set_object(self, id, content):
        if self.check_object_exists(id):
            raise RuntimeError("Does not support overwriting existing " +
                               "objects! Object exists {}".format(id))
        content_target = self.fs.new_file(_id=id)
        content.save(content_target)
        content_target.close()

    def del_object(self, id):
        raise NotImplemented("Yet")


class FileSystemStorageBackend(IStorageBackend):
    def __init__(self, lts_root):
        self.lts_root = Path(lts_root)

    def get_object_id_list(self):
        raise NotImplementedError()

    def get_object(self, id):
        content_path = Path(
            self.lts_root, identifier_to_path(id), "arf", "content.file"
        )
        return open(str(content_path))

    def check_object_exists(self, id):
        content_path = Path(
            self.lts_root, identifier_to_path(id), "arf", "content.file"
        )
        return content_path.is_file()

    def set_object(self, id, content):
        if self.check_object_exists(id):
            raise ValueError()
        content_path = Path(
            self.lts_root, identifier_to_path(id), "arf", "content.file"
        )
        makedirs(str(content_path.parent), exist_ok=True)
        content.save(str(content_path))


class S3ContentStorageBackend:
    # NOTE: THIS IS ENTIRELY UNTESTED
    # IT IS PRETTY MUCH A ROUGH DRAFT
    def s3_init(self, bucket_name, region_name=None, aws_access_key_id=None, aws_secret_access_key=None):
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
        return self.s3.list_objects(Bucket=self.bucket)[offset:offset+limit]

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
        if self.check_object_exists(id):
            raise ValueError()
        self.s3.Object(BLUEPRINT.config['storage'].name, id).put(Body=content)


class Root(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("offset", type=int, default=0)
        parser.add_argument("limit", type=int, default=1000)
        args = parser.parse_args()
        args['limit'] = check_limit(args['limit'])
        return {
            "objects": [
                {"identifier": x._id, "_link": API.url_for(Object, id=x._id)} for x
                in BLUEPRINT.config['storage'].get_object_id_list(args['offset'], args['limit'])
            ],
            "limit": args['limit'],
            "offset": args['offset']
        }


class Object(Resource):
    def get(self, id):

        def generate(e):
            data = e.read(BLUEPRINT.config['BUFF'])
            while data:
                yield data
                data = e.read(BLUEPRINT.config['BUFF'])

        if not BLUEPRINT.config['storage'].check_object_exists(id):
            abort(404)
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
        if id != secure_filename(id):
            log.critical(
                "Insecure identifier detected! ({})".format(id)
            )
            abort(500)

        BLUEPRINT.config['storage'].set_object(id, args['object'])
        return True

    def delete(self, id):
        if not BLUEPRINT.config['storage'].check_object_exists(id):
            abort(404)
        BLUEPRINT.config['storage'].del_object(id)
        return {"identifier": id, "deleted": True}


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

    def configure_s3(bp):
        # TODO
        raise NotImplemented("Yet")

    def configure_swift(bp):
        # TODO
        raise NotImplemented("Yet")

    storage_options = {
        "mongo": configure_mongo,
        "filesystem": configure_fs,
        "s3": configure_s3,
        "swift": configure_swift
    }

    app = setup_state.app
    BLUEPRINT.config.update(app.config)

    storage_choice = BLUEPRINT.config['STORAGE_BACKEND'].lower()

    if storage_choice is "noerror":
        pass
    else:
        storage_options[storage_choice](BLUEPRINT)

    if BLUEPRINT.config.get("VERBOSITY"):
        logging.basicConfig(level=BLUEPRINT.config['VERBOSITY'])
    else:
        logging.basicConfig(level="WARN")

API.add_resource(Root, "/")
API.add_resource(Object, "/<string:id>")
