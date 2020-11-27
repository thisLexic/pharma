import datetime

from django import forms
from django.contrib import admin
from django.utils import timezone
from django.contrib.admin import DateFieldListFilter
from django.contrib.auth import get_user_model
from django.http import HttpResponse, FileResponse

from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin
from rangefilter.filter import DateRangeFilter
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from .models import Purchases, Purchase_Payment_Method, Products, Distributor, Transactions
from location.models import Branches
from finance.admin import BaseExpensePurchaseSubAdmin
from adminApiModel.utils import FilterBranchStaffPurchaseMethodDistributorDropDown, \
                                BranchFilter, \
                                TotalsumAdmin


class PurchasesResource(resources.ModelResource):
    branch = fields.Field(
        column_name='branch',
        attribute='branch',
        widget=ForeignKeyWidget(Branches, 'location'))
    class Meta:
        model = Purchases
        fields = (
            'date',
            'branch',
            'is_paid',
            'short_or_over',
            'delivered_worth',
            'invoice_worth',
            'invoice_range',
        )
        export_order = ('date', 'branch')


@admin.register(Purchases)
class PurchaseCustomAdmin(TotalsumAdmin, FilterBranchStaffPurchaseMethodDistributorDropDown):
    change_list_template = "admin/utils/change_list.html"
    totalsum_list = ['short_or_over', 'delivered_worth', 'invoice_worth']
    ordering = ['-date', 'branch', 'short_or_over']
    search_fields = ['invoice_low', 'invoice_high']
    resource_class = PurchasesResource
    list_display = ['date', 'branch', 'is_paid', 'format_short_or_over', 'delivered_worth', 'invoice_worth', 'invoice_range', 'invoice_file']
    list_filter = ['is_paid',
                    'is_valid',
                   BranchFilter,
                   ('date', DateRangeFilter),
                   ('date', DateFieldListFilter),
    ]
    actions = ['export']


    def format_short_or_over(self, obj):
        if not obj.short_or_over:
            return "-"
        return str(obj.short_or_over)
    format_short_or_over.short_description = 'short or over'



    def get_form(self, request, obj=None, **kwargs):
        user = request.user
        form = super().get_form(request, obj, **kwargs)
        disabled_fields = set()  # type: Set[str]

        if not user.is_superuser:
            disabled_fields |= {
                'manager',
                'short_or_over',
            }

        if not user.roles.is_manager:
            disabled_fields |= {
                'retailer',
                'staff',
                'is_paid',
                'payment_method',
            }

            if not (user.roles.is_assistant and user.roles.purchase_can_validate):
                disabled_fields |= {
                    'is_valid',
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
            return super().get_queryset(request
                   ).filter(manager=user)
        elif user.roles.is_assistant:
            days = user.roles.purchase_days
            branches = user.roles.purchase_branches.all()
            if days and branches:
                return super().get_queryset(request
                       ).filter(manager=user.roles.manager
                       ).filter(date__gte=timezone.now() - datetime.timedelta(days=days)
                       ).filter(branch__in=branches)
            else:
                raise RuntimeError("User if assistant but roles improperly configured")
        elif user.roles.is_retailer:
            days = user.roles.days
            if days:
                return super().get_queryset(request
                       ).filter(manager=user.roles.manager
                       ).filter(date__gte=timezone.now() - datetime.timedelta(days=days)
                       ).filter(branch__in=user.roles.branches.all())
            else:
                return super().get_queryset(request
                       ).filter(manager=user.roles.manager
                       ).filter(date__gte=timezone.now() - datetime.timedelta(days=1)
                       ).filter(branch__in=user.roles.branches.all())
        # elif user.roles.is_assistant:
        #     return super().get_queryset(request
        #            ).filter(manager=user.roles.manager)
        # else:
        #     return super().get_queryset(request
        #            ).filter(manager=user.roles.manager
        #            ).filter(date__gte=timezone.now() - datetime.timedelta(days=14)
        #            ).filter(branch__in=user.roles.branches.all())


    def save_model(self, request, obj, form, change):
        if request.user.roles.is_manager:
            obj.manager = request.user
        elif request.user.roles.is_assistant:
            obj.manager = request.user.roles.manager
            obj.retailer = request.user
        elif request.user.roles.is_retailer:
            obj.manager = request.user.roles.manager
            obj.retailer = request.user
        else:
            obj.manager = request.user.roles.manager
            obj.staff = request.user
        super().save_model(request, obj, form, change)


    # def export(self, request, queryset):
    #     response = HttpResponse(content_type='application/pdf')
    #     response['Content-Disposition'] = 'inline; filename="purchases.pdf"'

    #     filename = "purchases.pdf"
    #     data = [
    #         ["Date", "Branch", "Is Paid", "Shrt/Ovr", "Del Worth", "Inv Worth", "Inv Range"],
    #     ]
    #     for q in queryset:
    #         row = []
    #         row.append(str(q.date))
    #         row.append(str(q.branch.location))
    #         row.append(str(q.is_paid))
    #         row.append(str(q.short_or_over))
    #         row.append(str(q.delivered_worth))
    #         row.append(str(q.invoice_worth))
    #         row.append(str(q.invoice_range))
    #         data.append(row)

    #     table = Table(data)
    #     buffer = BytesIO()
    #     p = canvas.Canvas(buffer)
    #     p.setPageSize(landscape(A4))
    #     width, height = A4
    #     p.drawString(30, 570, "Purchases")
    #     table.setStyle(TableStyle(
    #         [
    #             ('FONTSIZE', (0, 0), (-1, -1), 15),
    #         ]
    #     ))
    #     table.wrapOn(p, width, height)
    #     table.drawOn(p, 30, 100)


    #     # for bimonthly_in in queryset:
    #     #     staff = bimonthly_in.staff
    #     #     if size < 20:
    #     #         size = 760
    #     #         p.showPage()

    #     #         p.drawString(20, 780, "First Name")
    #     #         p.drawString(120, 780, "Last Name")
    #     #         p.drawString(220, 780, "Total Salary")
    #     #     p.drawString(20, size+10, "---------------------------------------------------------------------------------------------------------------------------------")
    #     #     p.drawString(20, size, staff.first_name)
    #     #     p.drawString(120, size, staff.last_name)
    #     #     p.drawString(220, size, str(bimonthly_in.pay_tot))
    #     #     size -= 20

    #     p.showPage()
    #     p.save()

    #     pdf = buffer.getvalue()
    #     buffer.close()
    #     response.write(pdf)

    #     return response
    # export.short_description = "Export as PDF"


@admin.register(Purchase_Payment_Method)
class CustomPurchasePaymentMethodAdmin(BaseExpensePurchaseSubAdmin):
    pass


@admin.register(Distributor)
class CustomDistributorAdmin(BaseExpensePurchaseSubAdmin):
    pass


class ProductsResource(resources.ModelResource):
    class Meta:
        model = Products
        fields = (
            'name',
            'size',
            'price',
            'is_active',
            'date_start',
            'product_id',
            'items_per_package',
        )
        export_order = ('name', 'size', 'price')
        skip_unchanged = True
        report_skipped = True
        exclude = ('id','manager',)
        import_id_fields = (
            'name',
            'size',
            'price',
            'is_active',
            'product_id',
            'items_per_package',
        )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(ProductsResource, self).__init__(*args, **kwargs)



    def before_save_instance(self, instance, using_transactions, dry_run):
        if self.request.user.roles.is_manager:
            instance.manager = self.request.user
        else:
            instance.manager = self.request.user.roles.manager
        return instance


@admin.register(Products)
class ProductCustomAdmin(ImportExportModelAdmin):
    ordering = ['-is_active', 'name', 'size', 'price']
    search_fields = ['name', 'size']
    list_display = ['name', 'size', 'price', 'is_active']
    list_filter = ['is_active',]
    readonly_fields = ['date_start',]
    resource_class = ProductsResource


    def get_form(self, request, obj=None, **kwargs):
        user = request.user
        form = super().get_form(request, obj, **kwargs)
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
            super().save_model(request, obj, form, change)
        elif request.user.roles.is_assistant:
            obj.manager = request.user.roles.manager
            super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        user = request.user
        if user.is_superuser:
            return Products.objects.all()
        elif user.roles.is_manager:
            return user.products
        else:
            return user.roles.manager.products


    def get_resource_kwargs(self, request, *args, **kwargs):
        """ Passing request to resource obj to control exported fields dynamically """
        return {'request': request}



class TransactionsResource(resources.ModelResource):
    branch = fields.Field(
        column_name='branch',
        attribute='branch',
        widget=ForeignKeyWidget(Branches, 'location'))
    class Meta:
        model = Transactions
        fields = (
            'date',
            'branch',
            'product',
            'count',
            'is_valid',
        )
        export_order = ('date', 'branch')



@admin.register(Transactions)
class TransactionCustomAdmin(ImportExportModelAdmin):
    ordering = ['-date', '-time', 'branch', 'product']
    # list_display = ['date', 'time', 'branch', 'product', 'count', 'is_valid']
    list_display = ['retailer', 'time', 'product', 'count']
    search_fields = ['product']
    list_filter = ['is_valid',
                   ('date', DateRangeFilter),
    ]
    readonly_fields = ['date']
    resource_class = TransactionsResource


    def get_form(self, request, obj=None, **kwargs):
        user = request.user
        form = super().get_form(request, obj, **kwargs)
        disabled_fields = set()

        form.base_fields['branch'].initial = request.user.cur_branch.branch.id

        if not user.is_superuser:
            disabled_fields |= {
                'manager',
                'date',
            }

        if not user.roles.is_manager:
            disabled_fields |= {
                'retailer',
                'branch',
                'is_valid'
            }


        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form


    def get_queryset(self, request):
        user = request.user
        if user.is_superuser:
            return Transactions.objects.all()
        elif user.roles.is_manager:
            return user.transactions
        else:
            return user.roles.manager.transactions.filter(manager=user.roles.manager
                       ).filter(date__gte=timezone.now() - datetime.timedelta(days=1)
                       ).filter(branch__in=user.roles.branches.all())


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "branch":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    Branches.objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = request.user.branches.filter(is_open=True)
            else:
                kwargs["queryset"] = request.user.roles.branches.filter(is_open=True).filter(id=request.user.cur_branch.branch.id)
        elif db_field.name == "product":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    Products.objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = request.user.products.filter(is_active=True)
            else:
                kwargs["queryset"] = request.user.roles.manager.products.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return [(None, {'fields': ('retailer', 'branch', 'product', 'count', 'is_valid')}),]
        elif request.user.roles.is_manager:
            if obj == None:
                return [(None, {'fields': ('retailer', 'branch', 'product', 'count', 'is_valid')}),]
            return [(None, {'fields': ('retailer', 'branch', 'product', 'count', 'is_valid', 'date', 'time')}),]
        else:
            return [(None, {'fields': ('branch', 'product', 'count')}),]
    # manager
    # retailer
    # branch
       # product
    # count
    # is_valid
    # date 