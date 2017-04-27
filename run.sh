#!/usr/bin/env bash
celery worker -A flask_celery.celery
python flask_celery.py