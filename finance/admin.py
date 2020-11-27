import datetime, calendar

from django.contrib import admin
from django.utils import timezone
from django.contrib.admin import SimpleListFilter
from django.contrib.admin import DateFieldListFilter
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from rangefilter.filter import DateRangeFilter

from location.models import Branches
from stock.models import Purchases
from staff.models import Bimonthly_In
from finance.models  import Sales, Expense_Types, Expense_Methods, \
                            Banks, Expenses, Bank_Status
from adminApiModel.utils import FilterBranchStaffDropDown, \
                                FilterBranchStaffBankDropDown, \
                                BranchFilter, \
                                BankFilter, \
                                ExpenseTypeFilter, \
                                TotalsumAdmin, HistoryFilterBranchStaffBankDropDown


class SalesResource(resources.ModelResource):
    branch = fields.Field(
        column_name='branch',
        attribute='branch',
        widget=ForeignKeyWidget(Branches, 'location'))
    class Meta:
        model = Sales
        fields = (
            'date',
            'branch',
            'short_or_over',
            'gross_sales',
            'cash_on_caja',
            'cash_for_deposit',
        )
        export_order = ('date', 'branch')


@admin.register(Sales)
class CustomSaleAdmin(TotalsumAdmin, HistoryFilterBranchStaffBankDropDown):
    change_list_template = "admin/utils/change_list.html"
    totalsum_list = ('gross_sales','cash_on_caja', 'short_or_over', 'caja_minus_deposit', 'cash_for_deposit')
    resource_class = SalesResource
    list_per_page = 10
    ordering = ['-date', 'branch']
    list_display = ['date', 'branch', 'short_or_over', 'cash_on_caja', 'gross_sales', 'cash_for_deposit', 'caja_minus_deposit', 'remark', 'num_trxn', 'num_cstmr', 'OR_nums', 'num_rcpt', 'total_disc', 'petty_cash', 'bank', 'was_deposited', 'is_valid', 'file', 'retailer']
    list_filter = ['is_valid',
                    BranchFilter,
                   ('date', DateRangeFilter),
                   ('date', DateFieldListFilter),
    ]


    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        user = request.user
        disabled_fields = set()  # type: Set[str]

        if not user.is_superuser:
            disabled_fields |= {
                'manager',
                'short_or_over',
            }

        if not user.roles.is_manager:
            disabled_fields |= {
                'retailer',
            }

            if not user.roles.sale_change_deposit:
                disabled_fields |= {
                    'was_deposited',
                }

            if not (user.roles.is_assistant and user.roles.sale_can_validate):
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
            days = user.roles.sale_days
            branches = user.roles.sale_branches.all()
            if days and branches:
                return super().get_queryset(request
                       ).filter(manager=user.roles.manager
                       ).filter(date__gte=timezone.now() - datetime.timedelta(days=days)
                       ).filter(branch__in=branches)
            else:
                raise RuntimeError("User is assistant but roles improperly configured")
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

        # elif user.roles.is_retailer:
        #     return super().get_queryset(request
        #            ).filter(manager=user.roles.manager
        #            ).filter(date__gte=timezone.now() - datetime.timedelta(days=1)
        #            ).filter(branch__in=user.roles.branches.all())


    def save_model(self, request, obj, form, change):
        if request.user.roles.is_manager:
            obj.manager = request.user
            obj.retailer = request.user
        elif request.user.roles.is_retailer or request.user.roles.is_assistant:
            obj.manager = request.user.roles.manager
            obj.retailer = request.user
        super().save_model(request, obj, form, change)


    def save_related(self, request, form, formsets, change):
        try:
            bank_status = form.instance.bank_status
        except Sales.bank_status.RelatedObjectDoesNotExist:
            bank_status = None

        if (not bank_status) and form.instance.was_deposited:
            if request.user.is_superuser:
                manager = request.user
            elif request.user.roles.is_manager:
                manager = request.user
            else:
                manager = request.user.roles.manager
            Bank_Status(manager=manager,
                        bank=form.instance.bank,
                        date=datetime.datetime.combine(form.instance.date, datetime.datetime.now().time()),
                        sale_report=form.instance,
                        deposit=form.instance.cash_for_deposit,
                ).save()
        elif bank_status:
            bank_status.deposit = form.instance.cash_for_deposit
            bank_status.bank = form.instance.bank
            bank_status.save()


