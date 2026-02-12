from django.contrib import admin
from .models import UserClienteMembership

@admin.register(UserClienteMembership)
class UserClienteMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "cliente", "role", "ativo", "criado_em")
    list_filter = ("role", "ativo", "cliente")
    search_fields = ("user__username", "user__email", "cliente__nome")
    autocomplete_fields = ("user", "cliente")
