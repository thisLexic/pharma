from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

from django.contrib import admin
from django.utils import timezone
from django.contrib.admin import SimpleListFilter, DateFieldListFilter
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import redirect
from django.db.models import Sum
from django.http import HttpResponse

from io import BytesIO
from reportlab.pdfgen import canvas
from rangefilter.filter import DateRangeFilter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from simple_history.admin import SimpleHistoryAdmin

from .models import Roles, Hours_In, Bimonthly_In, Government_Benefits, Loans, Branch_Attendance, Companies
from location.models import Branches, Current_Branch
from adminApiModel.utils import FilterBranchDropDown, ManyBranchFilter, FilterBranchSpecificStaffDropDown, TotalsumAdmin, \
                                HistoryFilterBranchSpecificStaffDropDown


admin.site.unregister(get_user_model())

def get_name(self):
    return '{} {}'.format(self.first_name, self.last_name)

get_user_model().add_to_class("__str__", get_name)


@admin.register(get_user_model())
class CustomUserAdmin(UserAdmin):
    ordering = ['first_name', 'last_name', '-is_staff', '-is_active']
    list_display = ['first_name', 'last_name', 'branch', 'is_staff', 'is_active']
    list_filter = ['groups', 'is_staff', 'is_active']
    readonly_fields = [
        'date_joined',
    ]
    # add_fieldsets = (
    #     (None, {
    #         'classes': ('wide',),
    #         'fields': ('first_name', 'last_name', 'username', 'password1', 'password2', ),
    #     }),
    # )


    def branch(self, obj):
        branches = ""
        for b in obj.roles.branches.order_by('location'):
            branches += b.location + " | "
        return branches


    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        user = request.user
        disabled_fields = set()  # type: Set[str]

        if user.is_superuser:
            return form

        if not user.is_superuser:
            disabled_fields |= {
                'is_superuser',
                'user_permissions',
                'last_login'
            }

        if obj:
            if not user.roles.is_manager:
                disabled_fields |= {
                    'username',
                    'first_name',
                    'last_name',
                    'email',
                    'is_active',
                    'is_staff',
                    'groups',
                    'last_login',
                    'date_joined',
                }

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form


    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return self.fieldsets
        elif request.user.roles.is_manager and obj:
            return [(None, {'fields': ('username','password', 'first_name', 'last_name', \
                                       'email', 'is_active', 'is_staff', 'groups', 'last_login', 'date_joined')}),]
        elif request.user.roles.is_manager and not obj:
            return [(None, {'fields': ('username','password1', 'password2', 'first_name', 'last_name', \
                                       'email', 'is_active', 'is_staff', 'groups', 'last_login', 'date_joined')}),]
        elif request.user.roles.is_assistant and obj:
            return [(None, {'fields': ('password',)}),]
        elif request.user.roles.is_assistant and not obj:
            return [(None, {'fields': ('username','password1', 'password2', 'first_name', 'last_name',)}),]
        else:
            return [(None, {'fields': ('',)}),]

    def get_queryset(self, request):
        user = request.user

        if user.is_superuser:
            return super().get_queryset(request)
        elif user.roles.is_manager:
            return get_user_model().objects.filter(roles__manager=user)
        elif user.roles.is_assistant:
            return get_user_model().objects.filter(roles__manager=user.roles.manager
                                          ).filter(roles__is_manager=False)
        else:
            return None

    def save_model(self, request, obj, form, change):
        if request.user.is_superuser or request.user.roles.is_assistant or request.user.roles.is_manager:
            if not change:
                obj.is_staff = True
            if obj.first_name == '':
                obj.first_name = 'Not Set'
            super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        if not change:
            if request.user.is_superuser:
                Roles(user=form.instance,
                        manager=request.user,
                        is_manager=True
                        ).save()
                Current_Branch(user=form.instance,
                               manager=request.user,
                              ).save()
            elif request.user.roles.is_manager:
                Roles(user=form.instance,
                        manager=request.user,
                        is_retailer=True
                        ).save()
                Current_Branch(user=form.instance,
                               manager=request.user,
                              ).save()
                Government_Benefits(manager=request.user,
                        staff = form.instance,
                        institute = 'SSS'
                    ).save()
                Government_Benefits(manager=request.user,
                        staff = form.instance,
                        institute = 'PH'
                    ).save()
                Government_Benefits(manager=request.user,
                        staff = form.instance,
                        institute = 'PI'
                    ).save()
            elif request.user.roles.is_assistant:
                Roles(user=form.instance,
                        manager=request.user.roles.manager,
                        is_retailer=True
                        ).save()
                Current_Branch(user=form.instance,
                               manager=request.user.roles.manager,
                              ).save()
                Government_Benefits(manager=request.user.roles.manager,
                        staff = form.instance,
                        institute = 'SSS'
                    ).save()
                Government_Benefits(manager=request.user.roles.manager,
                        staff = form.instance,
                        institute = 'PH'
                    ).save()
                Government_Benefits(manager=request.user.roles.manager,
                        staff = form.instance,
                        institute = 'PI'
                    ).save()
        super(CustomUserAdmin, self
             ).save_related(request, form, formsets, change)


    def response_add(self, request, obj, post_url_continue=None):
        if request.user.roles.is_manager:
            return redirect('/auth/user/' + str(obj.id) + '/change/')
        else:
            return redirect('/auth/')


