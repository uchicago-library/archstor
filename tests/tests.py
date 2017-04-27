import archstor
import unittest
from pymongo import MongoClient


class ArchstorTestCase(unittest.TestCase):
    def setUp(self):
        archstor.app.config['TESTING'] = True
        self.app = archstor.app.test_client()

    def tearDown(self):
        pass

    def test_getRoot(self):
        pass

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


class MongoStorageTestCases(ArchstorTestCase):
    def setUp(self):
        super().setUp()
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
