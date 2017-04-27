import datetime
import os

import time
from xml.etree import ElementTree
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from celery import Celery

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
    id = db.Column('id', db.Integer, primary_key = True)
    task_id = db.Column(db.String)
    weight = db.Column(db.Integer)
    date_add = db.Column(db.DateTime,default=datetime.datetime.now)

@celery.task(bind=True)
def test_task(self):
    for i in range(2, 10):
        self.update_state(state='TEST', meta={'count': i})
        time.sleep(10)

    return {'count': 10}

@celery.task(bind=True)
def parseXml(self):
    print("RUN")
    e = ElementTree.parse(os.path.join(app.config['UPLOAD_FOLDER'], 'test.xml')).getroot()
    graph = {}
    meta = {'count':0,'weight':0}

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
        meta['count']+=1
        self.update_state(state='PARSE',meta=meta)

    self.update_state(state='CALCULATE', meta=meta)
    weight = 0
    for point in graph.values():
        weight += len(point['childs'])
    meta['weight'] = weight

    return meta


@app.route('/')
def index():
    task = parseXml.apply_async()
    record = GraphRecord(task_id=task.id,weight=0)

    db.session.add(record)
    db.session.commit()

    return render_template('index.html', tasks=GraphRecord.query.all())


@app.route('/check/<task_id>')
def check(task_id):
    task = parseXml.AsyncResult(task_id)

    result = {
        'STATE' : task.state,
        'COUNT' : task.info.get('count')
    }
    return jsonify(result)


@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['tree']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        return redirect(url_for('index'))


@app.route('/parse')
def parse():
    e = ElementTree.parse(os.path.join(app.config['UPLOAD_FOLDER'], 'test.xml')).getroot()
    graph = {}

    for elem in e.findall('item'):
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

    weight = 0
    for point in graph.values():
        weight += len(point['childs'])

    return str(graph) + "<br>" + str(weight)


if __name__ == '__main__':
    db.create_all()
    app.run()