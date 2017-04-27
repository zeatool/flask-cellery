import os
import flask_celery
import unittest
import tempfile

class FlaskCeleryTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, flask_celery.app.config['DATABASE'] = tempfile.mkstemp()
        flask_celery.app.config['TESTING'] = True
        self.app = flask_celery.app.test_client()
        flask_celery.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(flask_celery.app.config['DATABASE'])

    def test_hello(self):
        assert True==True


if __name__ == '__main__':
    unittest.main()

