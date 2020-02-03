from django.contrib import admin
from .models import Worker, Pause, Statistic

admin.site.register(Worker)
admin.site.register(Pause)
admin.site.register(Statistic)