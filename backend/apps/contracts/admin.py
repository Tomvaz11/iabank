from __future__ import annotations

from django.contrib import admin

from .models import ApiContractArtifact, ContractDiffReport


class ContractDiffReportInline(admin.TabularInline):
    model = ContractDiffReport
    extra = 0
    readonly_fields = ('tool', 'status', 'summary', 'logged_at', 'created_at')
    can_delete = False


@admin.register(ApiContractArtifact)
class ApiContractArtifactAdmin(admin.ModelAdmin):
    list_display = ('type', 'version', 'path', 'breaking_change', 'released_at', 'updated_at')
    list_filter = ('type', 'breaking_change')
    search_fields = ('version', 'path', 'checksum')
    inlines = (ContractDiffReportInline,)


@admin.register(ContractDiffReport)
class ContractDiffReportAdmin(admin.ModelAdmin):
    list_display = ('artifact', 'tool', 'status', 'logged_at')
    list_filter = ('tool', 'status')
    search_fields = ('summary', 'artifact__path', 'artifact__version')
