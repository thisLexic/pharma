from django.contrib import admin

from location import models
from adminApiModel.utils import FilterBranchStaffDropDown


@admin.register(models.Branches)
class BranchAdmin(admin.ModelAdmin):


    def get_queryset(self, request):
        user = request.user

        if user.is_superuser:
            return super().get_queryset(request)
        elif user.roles.is_manager:
            return user.branches
        elif user.roles.is_assistant:
            return user.roles.manager.branches


    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        user = request.user
        disabled_fields = set()  # type: Set[str]

        if not user.is_superuser:
            disabled_fields |= {
                'manager',
            }

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form

    def save_model(self, request, obj, form, change):
        if request.user.roles.is_manager:
            obj.manager = request.user
        else:
            obj.manager = request.user.roles.manager
        super().save_model(request, obj, form, change)


@admin.register(models.Current_Branch)
class CurrentBranchAdmin(FilterBranchStaffDropDown):
    ordering = ['user', 'branch']
    list_display = ['user', 'branch']


    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        user = request.user
        disabled_fields = set()  # type: Set[str]

        if not user.is_superuser:
            disabled_fields |= {
                'manager',
            }

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form

    def get_queryset(self, request):
        user = request.user

        if user.is_superuser:
            return super().get_queryset(request)
        elif user.roles.is_manager:
            return user.staff_branches
        else:
            return models.Current_Branch.objects.filter(user=user)


    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        user = request.user
        disabled_fields = set()  # type: Set[str]

        if not user.is_superuser:
            disabled_fields |= {
                'manager',
            }

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form


    def save_model(self, request, obj, form, change):
        if request.user.roles.is_manager:
            obj.manager = request.user
        else:
            obj.manager = request.user.roles.manager
        super().save_model(request, obj, form, change)