@admin.register(Roles)
class RoleAdmin(FilterBranchDropDown):
    ordering = ['-is_assistant', '-is_retailer', 'user']
    list_display = ['user', 'branch']
    list_filter = [
                    ManyBranchFilter,
                    'is_assistant',
                    'is_retailer',
    ]

    def branch(self, obj):
        branches = ""
        for b in obj.branches.order_by('location'):
            branches += b.location + " | "
        return branches


    def get_queryset(self, request):
        user = request.user

        if user.is_superuser:
            return super().get_queryset(request)
        elif user.roles.is_manager:
            return user.staff_roles
        elif user.roles.is_assistant:
            return user.roles.manager.staff_roles


    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        user = request.user
        disabled_fields = set()  # type: Set[str]

        if not user.is_superuser:
            disabled_fields |= {
                'is_manager',
                'user',
                'manager',
            }

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form


    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return [(None, {'fields': ('user', 'manager', \
                'is_assistant', 'is_manager')}),]
        elif request.user.roles.is_manager:
            return [(None, {'fields': ('staff_id', 'hrly_rate', 'hrly_allow', 'company', 'is_retailer', 'days', 'branches', \
                'is_assistant', 'sale_days', 'sale_branches', 'sale_can_validate', 'sale_change_deposit', \
                'expense_days', 'expense_branches', 'expense_can_validate', \
                'purchase_days', 'purchase_branches', 'purchase_can_validate',
                'hours_in_days', 'hours_in_branches',)}),]
        elif request.user.roles.is_assistant:
            return [(None, {'fields': ('branches',)}),]


@admin.register(Hours_In)
class HoursInAdmin(HistoryFilterBranchSpecificStaffDropDown):
    ordering = ['-date', 'staff']
    list_display = ['date', 'staff', 'branch', 'hours', 'day_type']
    search_fields = ['staff__first_name', 'staff__last_name']

    def branch(self, obj):
        branches = ""
        for b in obj.staff.roles.branches.order_by('location'):
            branches += b.location + " | "
        return branches

    def get_queryset(self, request):
        user = request.user

        if user.roles.is_manager:
            return user.staff_hours_in
        elif user.roles.is_assistant:
            days = user.roles.hours_in_days
            branches = user.roles.hours_in_branches.all()
            if days and branches:
                return user.roles.manager.staff_hours_in.filter(date__gte=timezone.now() - timedelta(days=days)
                       ).filter(staff__roles__branches__in=branches).distinct()
            else:
                raise RuntimeError("User is assistant but roles improperly configured")
        else:
            days = user.roles.days
            return user.roles.manager.staff_hours_in.filter(date__gte=timezone.now() - timedelta(days=days)
                       ).filter(staff__roles__branches__in=user.roles.branches.all()).distinct()


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
        if obj:
            if obj.date < (datetime.today() - timedelta(days=20)).date():
                raise RuntimeError("Cannot edit due to date")
        if request.user.roles.is_manager:
            obj.manager = request.user
        elif request.user.roles.is_retailer or request.user.roles.is_assistant:
            obj.manager = request.user.roles.manager
        super().save_model(request, obj, form, change)



class BimonthlyBranchFilter(SimpleListFilter):
    title = 'branch'
    parameter_name = 'branch'

    def lookups(self, request, model_admin):
        if request.user.roles.is_manager:
            branches = request.user.branches.all()
        else:
            branches = request.user.roles.manager.branches.all()
        # print([(b.id, b.location) for b in branches])
        return [(b.id, b.location) for b in branches]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(staff__roles__branches__id=self.value())
        return queryset


