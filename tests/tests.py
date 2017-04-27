import archstor
import unittest
import json
from pymongo import MongoClient


class ArchstorTestCase:
    def response_200_json(self, rv):
        self.assertEqual(rv.status_code, 200)
        rt = rv.data.decode()
        rj = json.loads(rt)
        return rj

    def test_getRoot(self):
        rv = self.app.get("/")
        rj = self.response_200_json(rv)

    def test_rootPagination(self):
        pass

    def test_getObject(self):
        pass

    def test_putObject(self):
        pass

    def test_deleteObject(self):
        pass

    def test_deleteNonexistantObject(self):
        pass

    def test_objectOverwrite(self):
        pass


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


if __name__ == '__main__':
    unittest.main()
