import os
import xml

import flask_celery
import unittest
import tempfile


class FlaskCeleryTestCase(unittest.TestCase):
    def setUp(self):
        b = 1

    def tearDown(self):
        b = 0

    def test_hello(self):
        assert True == True

    def test_graph_weight_calculate(self):

        graph = {
            '1': {'childs': {'2', '3', '4'},'created':True}
        }
        assert flask_celery.GraphCalculator.get_graph_weight(graph) == 3

        graph = {
            '1': {'childs': {'2', '3', '4'},'created':False}
        }
        assert flask_celery.GraphCalculator.get_graph_weight(graph) == 0

        graph = {
            '1': {'childs': {'2', '1', '4'}, 'created': True},
            '2': {'childs': {'4'}, 'created': False},
            '5': {'childs': {'3', '8', '9'}, 'created': True}
        }
        assert flask_celery.GraphCalculator.get_graph_weight(graph) == 6

        graph = {}
        assert flask_celery.GraphCalculator.get_graph_weight(graph) == 0

        graph = {
            '1': {'childs': {'2', '3', '4'}}
        }
        assert flask_celery.GraphCalculator.get_graph_weight(graph) == 0

        graph = {
            '1': {'chilrrrrrrrrds': {'2', '3', '4'},'everybody':'dance now'}
        }
        assert flask_celery.GraphCalculator.get_graph_weight(graph) == 0

        graph = {
            '1': {'childs': 999,'created':True}
        }
        assert flask_celery.GraphCalculator.get_graph_weight(graph) == 0

        graph = {
            '1': {'childs': {'1'}, 'created': {'454'}}
        }
        assert flask_celery.GraphCalculator.get_graph_weight(graph) == 0

    def test_parse(self):
        t = flask_celery.GraphCalculator('test/test.xml')
        t.parseFile()

        while t.next():
            t.getMeta()

        meta = t.getMeta()
        assert meta['count'] == 64

    def test_parse_file_not_found(self):
        t = flask_celery.GraphCalculator('test_not_found.xml')

        with self.assertRaises(FileNotFoundError):
            t.parseFile()

    def test_parse_file_not_xml(self):
        t = flask_celery.GraphCalculator('test/test_no_xml.xml')
        with self.assertRaises(xml.etree.ElementTree.ParseError):
            t.parseFile()

    def test_parse_no_items(self):
        t = flask_celery.GraphCalculator('test/test_no_items.xml')
        t.parseFile()

    def test_parse_failed_items(self):
        t = flask_celery.GraphCalculator('test/test_failed_items.xml')
        t.parseFile()




if __name__ == '__main__':
    unittest.main()
