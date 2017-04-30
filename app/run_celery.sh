#!/bin/sh
su -m docker-user -c "celery worker -A flask_celery.celery"