# manager
# bank
# date
# sale_report
# expense_report
# deposit
# withdraw
# update
# remark
# check
# online
# image


class BaseExpensePurchaseSubAdmin(admin.ModelAdmin):


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


    def get_queryset(self, request):
        user = request.user
        if user.is_superuser:
            return super().get_queryset(request)
        elif user.roles.is_manager:
            return super().get_queryset(request
                   ).filter(manager=user)
        elif user.roles.is_assistant:
            return super().get_queryset(request
                   ).filter(manager=user.roles.manager)


@admin.register(Expense_Types)
class CustomExpenseTypeAdmin(BaseExpensePurchaseSubAdmin):
    pass


@admin.register(Expense_Methods)
class CustomExpenseMethodAdmin(BaseExpensePurchaseSubAdmin):
    pass


@admin.register(Banks)
class CustomBankAdmin(BaseExpensePurchaseSubAdmin):
    pass


class ExpensesResource(resources.ModelResource):
    branch = fields.Field(
        column_name='branch',
        attribute='branch',
        widget=ForeignKeyWidget(Branches, 'location'))
    type_of_expense = fields.Field(
        column_name='Type of Expense',
        attribute='type_of_expense',
        widget=ForeignKeyWidget(Expense_Types, 'name'))
    method_of_payment = fields.Field(
        column_name='Method of Payment',
        attribute='method_of_payment',
        widget=ForeignKeyWidget(Expense_Methods, 'name'))
    bank = fields.Field(
        column_name='Bank',
        attribute='bank',
        widget=ForeignKeyWidget(Banks, 'name'))
    class Meta:
        model = Expenses
        fields = (
            'date',
            'branch',
            'amount',
            'type_of_expense',
            'method_of_payment',
            'bank',
        )
        export_order = ('date', 'branch')


