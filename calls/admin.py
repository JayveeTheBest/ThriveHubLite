from django.contrib import admin
from .models import (
    Caller,
    CallSession,
    ReasonForCalling,
    Intervention,
    SuicideMethod,
    RiskDetail,
    SourceOfInfo,
    SiteConfig
)


@admin.register(Caller)
class CallerAdmin(admin.ModelAdmin):
    list_display = ('name', 'gender', 'status', 'age', 'location', 'source_of_info')
    search_fields = ('name', 'location', 'source_of_info')
    list_filter = ('gender', 'status')


@admin.register(CallSession)
class CallSessionAdmin(admin.ModelAdmin):
    list_display = ('date', 'responder', 'caller', 'shift', 'risk_level', 'length_of_call')
    list_filter = ('shift', 'risk_level', 'date')
    search_fields = ('caller__name', 'responder__username', 'code')
    readonly_fields = ('created_at',)


@admin.register(ReasonForCalling)
class ReasonForCallingAdmin(admin.ModelAdmin):
    list_display = ('label',)
    search_fields = ('label',)


@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display = ('label',)
    search_fields = ('label',)


@admin.register(SuicideMethod)
class SuicideMethodAdmin(admin.ModelAdmin):
    list_display = ('label',)
    search_fields = ('label',)


@admin.register(SourceOfInfo)
class SourceOfInfoAdmin(admin.ModelAdmin):
    list_display = ('label',)
    search_fields = ('label',)


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Prevent adding more than one SiteConfig
        if SiteConfig.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of SiteConfig
        return False