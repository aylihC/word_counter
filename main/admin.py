from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import SearchHistory

admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'date_joined', 'last_login', 'is_active')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'word_count', 'char_count', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('user__username', 'text')
    ordering = ('-created_at',)

