import unittest
import json
from os import environ
from uuid import uuid4
from io import BytesIO
from tempfile import TemporaryDirectory

from pymongo import MongoClient

# Defer any configuration to the tests setUp()
environ['ARCHSTOR_DEFER_CONFIG'] = "True"

import archstor


class PackageTests(unittest.TestCase):
    def testVersionAvailable(self):
        x = getattr(archstor, "__version__", None)
        self.assertTrue(x is not None)


class ArchstorTestCase:
    def testVersion(self):
        version_response = self.app.get("/version")
        self.assertEqual(version_response.status_code, 200)
        version_json = json.loads(version_response.data.decode())
        api_reported_version = version_json['version']
        self.assertEqual(
            archstor.blueprint.__version__,
            api_reported_version
        )

    def response_200_json(self, rv):
        self.assertEqual(rv.status_code, 200)
        rt = rv.data.decode()
        rj = json.loads(rt)
        return rj

    def test_getRoot(self):
        rv = self.app.get("/")
        self.response_200_json(rv)

    def test_rootPagination(self):
        ids = []
        for x in range(1234):
            id = uuid4().hex
            obj = BytesIO(bytes("this is a test object ({})".format(str(x)), encoding="utf-8"))
            rv = self.app.put("/{}".format(id), data={"object": (obj, "test.txt")})
            rj = self.response_200_json(rv)
            self.assertEqual(rj['added'], True)
            ids.append(id)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 1234)
        comp_ids = []
        next_cursor = "0"
        while next_cursor:
            rv = self.app.get("/", data={"cursor": next_cursor, "limit": 200})
            rj = self.response_200_json(rv)
            next_cursor = rj['pagination']['next_cursor']
            for x in rj['objects']:
                comp_ids.append(x['identifier'])
        self.assertEqual(len(comp_ids), 1234)
        for x in comp_ids:
            self.assertIn(x, ids)

    def test_putObject(self):
        id = uuid4().hex
        obj = BytesIO(b"this is a test object")
        rv = self.app.put("/{}".format(id), data={"object": (obj, "test.txt")})
        rj = self.response_200_json(rv)
        self.assertEqual(rj['added'], True)

    def test_getObject(self):
        # Put the object into the db
        id = uuid4().hex
        obj = BytesIO(b"this is a test object")
        prv = self.app.put("/{}".format(id), data={"object": (obj, "test.txt")})
        prj = self.response_200_json(prv)
        self.assertEqual(prj['added'], True)
        # Retrieve it
        grv = self.app.get("/{}".format(id))
        self.assertEqual(grv.data, b"this is a test object")

    def test_getNonexistantObject(self):
        rv = self.app.get("/{}".format(uuid4().hex))
        self.assertEqual(rv.status_code, 404)

    def test_deleteObject(self):
        # Put the object into the db
        id = uuid4().hex
        obj = BytesIO(b"this is a test object")
        prv = self.app.put("/{}".format(id), data={"object": (obj, "test.txt")})
        prj = self.response_200_json(prv)
        self.assertEqual(prj['added'], True)
        # Delete the object
        drv = self.app.delete("/{}".format(id))
        drj = self.response_200_json(drv)
        self.assertEqual(drj['deleted'], True)
        # Retrieve it (well, fail at retrieving it)
        grv = self.app.get("/{}".format(id))
        self.assertEqual(grv.status_code, 404)

    def test_deleteNonexistantObject(self):
        id = uuid4().hex
        # Delete the object
        drv = self.app.delete("/{}".format(id))
        drj = self.response_200_json(drv)
        self.assertEqual(drj['deleted'], True)
        # Retrieve it (well, fail at retrieving it)
        grv = self.app.get("/{}".format(id))
        self.assertEqual(grv.status_code, 404)

    def test_unsafeFileIdentifier(self):
        id = uuid4().hex
        obj = BytesIO(b"this is a test object")
        rv = self.app.put("/&#47;&#46;&#46;&#47;{}".format(id), data={"object": (obj, "test.txt")})
        self.assertEqual(rv.status_code, 400)

    def test_objectOverwrite(self):
        id = uuid4().hex
        obj1 = BytesIO(b"this is a test object")
        rv1 = self.app.put("/{}".format(id), data={"object": (obj1, "test.txt")})
        rj1 = self.response_200_json(rv1)
        self.assertEqual(rj1['added'], True)
        obj2 = BytesIO(b"this is another object")
        rv2 = self.app.put("/{}".format(id), data={"object": (obj2, "test.txt")})
        self.assertEqual(rv2.status_code, 400)

    def test_Version(self):
        rv = self.app.get("/version")
        rj = self.response_200_json(rv)
        self.assertEqual(rj['version'], archstor.blueprint.__version__)


class MongoStorageTestCases(ArchstorTestCase, unittest.TestCase):
    def setUp(self):
        archstor.app.config['TESTING'] = True
        self.app = archstor.app.test_client()
        archstor.blueprint.BLUEPRINT.config['storage'] = \
            archstor.blueprint.MongoStorageBackend(
                'localhost', 27017, "testing"
        )

    def tearDown(self):
        super().tearDown()
        c = MongoClient(
            'localhost',
            27017
        )
        c.drop_database("testing")


class FileSystemStrorageTestCase(ArchstorTestCase, unittest.TestCase):
    def setUp(self):
        archstor.app.config['TESTING'] = True
        self.tmpdir = TemporaryDirectory()
        tmpdirpath = self.tmpdir.name
        self.app = archstor.app.test_client()
        archstor.blueprint.BLUEPRINT.config['storage'] = \
            archstor.blueprint.FileSystemStorageBackend(
                tmpdirpath
        )

    def tearDown(self):
        del self.tmpdir

    def test_getRoot(self):
        rv = self.app.get("/")
        self.assertEqual(rv.status_code, 501)

    def test_rootPagination(self):
        pass


# class SwiftStorageTestCase(ArchstorTestCase, unittest.TestCase):
#    def setUp(self):
#        archstor.app.config['TESTING'] = True
#        self.app = archstor.app.test_client()
#        archstor.blueprint.BLUEPRINT.config['storage'] = \
#            archstor.blueprint.SwiftStorageBackend(
#                "http://127.0.0.1:12345/auth/v1.0",
#                '1',
#                "test:tester",
#                "RANDOMLYGENERATEDPASSWORDHERE",
#                'test',
#                container_name='testing'
#            )
#
#    def tearDown(self):
#        cursor = True
#        while cursor:
#            cursor, objs = archstor.blueprint.BLUEPRINT.config['storage']\
#                .get_object_id_list("0", None)
#            for x in objs:
#                archstor.blueprint.BLUEPRINT.config['storage'].del_object(x)


if __name__ == "__main__":
    unittest.main()