@admin.register(Bimonthly_In)
class BimonthlyInAdmin(TotalsumAdmin, FilterBranchSpecificStaffDropDown):
    change_list_template = "admin/utils/change_list.html"
    totalsum_list = ('pay_tot', 'pay_reg', 'pay_hd', 'pay_shd')
    ordering = ['-date', 'staff']
    list_display = ['date', 'staff', 'branch', 'day', 'pay_sss', 'pay_ph', 'pay_pi', 'pay_tot', 'extr_alw', 'hrs_reg', 'pay_reg', 'hrs_hd', 'pay_hd', 'pay_shd', 'hrs_shd', 'pay_vl', 'hrs_vl', 'pay_sl', 'hrs_sl',
              'bene_a', 'bene_a_desc', 'bene_b', 'bene_b_desc', 'bene_c', 'bene_c_desc', 'bene_d', 'bene_d_desc',
              'ded_a', 'ded_a_desc', 'ded_b', 'ded_b_desc', 'ded_c', 'ded_c_desc', 'ded_d', 'ded_d_desc',
              'giv_a', 'giv_a_desc', 'giv_b', 'giv_b_desc', 'giv_c', 'giv_c_desc', 'giv_d', 'giv_d_desc']
    fields = ['date', 'staff', 'day', 'pay_sss', 'pay_ph', 'pay_pi', 'pay_tot', 'extr_alw', 'hrs_reg', 'pay_reg', 'hrs_hd', 'pay_hd', 'pay_shd', 'hrs_shd', 'pay_vl', 'hrs_vl', 'pay_sl', 'hrs_sl',
              'bene_a', 'bene_a_desc', 'bene_b', 'bene_b_desc', 'bene_c', 'bene_c_desc', 'bene_d', 'bene_d_desc',
              'ded_a', 'ded_a_desc', 'ded_b', 'ded_b_desc', 'ded_c', 'ded_c_desc', 'ded_d', 'ded_d_desc',
              'giv_a', 'giv_a_desc', 'giv_b', 'giv_b_desc', 'giv_c', 'giv_c_desc', 'giv_d', 'giv_d_desc']
    readonly_fields = ['pay_tot', 'extr_alw', 'hrs_reg', 'pay_reg', 'pay_hd', 'hrs_hd', 'pay_shd', 'hrs_shd', 'pay_vl', 'hrs_vl', 'pay_sl', 'hrs_sl']
    actions = ['export', 'anull', 'bnull', 'cnull', 'automate_entries']
    list_filter = [
                   BimonthlyBranchFilter,
                   ('date', DateRangeFilter),
                   ('date', DateFieldListFilter),
    ]


    def branch(self, obj):
        branches = ""
        for b in obj.staff.roles.branches.order_by('location'):
            branches += b.location + " | "
        return branches


    def get_queryset(self, request):
        user = request.user

        if user.roles.is_manager:
            return user.staff_bimonthly_in
        else:
            personal_bimonthly_in = user.roles.manager.staff_bimonthly_in.filter(staff=user)
            most_recent = personal_bimonthly_in.order_by('-date').first()
            return personal_bimonthly_in.filter(date=most_recent.date)


    def save_model(self, request, obj, form, change):
        if obj:
            if obj.date < (datetime.today() - timedelta(days=20)).date():
                raise RuntimeError("Cannot edit due to date")
        if request.user.roles.is_manager:
            obj.manager = request.user
        elif request.user.roles.is_retailer or request.user.roles.is_assistant:
            obj.manager = request.user.roles.manager

        if obj.day == '8':
            obj.date = obj.date.replace(day=8)
        else:
            obj.date = obj.date.replace(day=23)

        obj.pay_tot = 0

        # pay based on hours worked and if day is a holiday
        hours_in = Hours_In.get_dailies(obj.staff, obj.day, obj.date)

        hrly_rate = obj.staff.roles.hrly_rate

        obj.hrs_reg = BimonthlyInAdmin.turn_zero(hours_in.filter(day_type='REG').aggregate(total=Sum('hours'))['total'])
        obj.pay_reg = obj.hrs_reg * obj.staff.roles.hrly_rate
        obj.pay_tot += obj.pay_reg

        hd_db = hours_in.filter(day_type='HD')
        obj.hrs_hd = BimonthlyInAdmin.turn_zero(hd_db.aggregate(total=Sum('hours'))['total'])
        obj.pay_hd = obj.hrs_hd * hrly_rate * 2 + hrly_rate * 8 * hd_db.filter(hours=0).count()
        obj.pay_tot += obj.pay_hd

        shd_db = hours_in.filter(day_type='SHD')
        obj.hrs_shd = BimonthlyInAdmin.turn_zero(shd_db.aggregate(total=Sum('hours'))['total'])
        obj.pay_shd = obj.hrs_shd * hrly_rate * 1.3 # + hrly_rate * 8 * shd_db.filter(hours=0).count()
        obj.pay_tot += obj.pay_shd

        vl_db = hours_in.filter(day_type='VL')
        obj.hrs_vl = len(vl_db) * 8
        obj.pay_vl = obj.hrs_vl * hrly_rate
        obj.pay_tot += obj.pay_vl

        sl_db = hours_in.filter(day_type='SL')
        obj.hrs_sl = len(sl_db) * 8
        obj.pay_sl = obj.hrs_sl * hrly_rate
        obj.pay_tot += obj.pay_sl

        # old extra allowance pay
        # obj.extr_alw = obj.staff.roles.hrly_allow * obj.hrs_reg
        # obj.extr_alw += obj.hrs_hd * obj.staff.roles.hrly_allow * 2 + obj.staff.roles.hrly_allow * 8 * hd_db.filter(hours=0).count()
        # obj.extr_alw += obj.hrs_shd * obj.staff.roles.hrly_allow * 1.3 + obj.staff.roles.hrly_allow * 8 * shd_db.filter(hours=0).count()
        # obj.pay_tot += obj.extr_alw

        # new extra allowance pay
        obj.extr_alw = obj.staff.roles.hrly_allow * obj.hrs_reg
        obj.extr_alw += obj.hrs_hd * obj.staff.roles.hrly_allow
        obj.extr_alw += obj.hrs_shd * obj.staff.roles.hrly_allow
        obj.pay_tot += obj.extr_alw

        # benefits and deductions
        benefits = [obj.bene_a, obj.bene_b, obj.bene_c, obj.bene_d]
        deductions = [obj.ded_a, obj.ded_b, obj.ded_c, obj.ded_d]
        for b in benefits:
            if not b:
                continue
            obj.pay_tot += b
        for d in deductions:
            if not d:
                continue
            obj.pay_tot -= d

        # government loans and sss, pi, ph
        if obj.pay_sss:
            BimonthlyInAdmin.ded_gov(obj, change, "SSS")

        if obj.pay_pi:
            BimonthlyInAdmin.ded_gov(obj, change, "PI")

        if obj.pay_ph:
            BimonthlyInAdmin.ded_gov(obj, change, "PH")


        super().save_model(request, obj, form, change)

    def turn_zero(number):
        if not number:
            return 0
        return number

    def ded_gov(obj, change, institute):
        gov_ben = obj.staff.government_benefits.get(institute=institute)
        obj.pay_tot -= gov_ben.staff_cont
        for g in gov_ben.loans.filter(is_valid=True).filter(is_paid=False):
            obj.pay_tot -= g.mnth_pay
            if not change:
                g.total_paid += g.mnth_pay
                g.save()

    def anull(self, request, queryset):
        pass
    anull.short_description = "======="

    def bnull(self, request, queryset):
        pass
    bnull.short_description = "======="

    def cnull(self, request, queryset):
        pass
    cnull.short_description = "======="

    def export(self, request, queryset):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="bimonthly-payroll.pdf"'

        filename = "bimonthly-payroll.pdf"

        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.setPageSize(A4)

        nextPage = False
        for bimonthly_in in queryset:
            if nextPage:
                loc = 100
                top_loc = 400
            else:
                p.setFont('Times-Bold', 10)
                loc = 520
                top_loc = 820

            year = bimonthly_in.date.year
            month = bimonthly_in.date.month
            if bimonthly_in.day == "8":
                if month != 1:
                    date_str = datetime(year, month-1, 22)
                else:
                    date_str = datetime(year-1, 12, 22)
                date_end = datetime(year, month, 6)
            else:
                date_str = datetime(year, month, 7)
                date_end = datetime(year, month, 21)
            date = date_str.strftime("%B %d %Y") + " - " + date_end.strftime("%B %d %Y")


            p.drawString(10, top_loc, "Pay Slip " + date)
            p.drawString(10, top_loc - 20, str(bimonthly_in.staff.roles.company))
            # p.setFont('Times-Bold', 8)
            # p.drawString(10, top_loc - 40, date)
            p.setFont('Times-Bold', 10)
            p.drawString(10, top_loc - 40, str(bimonthly_in.staff))

            data_in = [
                ["Payment", "Amt", "Days", "Deduct", "Stf Cnt", "Mngt Cnt", "Alrdy Given", "Amt"],
            ]

            #  Payment
            total_in = [0]
            spaces_in = [0]
            BimonthlyInAdmin.add_not_null_zero(data_in, "Regular Pay", bimonthly_in.pay_reg, total_in, spaces_in=spaces_in, hours=bimonthly_in.hrs_reg)
            BimonthlyInAdmin.add_not_null_zero(data_in, "Holiday Pay", bimonthly_in.pay_hd, total_in, spaces_in=spaces_in, hours=bimonthly_in.hrs_hd)
            BimonthlyInAdmin.add_not_null_zero(data_in, "Special Holiday Pay", bimonthly_in.pay_shd, total_in, spaces_in=spaces_in, hours=bimonthly_in.hrs_shd)
            BimonthlyInAdmin.add_not_null_zero(data_in, "Extra Allowance", bimonthly_in.extr_alw, total_in, spaces_in=spaces_in)
            BimonthlyInAdmin.add_not_null_zero(data_in, "Vacation Leave", bimonthly_in.pay_vl, total_in, spaces_in=spaces_in, hours=bimonthly_in.hrs_vl)
            BimonthlyInAdmin.add_not_null_zero(data_in, "Sick Leave", bimonthly_in.pay_sl, total_in, spaces_in=spaces_in, hours=bimonthly_in.hrs_sl)
            BimonthlyInAdmin.add_not_null_zero(data_in, bimonthly_in.bene_a_desc, bimonthly_in.bene_a, total_in, spaces_in=spaces_in)
            BimonthlyInAdmin.add_not_null_zero(data_in, bimonthly_in.bene_b_desc, bimonthly_in.bene_b, total_in, spaces_in=spaces_in)
            BimonthlyInAdmin.add_not_null_zero(data_in, bimonthly_in.bene_c_desc, bimonthly_in.bene_c, total_in, spaces_in=spaces_in)
            BimonthlyInAdmin.add_not_null_zero(data_in, bimonthly_in.bene_d_desc, bimonthly_in.bene_d, total_in, spaces_in=spaces_in)
            for i in range(spaces_in[0] + 1):
                data_in.append(["", ""])
            if total_in[0] != 0:
                BimonthlyInAdmin.add_not_null_zero(data_in, "Total Pay:", 0, total_in, spaces_in=spaces_in, is_total=True)
            else:
                data_in.append(["", ""])

            # Deduction
            total_out = [0]
            cur_row = [1]
            BimonthlyInAdmin.add_not_null_zero(data_in, bimonthly_in.ded_a_desc, bimonthly_in.ded_a, total_out, i=cur_row, pay=False)
            BimonthlyInAdmin.add_not_null_zero(data_in, bimonthly_in.ded_b_desc, bimonthly_in.ded_b, total_out, i=cur_row, pay=False)
            BimonthlyInAdmin.add_not_null_zero(data_in, bimonthly_in.ded_c_desc, bimonthly_in.ded_c, total_out, i=cur_row, pay=False)
            BimonthlyInAdmin.add_not_null_zero(data_in, bimonthly_in.ded_d_desc, bimonthly_in.ded_d, total_out, i=cur_row, pay=False)
            for gb in bimonthly_in.staff.government_benefits.all():
                institute = gb.institute
                if institute == "SSS" and not bimonthly_in.pay_sss:
                    continue
                elif institute == "PH" and not bimonthly_in.pay_ph:
                    continue
                elif institute == "PI" and not bimonthly_in.pay_pi:
                    continue
                BimonthlyInAdmin.add_not_null_zero(data_in, institute, gb.staff_cont, total_out, i=cur_row, pay=False, v_mngr=gb.mngr_cont)
                for loan in gb.loans.filter(is_paid=False).filter(is_valid=True):
                    loan_type = loan.loan_type
                    BimonthlyInAdmin.add_not_null_zero(data_in, institute + " " + loan_type, loan.mnth_pay, total_out, i=cur_row, pay=False)

            BimonthlyInAdmin.add_not_null_zero(data_in, "Total Deduct:", 0, total_out, i=[12], pay=False, is_total=True)

            # Already Given Benefits
            total_giv = [0]
            cur_row = [1]
            BimonthlyInAdmin.add_not_null_zero(data_in, bimonthly_in.giv_a_desc, bimonthly_in.giv_a, total_giv, i=cur_row, pay=False, is_giv=True)
            BimonthlyInAdmin.add_not_null_zero(data_in, bimonthly_in.giv_b_desc, bimonthly_in.giv_b, total_giv, i=cur_row, pay=False, is_giv=True)
            BimonthlyInAdmin.add_not_null_zero(data_in, bimonthly_in.giv_c_desc, bimonthly_in.giv_c, total_giv, i=cur_row, pay=False, is_giv=True)
            BimonthlyInAdmin.add_not_null_zero(data_in, bimonthly_in.giv_d_desc, bimonthly_in.giv_d, total_giv, i=cur_row, pay=False, is_giv=True)

            BimonthlyInAdmin.add_not_null_zero(data_in, "Total Alrdy Gvn:", 0, total_giv, i=[12], pay=False, is_total=True, is_giv=True)


            table = Table(data_in)
            width, height = A4
            table.setStyle(TableStyle(
                [
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                ]
            ))
            table.wrapOn(p, width, height)
            table.drawOn(p, 10, loc)

            p.drawString(40, loc - 30, "Total Salary: " + str(total_in[0] - total_out[0]))
            p.drawString(40, loc - 65, "_________________________________________________")
            p.drawString(40, loc - 80, "           Printed Name over Signature           ")


            # for bimonthly_in in queryset:
            #     staff = bimonthly_in.staff
            #     if size < 20:
            #         size = 760
            #         p.showPage()

            #         p.drawString(20, 780, "First Name")
            #         p.drawString(120, 780, "Last Name")
            #         p.drawString(220, 780, "Total Salary")
            #     p.drawString(20, size+10, "---------------------------------------------------------------------------------------------------------------------------------")
            #     p.drawString(20, size, staff.first_name)
            #     p.drawString(120, size, staff.last_name)
            #     p.drawString(220, size, str(bimonthly_in.pay_tot))
            #     size -= 20
            if nextPage:
                p.showPage()
                nextPage = False
            else:
                nextPage = True
                p.drawString(0, 410, "---------------------------------------------------------------------------------------------------------------------------")

        p.save()

        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)

        return response
    export.short_description = "Export as PDF"


    def automate_entries(self, request, queryset):

        if not request.user.roles.is_manager:
            raise RuntimeError("User must be a manager to perform this action")

        for bi in queryset:
            prev_date = bi.date
            prev_year = prev_date.year
            prev_month = prev_date.month
            if prev_date.day == 8:
                new_date = date(prev_year, prev_month, 23)
                day = '23'
                pay_sss = False
                pay_pi = False
                pay_ph = False
            else:
                new_date = date(prev_year, prev_month, 8)
                day = '8'
                new_date = new_date + relativedelta(months=+1)
                pay_sss = True
                pay_pi = True
                pay_ph = True
            obj = Bimonthly_In(
                staff=bi.staff,
                manager=bi.manager,
                date=new_date,
                day=day,
                pay_sss=pay_sss,
                pay_pi=pay_pi,
                pay_ph=pay_ph,

                bene_a=bi.bene_a,
                bene_a_desc=bi.bene_a_desc,
                bene_b=bi.bene_b,
                bene_b_desc=bi.bene_b_desc,
                bene_c=bi.bene_c,
                bene_c_desc=bi.bene_c_desc,
                bene_d=bi.bene_d,
                bene_d_desc=bi.bene_d_desc,

                ded_a=bi.ded_a,
                ded_a_desc=bi.ded_a_desc,
                ded_b=bi.ded_b,
                ded_b_desc=bi.ded_b_desc,
                ded_c=bi.ded_c,
                ded_c_desc=bi.ded_c_desc,
                ded_d=bi.ded_d,
                ded_d_desc=bi.ded_d_desc,
            )
            
            
            if obj.date < (datetime.today() - timedelta(days=20)).date():
                raise RuntimeError("Cannot edit due to date. You cannot edit if it has been entered for more than 20 days.")
            elif obj.date > (datetime.today() + timedelta(days=10)).date():
                raise RuntimeError("Cannot edit due to date. Please automate entries only when the payroll is within 10 days away.")
            

            obj.pay_tot = 0

            # pay based on hours worked and if day is a holiday
            hours_in = Hours_In.get_dailies(obj.staff, obj.day, obj.date)

            hrly_rate = obj.staff.roles.hrly_rate

            obj.hrs_reg = BimonthlyInAdmin.turn_zero(hours_in.filter(day_type='REG').aggregate(total=Sum('hours'))['total'])
            obj.pay_reg = obj.hrs_reg * obj.staff.roles.hrly_rate
            obj.pay_tot += obj.pay_reg

            hd_db = hours_in.filter(day_type='HD')
            obj.hrs_hd = BimonthlyInAdmin.turn_zero(hd_db.aggregate(total=Sum('hours'))['total'])
            obj.pay_hd = obj.hrs_hd * hrly_rate * 2 + hrly_rate * 8 * hd_db.filter(hours=0).count()
            obj.pay_tot += obj.pay_hd

            shd_db = hours_in.filter(day_type='SHD')
            obj.hrs_shd = BimonthlyInAdmin.turn_zero(shd_db.aggregate(total=Sum('hours'))['total'])
            obj.pay_shd = obj.hrs_shd * hrly_rate * 1.3 # + hrly_rate * 8 * shd_db.filter(hours=0).count()
            obj.pay_tot += obj.pay_shd

            vl_db = hours_in.filter(day_type='VL')
            obj.hrs_vl = len(vl_db) * 8
            obj.pay_vl = obj.hrs_vl * hrly_rate
            obj.pay_tot += obj.pay_vl

            sl_db = hours_in.filter(day_type='SL')
            obj.hrs_sl = len(sl_db) * 8
            obj.pay_sl = obj.hrs_sl * hrly_rate
            obj.pay_tot += obj.pay_sl

            # extra allowance pay pay
            obj.extr_alw = obj.staff.roles.hrly_allow * obj.hrs_reg
            obj.extr_alw += obj.hrs_hd * obj.staff.roles.hrly_allow
            obj.extr_alw += obj.hrs_shd * obj.staff.roles.hrly_allow
            obj.pay_tot += obj.extr_alw

            # benefits and deductions
            benefits = [obj.bene_a, obj.bene_b, obj.bene_c, obj.bene_d]
            deductions = [obj.ded_a, obj.ded_b, obj.ded_c, obj.ded_d]
            for b in benefits:
                if not b:
                    continue
                obj.pay_tot += b
            for d in deductions:
                if not d:
                    continue
                obj.pay_tot -= d

            # government loans and sss, pi, ph
            if obj.pay_sss:
                BimonthlyInAdmin.ded_gov(obj, False, "SSS")

            if obj.pay_pi:
                BimonthlyInAdmin.ded_gov(obj, False, "PI")

            if obj.pay_ph:
                BimonthlyInAdmin.ded_gov(obj, False, "PH")

            obj.save()
    automate_entries.short_description = "Automate Bimonthlies"


    def add_not_null_zero(l, caption, v, t, i=0.1, spaces_in=0.1, pay=True, is_total=False, v_mngr="", is_giv=False, hours=0):
        if not v:
            if not is_total:
                if pay:
                    spaces_in[0] += 1
                return None
        if i != 0.1:
            if is_total:
                v = t[0]
            else:
                t[0] += v
            if not v:
                return None
            if is_giv:
                if len(l[i[0]]) == 3:
                    l[i[0]].append('')
                    l[i[0]].append('')
                    l[i[0]].append('')
                    l[i[0]].append('')
                elif len(l[i[0]]) == 0:
                    l[i[0]].append(['', '', '', '', '', ''])
                l[i[0]].append(caption)
                l[i[0]].append(round(v,2))
                i[0] += 1
            else:
                if len(l[i[0]]) == 2:
                    l[i[0]].append('')
                l[i[0]].append(caption)
                l[i[0]].append(round(v,2))
                l[i[0]].append(v_mngr)
                i[0] += 1
        else:
            if is_total:
                v = t[0]
            else:
                t[0] += v
            l.append([caption, round(v,2), hours/8])

    # def export(self, request, queryset):
    #     response = HttpResponse(content_type='application/pdf')
    #     response['Content-Disposition'] = 'inline; filename="bimonthly-payroll.pdf"'

    #     buffer = BytesIO()
    #     p = canvas.Canvas(buffer)


    #     size = 760

    #     p.drawString(20, 780, "First Name")
    #     p.drawString(120, 780, "Last Name")
    #     p.drawString(220, 780, "Total Salary")

    #     for bimonthly_in in queryset:
    #         staff = bimonthly_in.staff
    #         if size < 20:
    #             size = 760
    #             p.showPage()

    #             p.drawString(20, 780, "First Name")
    #             p.drawString(120, 780, "Last Name")
    #             p.drawString(220, 780, "Total Salary")
    #         p.drawString(20, size+10, "---------------------------------------------------------------------------------------------------------------------------------")
    #         p.drawString(20, size, staff.first_name)
    #         p.drawString(120, size, staff.last_name)
    #         p.drawString(220, size, str(bimonthly_in.pay_tot))
    #         size -= 20

    #     p.save()

    #     pdf = buffer.getvalue()
    #     buffer.close()
    #     response.write(pdf)

    #     return response
    # export.short_description = "Export as PDF"


