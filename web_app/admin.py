# admin.py
from django.contrib import admin
from .models import WrappedData

@admin.register(WrappedData)
class WrappedDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'year', 'created_at')
    list_filter = ('year',)
    search_fields = ('user__username',)
