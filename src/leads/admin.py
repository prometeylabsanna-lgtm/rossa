from django.contrib import admin
from unfold.admin import ModelAdmin

from leads.models import ContactLead, OrderRequest, PartnershipLead


@admin.register(OrderRequest)
class OrderRequestAdmin(ModelAdmin):
    list_display = ('created_at', 'product_name', 'fabric_name', 'shade_name', 'price', 'name', 'phone', 'status')
    list_filter = ('status', 'fulfillment')
    search_fields = ('product_name', 'name', 'phone', 'email', 'sku')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)


@admin.register(PartnershipLead)
class PartnershipLeadAdmin(ModelAdmin):
    list_display = ('created_at', 'company', 'phone', 'email', 'collab_type', 'status')
    list_filter = ('status', 'collab_type')
    search_fields = ('company', 'name', 'phone', 'email')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)


@admin.register(ContactLead)
class ContactLeadAdmin(ModelAdmin):
    list_display = ('created_at', 'name', 'phone', 'status')
    list_filter = ('status',)
    search_fields = ('name', 'phone', 'message')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)