@admin.register(Government_Benefits)
class GovernmentBenefitsAdmin(admin.ModelAdmin):
    ordering = ['staff', 'institute']
    list_display = ['staff', 'branch', 'institute', 'total', 'staff_cont', 'mngr_cont']
    fields = ['staff', 'institute', 'total', 'staff_cont', 'mngr_cont']
    # readonly_fields = ['staff', 'institute']
    list_filter = ['institute']


    def branch(self, obj):
        branches = ""
        for b in obj.staff.roles.branches.order_by('location'):
            branches += b.location + " | "
        return branches

    def get_queryset(self, request):
        user = request.user

        if user.roles.is_manager:
            return user.staff_government_benefits
        elif user.roles.is_assistant:
            return user.roles.manager.staff_government_benefits

    def get_readonly_fields(self, request, obj=None):
        if obj: # editing an existing object
            return self.readonly_fields + ('staff', 'institute')
        return self.readonly_fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if request.user.roles.is_manager:
            manager = request.user
        else:
            manager = request.user.roles.manager
        if db_field.name == "staff":
            kwargs["queryset"] = get_user_model().objects.filter(roles__manager=manager)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            if request.user.roles.is_manager:
                obj.manager = request.user
            else:
                obj.manager = request.user.roles.manager
        super().save_model(request, obj, form, change)


