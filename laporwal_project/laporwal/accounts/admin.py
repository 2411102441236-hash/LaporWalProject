from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_admin_dinas', 'is_staff')
    list_filter = ('is_admin_dinas', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Info Tambahan', {'fields': ('phone', 'kota', 'avatar', 'is_admin_dinas')}),
    )
