import archstor
import unittest
import json
from uuid import uuid4
from io import BytesIO
from pymongo import MongoClient
from tempfile import TemporaryDirectory


class ArchstorTestCase:
    def response_200_json(self, rv):
        self.assertEqual(rv.status_code, 200)
        rt = rv.data.decode()
        rj = json.loads(rt)
        return rj

    def test_getRoot(self):
        rv = self.app.get("/")
        self.response_200_json(rv)

    def test_rootPagination(self):
        pass

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
        self.assertEqual(rv.status_code, 500)

    def test_objectOverwrite(self):
        id = uuid4().hex
        obj1 = BytesIO(b"this is a test object")
        rv1 = self.app.put("/{}".format(id), data={"object": (obj1, "test.txt")})
        rj1 = self.response_200_json(rv1)
        self.assertEqual(rj1['added'], True)
        obj2 = BytesIO(b"this is another object")
        rv2 = self.app.put("/{}".format(id), data={"object": (obj2, "test.txt")})
        self.assertEqual(rv2.status_code, 500)


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
        self.assertEqual(rv.status_code, 500)


if __name__ == '__main__':
    unittest.main()