@admin.register(Loans)
class LoansAdmin(admin.ModelAdmin):
    ordering = ['-is_valid', 'is_paid']
    list_display = ['staff', 'branch', 'institute', 'loan_type', 'is_paid', 'is_valid',
                    'date_str', 'date_end',
                    'total', 'mnth_pay', 'total_paid', 'interest']
    fields = ['institute', 'loan_type', 'date_str', 'date_end',
              'total', 'mnth_pay', 'total_paid', 'interest',
              'is_paid', 'is_valid']
    

    def branch(self, obj):
        branches = ""
        for b in obj.institute.staff.roles.branches.order_by('location'):
            branches += b.location + " | "
        return branches

    def staff(self, obj):
        return str(obj.institute.staff)


    def get_queryset(self, request):
        user = request.user

        if user.roles.is_manager:
            return user.staff_government_loans
        elif user.roles.is_assistant:
            return user.roles.manager.staff_government_loans

    def save_model(self, request, obj, form, change):
        if not change:
            if request.user.roles.is_manager:
                obj.manager = request.user
            else:
                obj.manager = request.user.roles.manager
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if request.user.roles.is_manager:
            manager = request.user
        else:
            manager = request.user.roles.manager
        if db_field.name == "institute":
            kwargs["queryset"] = manager.staff_government_benefits
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


    def get_readonly_fields(self, request, obj=None):
        if obj: # editing an existing object
            if request.user.roles.is_manager:
                return []
            else:
                return ['institute', 'loan_type', 'date_str', 'date_end',
              'total', 'mnth_pay', 'total_paid', 'interest', 'is_paid', 'is_valid']
        return []


