from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Worker(models.Model):
    name = models.CharField(max_length=30)
    telegram_id = models.IntegerField()
    alias = models.CharField(max_length=20, null=True, default=None)
    sick = models.DateField(null=True, default=None, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(blank=True, null=True)


class Statistic(models.Model):
    worker_id = models.IntegerField()
    current_status = models.CharField(max_length=20, default=None, null=True)
    place = models.CharField(max_length=10, default='Дома')
    start_time = models.DateTimeField(default=None, null=True)
    end_time = models.DateTimeField(null=True, default=None)
    current_day = models.DateField(default=timezone.now)
    wait = models.IntegerField(default=0)
    task = models.TextField(default=None, null=True)


class Pause(models.Model):
    statistic_id = models.IntegerField()
    start_pause = models.DateTimeField(null=True, default=None)
    total_time = models.DurationField(null=True, default=timedelta(seconds=0, minutes=0, hours=0), blank=True)

