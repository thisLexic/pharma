from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.utils import label_for_field
from django.db.models import Sum
from django.db.models.fields import FieldDoesNotExist

from location.models import Branches
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin


class FilterBranchDropDown(admin.ModelAdmin):

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "branches" or db_field.name == "sale_branches" or db_field.name == "expense_branches" or db_field.name == "purchase_branches" or db_field.name == "hours_in_branches":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    Branches.objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = request.user.branches.filter(is_open=True)
            elif request.user.roles.is_assistant:
                kwargs["queryset"] = request.user.roles.manager.branches.filter(is_open=True)
            else:
                kwargs["queryset"] = request.user.roles.branches.filter(is_open=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "branch":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    Branches.objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = request.user.branches.filter(is_open=True)
            else:
                kwargs["queryset"] = request.user.roles.branches.filter(is_open=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class FilterStaffDropDown(admin.ModelAdmin):


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "staff" or db_field.name == "retailer":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    get_user_model().objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = \
                    get_user_model().objects.filter(
                        roles__manager=request.user)
            else:
                kwargs["queryset"] = \
                    get_user_model().objects.filter(
                        roles__manager=request.user.roles.manager)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class FilterBranchSpecificStaffDropDown(admin.ModelAdmin):


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "staff" or db_field.name == "retailer" or db_field.name == "user":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    get_user_model().objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = \
                    get_user_model().objects.filter(
                        roles__manager=request.user)
            else:
                kwargs["queryset"] = \
                    get_user_model().objects.filter(
                        roles__manager=request.user.roles.manager).filter(
                        roles__branches__in=request.user.roles.branches.all()).distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class HistoryFilterBranchSpecificStaffDropDown(SimpleHistoryAdmin):


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "staff" or db_field.name == "retailer" or db_field.name == "user":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    get_user_model().objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = \
                    get_user_model().objects.filter(
                        roles__manager=request.user)
            else:
                kwargs["queryset"] = \
                    get_user_model().objects.filter(
                        roles__manager=request.user.roles.manager).filter(
                        roles__branches__in=request.user.roles.branches.all()).distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class FilterBranchStaffDropDown(admin.ModelAdmin):


    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if db_field.name == "staff" or db_field.name == "retailer" or db_field.name == "user":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    get_user_model().objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = \
                    get_user_model().objects.filter(
                        roles__manager=request.user)
            else:
                kwargs["queryset"] = \
                    get_user_model().objects.filter(
                        roles__manager=request.user.roles.manager)
        elif db_field.name == "branch":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    Branches.objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = request.user.branches.filter(is_open=True)
            else:
                kwargs["queryset"] = request.user.roles.branches.filter(is_open=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "branches":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    Branches.objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = request.user.branches.filter(is_open=True)
            else:
                kwargs["queryset"] = request.user.roles.branches.filter(is_open=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class FilterBranchStaffBankDropDown(admin.ModelAdmin):


    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if db_field.name == "staff" or db_field.name == "retailer":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    get_user_model().objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = \
                    get_user_model().objects.filter(
                        roles__manager=request.user)
            else:
                kwargs["queryset"] = \
                    get_user_model().objects.filter(
                        roles__manager=request.user.roles.manager)
        elif db_field.name == "branch":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    Branches.objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = request.user.branches.filter(is_open=True)
            else:
                kwargs["queryset"] = request.user.roles.branches.filter(is_open=True)
        elif db_field.name == "bank":
            if request.user.roles.is_manager:
                kwargs["queryset"] = request.user.banks.filter(is_active=True)
            else:
                kwargs["queryset"] = request.user.roles.manager.banks.filter(is_active=True)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class HistoryFilterBranchStaffBankDropDown(admin.ModelAdmin):


    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if db_field.name == "staff" or db_field.name == "retailer":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    get_user_model().objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = \
                    get_user_model().objects.filter(
                        roles__manager=request.user)
            else:
                kwargs["queryset"] = \
                    get_user_model().objects.filter(
                        roles__manager=request.user.roles.manager)
        elif db_field.name == "branch":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    Branches.objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = request.user.branches.filter(is_open=True)
            else:
                kwargs["queryset"] = request.user.roles.branches.filter(is_open=True)
        elif db_field.name == "bank":
            if request.user.roles.is_manager:
                kwargs["queryset"] = request.user.banks.filter(is_active=True)
            else:
                kwargs["queryset"] = request.user.roles.manager.banks.filter(is_active=True)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "branches":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    Branches.objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = request.user.branches.filter(is_open=True)
            else:
                kwargs["queryset"] = request.user.roles.branches.filter(is_open=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class FilterBranchStaffPurchaseMethodDistributorDropDown(admin.ModelAdmin):


    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if db_field.name == "staff" or db_field.name == "retailer":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    get_user_model().objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = \
                    get_user_model().objects.filter(
                        roles__manager=request.user)
            else:
                kwargs["queryset"] = \
                    get_user_model().objects.filter(
                        roles__manager=request.user.roles.manager)
        elif db_field.name == "branch":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    Branches.objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = request.user.branches.filter(is_open=True)
            else:
                kwargs["queryset"] = request.user.roles.branches.filter(is_open=True)
        elif db_field.name == 'payment_method':
            if request.user.roles.is_manager:
                kwargs["queryset"] = request.user.purchase_payment_methods.filter(is_active=True)
            else:
                kwargs["queryset"] = request.user.roles.manager.purchase_payment_methods.filter(is_active=True)
        elif db_field.name == 'distributor':
            if request.user.roles.is_manager:
                kwargs["queryset"] = request.user.distributors.filter(is_active=True)
            else:
                kwargs["queryset"] = request.user.roles.manager.distributors.filter(is_active=True)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "branches":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    Branches.objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = request.user.branches.filter(is_open=True)
            else:
                kwargs["queryset"] = request.user.roles.branches.filter(is_open=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

class BranchFilter(SimpleListFilter):
    title = 'branch'
    parameter_name = 'branch'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            branches = \
                Branches.objects.all()
        elif request.user.roles.is_manager:
            branches = request.user.branches.all()
        else:
            branches = request.user.roles.manager.branches.all()
        return [(b.id, b.location) for b in branches]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(branch=self.value())
        return queryset


class BankFilter(SimpleListFilter):
    title = 'bank'
    parameter_name = 'bank'

    def lookups(self, request, model_admin):
        if request.user.roles.is_manager:
            banks = request.user.banks.filter(is_active=True)
        else:
            banks = request.user.roles.manager.banks.filter(is_active=True)
        return [(b.id, b.name) for b in banks]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(bank=self.value())
        return queryset


class ManyBranchFilter(SimpleListFilter):
    title = 'branch'
    parameter_name = 'branch'

    def lookups(self, request, model_admin):
        if request.user.roles.is_manager:
            branches = request.user.branches.all()
        else:
            branches = request.user.roles.manager.branches.all()
        return [(b.id, b.location) for b in branches]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(branches__id=self.value())
        return queryset


class ExpenseTypeFilter(SimpleListFilter):
    title = 'Type of Expense'
    parameter_name = 'type_of_expense'

    def lookups(self, request, model_admin):
        if request.user.roles.is_manager:
            expense_types = request.user.expense_types.all()
        else:
            expense_types = request.user.roles.manager.expense_types.all()
        return [(e.id, e.name) for e in expense_types.order_by('name')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(type_of_expense=self.value())
        return queryset


class TotalsumAdmin(ImportExportModelAdmin):
    # change_list_template = "admin/finance/sales/change_list.html"
    # totalsum_list = ('gross_sales',)

    unit_of_measure = ""
    totalsum_decimal_places = 2

    def changelist_view(self, request, extra_context=None):
        response = super(TotalsumAdmin, self).changelist_view(request, extra_context)
        if not hasattr(response, "context_data") or "cl" not in response.context_data:
            return response
        filtered_query_set = response.context_data["cl"].queryset
        extra_context = extra_context or {}
        extra_context["totals"] = {}
        extra_context["unit_of_measure"] = self.unit_of_measure

        for elem in self.totalsum_list:
            try:
                self.model._meta.get_field(elem)  # Checking if elem is a field
                total = filtered_query_set.aggregate(totalsum_field=Sum(elem))[
                    "totalsum_field"
                ]
                if total is not None:
                    extra_context["totals"][
                        label_for_field(elem, self.model, self)
                    ] = round(total, self.totalsum_decimal_places)
            except FieldDoesNotExist:  # maybe it's a property
                if hasattr(self.model, elem):
                    total = 0
                    for f in filtered_query_set:
                        total += getattr(f, elem, 0)
                    extra_context["totals"][
                        label_for_field(elem, self.model, self)
                    ] = round(total, self.totalsum_decimal_places)

        response.context_data.update(extra_context)
        return response