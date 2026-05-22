from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
	model = CustomUser
	ordering = ('id',)
	list_display = ('email', 'first_name', 'last_name', 'role', 'agency', 'is_staff', 'is_active')
	list_filter = ('role', 'agency', 'is_staff', 'is_active', 'is_superuser')
	search_fields = ('email', 'first_name', 'last_name')

	fieldsets = (
		(None, {'fields': ('email', 'password')}),
		('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 'role', 'agency')}),
		(
			'Permissions',
			{'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')},
		),
		('Important dates', {'fields': ('last_login', 'date_joined')}),
	)

	add_fieldsets = (
		(
			None,
			{
				'classes': ('wide',),
				'fields': ('email', 'password1', 'password2', 'role', 'agency', 'is_staff', 'is_active'),
			},
		),
	)
