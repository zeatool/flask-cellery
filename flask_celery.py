import datetime
import os

import time
from xml.etree import ElementTree
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from celery import Celery
from itertools import cycle

UPLOAD_FOLDER = r'C:/pyProjects/flask_celery/tmp'

# Base configuration
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Celery configuration
app.config['BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name)
celery.conf.update(app.config)

# DB configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.sqlite3'
app.config['SECRET_KEY'] = "random string"

db = SQLAlchemy(app)


class GraphRecord(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    task_id = db.Column(db.String)
    weight = db.Column(db.Integer)
    state = db.Column(db.String)
    count = db.Column(db.Integer)
    date_add = db.Column(db.DateTime, default=datetime.datetime.now)


class GraphCalculator():
    filename = ''
    graph = {}
    weight = 0
    count = 0

    def __init__(self, filename=None):
        if filename != None:
            self.filename = filename
            tree = ElementTree.parse(os.path.join(app.config['UPLOAD_FOLDER'], self.filename)).getroot()
            self.elems = iter(tree.findall('item'))

    def next(self):
        try:
            elem = next(self.elems)
        except StopIteration:
            return False

        if (elem.find('id') != None):
            id = elem.find('id').text

            if (self.graph.get(id) == None):
                self.graph[id] = {'childs': set(), 'created': True}
            else:
                self.graph[id]['created'] = True

            if elem.find('parentId') != None:
                parent = elem.find('parentId').text

                if (self.graph.get(parent) == None):
                    self.graph[parent] = {'childs': set(), 'created': False}

                self.graph[parent]['childs'].add(id)

        self.count += 1
        return True

    def getMeta(self):
        return {'count': self.count, 'weight': self.weight}

    def calculate_graph_weight(self):
        self.weight = self.get_graph_weight(self.graph)

        return self.weight

    @staticmethod
    def get_graph_weight(graph):
        weight = 0

        for point in graph.values():
            if (point.get('created') == True):
                if point.get('childs') and isinstance(point['childs'], set):
                    weight += len(point['childs'])

        return weight


@celery.task(bind=True)
def test_task(self):
    for i in range(2, 10):
        self.update_state(state='TEST', meta={'count': i})
        time.sleep(10)

    return {'count': 10}


@celery.task(bind=True)
def calculate_graph_from_file(self, filename):
    graph = GraphCalculator(filename)
    meta = {'count': 0, 'weight': 0}

    while graph.next():
        meta = graph.getMeta()
        self.update_state(state='PARSE', meta=meta)

    self.update_state(state='CALCULATE', meta=meta)
    graph.calculate_graph_weight()
    meta = graph.getMeta()
    self.update_state(state='CALCULATE', meta=meta)

    GraphRecord.query.filter_by(task_id=self.request.id).update(
        {'weight': meta['weight'], 'state': 'SUCCESS', 'count': meta['count']})
    db.session.commit()

    return meta

# depricated
@celery.task(bind=True)
def parseXml(self, filename):
    e = ElementTree.parse(os.path.join(app.config['UPLOAD_FOLDER'], filename)).getroot()
    graph = {}
    meta = {'count': 0, 'weight': 0}

    for elem in e.findall('item'):
        time.sleep(0.5)
        if elem.find('parentId') != None:
            parent = elem.find('parentId').text
            id = elem.find('id').text

            if (graph.get(id) == None):
                graph[id] = {'childs': set(), 'created': True}
            else:
                graph[id]['created'] = True

            if (graph.get(parent) == None):
                graph[parent] = {'childs': set(), 'created': False}

            graph[parent]['childs'].add(id)
        meta['count'] += 1
        self.update_state(state='PARSE', meta=meta)

    self.update_state(state='CALCULATE', meta=meta)

    weight = calculate_graph_weight(graph)
    meta['weight'] = weight

    self.update_state(state='CALCULATED', meta=meta)
    GraphRecord.query.filter_by(task_id=self.request.id).update(
        {'weight': weight, 'state': 'SUCCESS', 'count': meta['count']})
    db.session.commit()

    return meta


def calculate_graph_weight(graph):
    weight = 0

    for point in graph.values():
        if (point.get('created') == True):
            if point.get('childs') and isinstance(point['childs'], set):
                weight += len(point['childs'])

    return weight


@app.route('/')
def index():
    # task = parseXml.apply_async(kwargs={'filename': 'test.xml'})
    # record = GraphRecord(task_id=task.id,weight=0)

    # db.session.add(record)
    # db.session.commit()

    return render_template('index.html', tasks=GraphRecord.query.order_by(GraphRecord.date_add.desc()).slice(0, 20))


@app.route('/check/<task_id>')
def check(task_id):
    task = parseXml.AsyncResult(task_id)

    result = {
        'STATE': task.state,
        'COUNT': 0,
        'WEIGHT': 0,
    }

    if task.info != None:
        result['COUNT'] = task.info.get('count')
        result['WEIGHT'] = task.info.get('weight')

    return jsonify(result)


@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        salt = str(datetime.datetime.now().timestamp()).replace('.', '')
        file = request.files['tree']
        filename = salt + '_' + secure_filename(file.filename)

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        task = calculate_graph_from_file.apply_async(kwargs={'filename': filename})
        record = GraphRecord(task_id=task.id, weight=0)

        db.session.add(record)
        db.session.commit()

        return redirect(url_for('index'))


if __name__ == '__main__':
    db.create_all()
    app.run()