@admin.register(Branch_Attendance)
class BranchAttendanceAdmin(FilterBranchDropDown):
    ordering = ['-date', 'branch']
    list_display = ['date', 'branch', 'image']
    fields = ['date', 'branch', 'image']
    

    def get_queryset(self, request):
        user = request.user

        if user.roles.is_manager:
            return user.branch_attendance
        else:
            return user.roles.manager.branch_attendance.filter(
                branch__in=request.user.roles.branches.all()).distinct()

    def save_model(self, request, obj, form, change):
        if not change:
            if request.user.roles.is_manager:
                obj.manager = request.user
            else:
                obj.manager = request.user.roles.manager
        super().save_model(request, obj, form, change)


# @admin.register(Hours_In_Summary)
# class HoursInSummaryAdmin(admin.ModelAdmin):
#     change_list_template = 'admin/staff/hours_in_summary_change_list.html'
#     date_hierarchy = 'date'

    # def changelist_view(self, request, extra_context=None):
    #     response = super().changelist_view(
    #         request,
    #         extra_context=extra_context,
    #     )

    #     try:
    #         qs = response.context_data['cl'].queryset
    #     except (AttributeError, KeyError):
    #         return response

    #     metrics = {
    #         'total': Count('id'),
    #         'total_sales': Sum('price'),
    #     }

    #     response.context_data['summary'] = list(
    #         qs
    #         .values('sale__category__name')
    #         .annotate(**metrics)
    #         .order_by('-total_sales')
    #     )

    #     return response

@admin.register(Companies)
class CompanyAdmin(admin.ModelAdmin):
    ordering = ['name']
    list_display = ['name']


    def get_queryset(self, request):
        user = request.user

        if user.roles.is_manager:
            return user.companies
        else:
            return user.roles.manager.companies


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
        elif request.user.roles.is_retailer or request.user.roles.is_assistant:
            obj.manager = request.user.roles.manager
        super().save_model(request, obj, form, change)