@admin.register(Expenses)
class CustomExpenseAdmin(TotalsumAdmin):
    change_list_template = "admin/utils/change_list.html"
    totalsum_list = ('amount',)
    resource_class = ExpensesResource
    ordering = ['-date', 'branch']
    list_display = ['date', 'branch', 'is_paid', 'amount', 'type_of_expense', 'method_of_payment', 'bank', 'remark', 'is_valid', 'bill_stmt', 'prf_pay', 'attch_doc', 'doc_desc']
    list_filter = ['is_valid',
                   BranchFilter,
                   ExpenseTypeFilter,
                   ('date', DateRangeFilter),
                   ('date', DateFieldListFilter),
    ]
    actions = ['expense_weekly_report', 'expense_monthly_report']


    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        user = request.user
        disabled_fields = set()  # type: Set[str]

        if not user.is_superuser:
            disabled_fields |= {
                'manager',
            }

        if not user.roles.is_manager:
            disabled_fields |= {
                'retailer',
            }
            if not (user.roles.is_assistant and user.roles.expense_can_validate):
                disabled_fields |= {
                    'is_valid',
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
            obj.retailer = request.user
        super().save_model(request, obj, form, change)


    def get_queryset(self, request):
        user = request.user
        if user.is_superuser:
            return super().get_queryset(request)
        elif user.roles.is_manager:
            return super().get_queryset(request
                   ).filter(manager=user)
        elif user.roles.is_assistant:
            days = user.roles.expense_days
            branches = user.roles.expense_branches.all()
            if days and branches:
                return super().get_queryset(request
                       ).filter(manager=user.roles.manager
                       ).filter(date__gte=timezone.now() - datetime.timedelta(days=days)
                       ).filter(branch__in=branches)
            else:
                raise RuntimeError("User is assistant but roles improperly configured")
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


    def save_related(self, request, form, formsets, change):
        try:
            bank_status = form.instance.bank_status
        except Expenses.bank_status.RelatedObjectDoesNotExist:
            bank_status = None

        if (not bank_status) and form.instance.is_valid and form.instance.bank:
            if request.user.is_superuser:
                manager = request.user
            elif request.user.roles.is_manager:
                manager = request.user
            else:
                manager = request.user.roles.manager
            Bank_Status(manager=manager,
                        bank=form.instance.bank,
                        date=datetime.datetime.combine(form.instance.date, datetime.datetime.now().time()),
                        expense_report=form.instance,
                        withdraw=form.instance.amount,
                ).save()
        elif bank_status:
            bank_status.withdraw = form.instance.amount
            bank_status.bank = form.instance.bank
            bank_status.save()


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


        elif db_field.name == "type_of_expense":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    Expense_Types.objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = request.user.expense_types.filter(is_active=True)
            else:
                kwargs["queryset"] = request.user.roles.manager.expense_types.filter(is_active=True)


        elif db_field.name == "method_of_payment":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    Expense_Methods.objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = request.user.expense_methods.filter(is_active=True)
            else:
                kwargs["queryset"] = request.user.roles.manager.expense_methods.filter(is_active=True)


        elif db_field.name == "bank":
            if request.user.is_superuser:
                kwargs["queryset"] = \
                    Banks.objects.all()
            elif request.user.roles.is_manager:
                kwargs["queryset"] = request.user.banks.filter(is_active=True)
            else:
                kwargs["queryset"] = request.user.roles.manager.banks.filter(is_active=True)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)



    def expense_weekly_report(self, request, queryset):
        # the queryset itself is not necessarily the most important
        # the queryset must just include the right start and end dates

        if not request.user.roles.is_manager:
            raise RuntimeError("User must be a manager to perform this action")

        constant_body_top = 740

        response = CustomExpenseAdmin.getResponse()
        p, buffer = CustomExpenseAdmin.getPage()
        headerInfo = CustomExpenseAdmin.getHeaderInfo(queryset)

        p = CustomExpenseAdmin.addHeader(p, headerInfo)
        sales, complete_total_sales = CustomExpenseAdmin.getSales(headerInfo['startDate'], headerInfo['endDate'], headerInfo['branches'])
        new_body_top = CustomExpenseAdmin.addTable(p, sales, constant_body_top, "Sales", constant_body_top, headerInfo, "weekly")
        
        expenseTypes = []
        expenseTypeObjects = Expense_Types.objects.filter(is_active=True).filter(manager=request.user)
        for expType in expenseTypeObjects:
            expenseTypes.append(expType.name)

        all_branch_expense_total = 0
        for num in range(len(headerInfo['branches'])):
            expenses, complete_total_expense = CustomExpenseAdmin.getExpenses(headerInfo['startDate'], headerInfo['endDate'], expenseTypes, headerInfo['branches'][num])
            all_branch_expense_total += float(complete_total_expense.translate({ord(i): None for i in ', '}))
            new_body_top = CustomExpenseAdmin.addTable(p, expenses, new_body_top, "Expenses - " + headerInfo['branches'][num], constant_body_top, headerInfo, "weekly")

        p = CustomExpenseAdmin.addSummary(p, complete_total_sales, all_branch_expense_total, constant_body_top, headerInfo)

        response = CustomExpenseAdmin.addPageToResponse(p, buffer, response)
        
        return response
    expense_weekly_report.short_description = "Generate Weekly Report"


    def getResponse():
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="weekly_report.pdf"'
        filename = "weekly_report.pdf"
        return response
    
    def getPage():
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.setPageSize(A4)
        return p, buffer

    def getHeaderInfo(queryset):
        headerInfo = {}
        headerInfo['startDate'] = queryset.order_by('date')[0].date
        headerInfo['endDate'] = queryset.order_by('-date')[0].date

        branches = []
        manager = queryset[0].manager
        for branch in Branches.objects.filter(manager=manager):
            if branch.location == "BTS MAUBAN":
                continue
            branches.append(branch.location)
        # for expense in queryset:
        #     branch_name = expense.branch.location
        #     if not branch_name in branches:
        #         branches.append(branch_name)

        headerInfo['branches'] =  branches

        return headerInfo
    
    def addHeader(p, headerInfo):
        p.setFont('Times-Bold', 10)
        top_loc = 820

        p.drawString(25, top_loc, "Report Type: Weekly")
        p.drawString(25, top_loc - 20, "Start Date: " + headerInfo['startDate'].strftime("%B %d %Y"))
        p.drawString(25, top_loc - 40, "End Date: " + headerInfo['endDate'].strftime("%B %d %Y"))
        p.drawString(25, top_loc - 60, "Branches: " + ' | '.join(headerInfo['branches']))
        return p

    def getSales(startDate, endDate, branches):
        sale_objects = Sales.objects.filter(date__range=[startDate, endDate])
        table, complete_total_sales = CustomExpenseAdmin.getTable(startDate, endDate, sale_objects, branches, "sale", None)
        return table, complete_total_sales

    def getExpenses(startDate, endDate, expenseTypes, expense_branch_name):
        expense_objects = Expenses.objects.filter(date__range=[startDate, endDate])
        table, complete_total_expenses = CustomExpenseAdmin.getTable(startDate, endDate, expense_objects, expenseTypes, "expense", expense_branch_name)
        return table, complete_total_expenses

    def getTable(startDate, endDate, objects, iterable, tableType, expense_branch_name):
        if tableType == "sale":
            heading = "Branch"
        elif tableType == "expense":
            heading = "Type"

        days = []
        for num in range((endDate - startDate).days + 1):
            days.append((startDate + datetime.timedelta(days=num)))

        heading = [heading]
        for day in days:
            heading.append(day.strftime("%b %d"))
        heading.append('Row Total')
        table = [
            heading
        ]

        daily_total = []
        for date in days:
            daily_total.append(0)

        table, complete_total = CustomExpenseAdmin.getTableContents(table, objects, iterable, days, daily_total, tableType, expense_branch_name)

        return table, complete_total

    def getTableContents(table, objects, iterable, days, daily_total, tableType, expense_branch_name):        
        for i in iterable:
            if tableType == "sale":
                i_object = objects.filter(branch__location=i)
            elif tableType == "expense":
                i_object = objects.filter(branch__location=expense_branch_name).filter(type_of_expense__name=i)

            daily_total_index = -1            
            table_row = [i]
            i_weekly_sale_total = 0
            for date in days:
                daily_total_index += 1
                try:
                    if tableType == "sale":
                        i_value = i_object.filter(date=date).get().gross_sales
                    elif tableType == "expense":
                        i_value = i_object.filter(date=date).get().amount

                except:
                    i_value = 0
                table_row.append('{:,.2f}'.format(i_value).replace(',', ', '))
                i_weekly_sale_total += i_value

                daily_total[daily_total_index] += i_value

            table_row.append('{:,.2f}'.format(i_weekly_sale_total).replace(',', ', '))
            table.append(table_row)

            formatted_daily_total = ['Row Total']
            all_branch_total = 0
            for total in daily_total:
                all_branch_total += total
                formatted_daily_total.append('{:,.2f}'.format(total).replace(',', ', '))
            formatted_daily_total.append('{:,.2f}'.format(all_branch_total).replace(',', ', '))

        table.append(formatted_daily_total)
        return table, '{:,.2f}'.format(all_branch_total).replace(',', ', ')
    
    def addTable(p, sales, body_top, title, constant_body_top, headerInfo, weeklyOrMonthly):
        table_bottom = body_top - (len(sales) + 1)*19
        if table_bottom < 100:
            p.showPage()
            p.setFont('Times-Bold', 10)
            if weeklyOrMonthly == "monthly":
                p = CustomExpenseAdmin.addHeaderMonthly(p, headerInfo)
            else:
                p = CustomExpenseAdmin.addHeader(p, headerInfo)
            table_bottom = constant_body_top - (len(sales) + 1)*19
            body_top = constant_body_top
        p.drawString(25, body_top - 20, title)
        table = Table(sales)
        width, height = A4
        table.setStyle(TableStyle(
            [
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ]
        ))
        table.wrapOn(p, width, height)
        table.drawOn(p, 25, table_bottom)
        return table_bottom - 20
    
    def addSummary(p, complete_total_sales, all_branch_expense_total, constant_body_top, headerInfo):
        p.showPage()
        p.setFont('Times-Bold', 12)
        p = CustomExpenseAdmin.addHeader(p, headerInfo)
        p.drawString(20, constant_body_top - 20, "Weekly Summary:")
        p.drawString(30, constant_body_top - 40, "Total Sales: " + complete_total_sales)
        p.drawString(30, constant_body_top - 60, "Total Expenses: " + '{:,.2f}'.format(all_branch_expense_total).replace(',', ', '))
        salesMinusExpense = float(complete_total_sales.translate({ord(i): None for i in ', '})) - all_branch_expense_total
        salesMinusExpenseFormatted = '{:,.2f}'.format(salesMinusExpense).replace(',', ', ')
        p.drawString(20, constant_body_top - 80, "Total Sales - Total Expenses: " + salesMinusExpenseFormatted)
        return p


    def addPageToResponse(p, buffer, response):
        p.save()
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        return response


    def expense_monthly_report(self, request, queryset):
        # the queryset itself is not necessarily the most important
        # the queryset must just include the right date

        if not request.user.roles.is_manager:
            raise RuntimeError("User must be a manager to perform this action")
        
        constant_body_top = 770

        response = CustomExpenseAdmin.getResponse()
        p, buffer = CustomExpenseAdmin.getPage()
        headerInfo = CustomExpenseAdmin.getHeaderInfoMonthly(queryset)

        p = CustomExpenseAdmin.addHeaderMonthly(p, headerInfo)

        sales, complete_total_sales, per_branch_total = CustomExpenseAdmin.getSalesMonthly(headerInfo['date'], headerInfo['branches'], request.user)
        new_body_top = CustomExpenseAdmin.addTable(p, sales, constant_body_top, "Sales", constant_body_top, headerInfo, "monthly")

        expenses, complete_total_expenses, _ = CustomExpenseAdmin.getExpensesMonthly(headerInfo['date'], headerInfo['branches'], request.user)
        new_body_top = CustomExpenseAdmin.addTable(p, expenses, new_body_top, "Expenses", constant_body_top, headerInfo, "monthly")

        purchases, complete_total_purchases, _ = CustomExpenseAdmin.getPurchasesMonthly(headerInfo['date'], headerInfo['branches'], request.user, per_branch_total)
        new_body_top = CustomExpenseAdmin.addTable(p, purchases, new_body_top, "Purchases", constant_body_top, headerInfo, "monthly")
        
        p = CustomExpenseAdmin.addSummaryMonthly(p, complete_total_sales, complete_total_expenses, complete_total_purchases, headerInfo, constant_body_top)

        response = CustomExpenseAdmin.addPageToResponse(p, buffer, response)
        
        return response
    expense_monthly_report.short_description = "Generate Monthly Report"


    def getHeaderInfoMonthly(queryset):
        headerInfo = {}
        headerInfo['date'] = queryset.order_by('-date')[0].date

        branches = []
        manager = queryset[0].manager
        for branch in Branches.objects.filter(manager=manager):
            if branch.location == "BTS MAUBAN":
                continue
            branches.append(branch.location)
        headerInfo['branches'] =  branches

        return headerInfo


    def addHeaderMonthly(p, headerInfo):
        p.setFont('Times-Bold', 10)
        top_loc = 820

        p.drawString(25, top_loc, "Report Type: Monthly")
        p.drawString(25, top_loc - 20, "Date: " + headerInfo['date'].strftime("%B %Y"))
        p.drawString(25, top_loc - 40, "Branches: " + ' | '.join(headerInfo['branches']))
        return p

    def getSalesMonthly(date, branches, user):
        _, endDay = calendar.monthrange(date.year, date.month)
        startDate = date.replace(day=1)
        endDate = date.replace(day=endDay)
        sale_objects = Sales.objects.filter(date__range=[startDate, endDate])
        table, complete_total_sales, per_branch_total = CustomExpenseAdmin.getTableMonthly(startDate, endDate, branches, sale_objects, "sale", user, _)
        return table, complete_total_sales, per_branch_total

    def getExpensesMonthly(date, branches, user):
        _, endDay = calendar.monthrange(date.year, date.month)
        startDate = date.replace(day=1)
        endDate = date.replace(day=endDay)
        expense_objects = Expenses.objects.filter(date__range=[startDate, endDate])
        table, complete_total_expenses, _ = CustomExpenseAdmin.getTableMonthly(startDate, endDate, branches, expense_objects, "expense", user, _)
        return table, complete_total_expenses, _

    def getPurchasesMonthly(date, branches, user, per_branch_total):
        _, endDay = calendar.monthrange(date.year, date.month)
        startDate = date.replace(day=1)
        endDate = date.replace(day=endDay)
        purchase_objects = Purchases.objects.filter(date__range=[startDate, endDate])
        table, complete_total_purchases, _ = CustomExpenseAdmin.getTableMonthly(startDate, endDate, branches, purchase_objects, "purchase", user, per_branch_total)
        return table, complete_total_purchases, _

    def getTableMonthly(startDate, endDate, branches, objects, tableType, user, per_branch_total):
        days = []
        for num in range((endDate - startDate).days + 1):
            days.append((startDate + datetime.timedelta(days=num)))

        types = []
        for t in Expense_Types.objects.filter(manager=user).filter(is_active=True):
            types.append(t.name)

        days_purchased = []
        for p in objects:
            days_purchased.append(p.date)
        days_purchased = list(set(days_purchased))
        days_purchased.sort()

        if tableType == "sale":
            column1Title = "Date"
            rows = days
        elif tableType == "expense":
            column1Title = "Type"
            rows = types
        elif tableType == "purchase":
            column1Title = "Date"
            rows = days_purchased

        heading = [column1Title]
        branch_total = []
        for branch in branches:
            heading.append(branch)
            branch_total.append(0)
        heading.append('Row Total')

        table = [
            heading
        ]
        
        table, complete_total, per_branch_total = CustomExpenseAdmin.getTableContentsMonthly(table, objects, rows, branch_total, branches, tableType, per_branch_total, startDate, endDate)

        return table, complete_total, per_branch_total

    def getTableContentsMonthly(table, objects, rows, daily_total, branches, tableType, per_branch_total, startDate, endDate):
        if tableType == "sale":
            per_branch_total = {}
            for branch in branches:
                per_branch_total[branch] = 0

        if tableType == "expense":
            salary_row = []
            salary_total = 0
            for branch in branches:
                branch_salary = 0
                bimonthly_objects = Bimonthly_In.objects.filter(staff__roles__branches__location=branch)
                bimonthly_objects = bimonthly_objects.filter(date__range=[startDate, endDate])
                for b in bimonthly_objects:
                    branch_salary += b.pay_reg
                    branch_salary += b.pay_hd
                    branch_salary += b.pay_shd
                salary_total += branch_salary
                salary_row.append(branch_salary)
            salary_row.append(salary_total)

        once = True
        for i in rows:
            branch_total_index = -1
            i_weekly_total = 0

            if tableType == "sale":            
                table_row = [i.strftime("%b %d")]
                i_object = objects.filter(date=i)
            elif tableType == "expense":            
                table_row = [i]
                i_object = objects.filter(type_of_expense__name=i)
            elif tableType == "purchase":            
                table_row = [i.strftime("%b %d")]
                i_object = objects.filter(date=i)

            for branch in branches:
                branch_total_index += 1
                try:
                    if tableType == "sale":
                        i_value = i_object.filter(branch__location=branch).get().gross_sales
                    elif tableType == "expense":
                        i_value = 0
                        for expense in i_object.filter(branch__location=branch):
                            i_value += expense.amount
                    elif tableType == "purchase":
                        i_value = 0
                        for purchase in i_object.filter(branch__location=branch):
                            i_value += purchase.invoice_worth
                except:
                    i_value = 0

                table_row.append('{:,.2f}'.format(i_value).replace(',', ', '))
                i_weekly_total += i_value

                daily_total[branch_total_index] += i_value
                if tableType=="sale":
                    per_branch_total[branch] += i_value

            if tableType == "expense" and once:
                for i in range(len(branches)):
                    daily_total[i] += salary_row[i]
            once = False

            table_row.append('{:,.2f}'.format(i_weekly_total).replace(',', ', '))
            table.append(table_row)

            formatted_daily_total = ['Row Total']
            all_branch_total = 0
            for total in daily_total:
                all_branch_total += total
                formatted_daily_total.append('{:,.2f}'.format(total).replace(',', ', '))
            formatted_daily_total.append('{:,.2f}'.format(all_branch_total).replace(',', ', '))

            if tableType == "purchase":
                percentages = ["Percent"] 
                percent_total = 0
                for index in range(len(branches)):
                    try:
                        percent = daily_total[index]/per_branch_total[branches[index]]
                    except ZeroDivisionError:
                        percent = 0
                    percent_total += percent
                    percentages.append("{0:.2%}".format(percent))
                percentages.append("{0:.2%}".format(percent_total/len(branches)))

        if tableType == "expense":
            formatted_salary = ["Payroll: Salary"]
            for s in salary_row:
                formatted_salary.append('{:,.2f}'.format(s).replace(',', ', '))
            table.append(formatted_salary)
        table.append(formatted_daily_total)
        if tableType == "purchase":
            table.append(percentages)   
        return table, '{:,.2f}'.format(all_branch_total).replace(',', ', '), per_branch_total

    def addSummaryMonthly(p, complete_total_sales, complete_total_expenses, complete_total_purchases, headerInfo, constant_body_top):
        p.showPage()
        p.setFont('Times-Bold', 12)
        p = CustomExpenseAdmin.addHeaderMonthly(p, headerInfo)
        p.drawString(20, constant_body_top - 20, "Monthly Summary:")
        p.drawString(30, constant_body_top - 40, "Total Sales: " + complete_total_sales)
        p.drawString(30, constant_body_top - 60, "Total Expenses: " + complete_total_expenses)
        p.drawString(30, constant_body_top - 80, "Total Purchases: " + complete_total_purchases)
        complete_total_sales = complete_total_sales.replace(" ", "")
        complete_total_sales = complete_total_sales.replace(",", "")
        complete_total_expenses = complete_total_expenses.replace(" ", "")
        complete_total_expenses = complete_total_expenses.replace(",", "")
        complete_total_purchases = complete_total_purchases.replace(" ", "")
        complete_total_purchases = complete_total_purchases.replace(",", "")
        profit = float(complete_total_sales) -  float(complete_total_expenses) - float(complete_total_purchases)
        formatted_profit = '{:,.2f}'.format(profit).replace(',', ', ')
        p.drawString(30, constant_body_top - 100, "Total Profit: " + formatted_profit)
        # salesMinusExpense = float(complete_total_sales.translate({ord(i): None for i in ', '})) - all_branch_expense_total
        # salesMinusExpenseFormatted = '{:,.2f}'.format(salesMinusExpense).replace(',', ', ')
        # p.drawString(20, constant_body_top - 80, "Total Sales - Total Expenses: " + salesMinusExpenseFormatted)
        return p  


@admin.register(Bank_Status)
class CustomBankStatusAdmin(TotalsumAdmin):
    change_list_template = "admin/finance/change_list_bank_status.html"
    totalsum_list = ('deposit', 'withdraw')
    ordering = ['bank', '-date']
    # ordering = ['-date', 'bank']
    list_display = ['date', 'bank', 'total', 'update', 'error', 'deposit', 'withdraw', 'remark']
    list_filter = [BankFilter,
                   ('date', DateRangeFilter),
                   ('date', DateFieldListFilter),
    ]
    list_per_page = 10
    readonly_fields = ('deposit', 'withdraw', 'total', 'error')
    fields = ('deposit', 'withdraw', 'total', 'date', 'update', 'error', 'remark', 'check', 'online', 'image')


    def get_queryset(self, request):
        user = request.user
        if user.roles.is_manager:
            return user.bank_statuses


    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        user = request.user
        disabled_fields = set()  # type: Set[str]

        if not user.is_superuser:
            disabled_fields |= {
                'manager',
                'sale_report',
                'expense_report',
                'bank',
                'deposit',
                'withdraw',
            }



        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form

    def get_total(self, request):
        user = request.user
        if user.roles.is_manager:
            banks = user.banks
            m_bank_status = user.bank_statuses
        else:
            banks = user.roles.manager.banks
            m_bank_status = user.roles.manager.bank_statuses
        total = 0
        for b in banks.all():
            filtered_bank_status =  m_bank_status.filter(bank=b)
            if filtered_bank_status:
                latest = filtered_bank_status.order_by('-date').first()
                if latest.update:
                    total += latest.update
                else:
                    total += latest.total()
        return str(total)

    def changelist_view(self, request, extra_context=None):
        my_context = {
            'total': self.get_total(request),
        }
        return super(CustomBankStatusAdmin, self).changelist_view(request,
            extra_context=my_context)