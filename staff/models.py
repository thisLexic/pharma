from datetime import timedelta

from django.db import models
from django.contrib.auth import get_user_model

from private_storage.fields import PrivateFileField

from location.models import Branches
from simple_history.models import HistoricalRecords



class Roles(models.Model):
    user = models.OneToOneField(get_user_model(),
                             related_name='roles',
                             on_delete=models.CASCADE,
                             null=True,
                             blank=True)
    manager = models.ForeignKey(get_user_model(),
                                related_name='staff_roles',
                                on_delete=models.CASCADE,
                                null=True,
                                blank=True)
    company = models.ForeignKey('Companies',
                             related_name='company',
                             on_delete=models.CASCADE,
                             null=True,
                             blank=True)
    days = models.IntegerField(blank=True, null=True)
    branches = models.ManyToManyField(Branches,
                                related_name='staffs',
                                blank=True)
    is_manager = models.BooleanField(default=False)
    staff_id = models.IntegerField(null=True)
    hrly_rate = models.FloatField(null=True)
    hrly_allow = models.FloatField(null=True)
    is_retailer = models.BooleanField(default=False)
    is_assistant = models.BooleanField(default=False)
    sale_days = models.IntegerField(blank=True, null=True)
    sale_branches = models.ManyToManyField(Branches,
                                related_name='sale_staffs',
                                blank=True)
    sale_can_validate = models.BooleanField(default=False)
    sale_change_deposit = models.BooleanField(default=False)
    expense_days = models.IntegerField(blank=True, null=True)
    expense_branches = models.ManyToManyField(Branches,
                                related_name='expense_staffs',
                                blank=True)
    expense_can_validate = models.BooleanField(default=False)
    purchase_days = models.IntegerField(blank=True, null=True)
    purchase_branches = models.ManyToManyField(Branches,
                                related_name='purchase_staffs',
                                blank=True)
    purchase_can_validate = models.BooleanField(default=False)
    hours_in_days = models.IntegerField(blank=True, null=True)
    hours_in_branches = models.ManyToManyField(Branches,
                                related_name='hours_in_staffs',
                                blank=True)


    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        constraints = [
            models.UniqueConstraint(
                fields=['manager',
                        'staff_id'],
                name='unique staff id'),
        ]


    def __str__(self):
        return str(self.user)


class Hours_In(models.Model):
    staff = models.ForeignKey(get_user_model(),
                             related_name='hours_in',
                             on_delete=models.CASCADE)
    manager = models.ForeignKey(get_user_model(),
                                related_name='staff_hours_in',
                                on_delete=models.CASCADE,
                                blank=True)
    date = models.DateField()
    hours = models.FloatField()
    day_type = models.CharField(
        max_length=5,
        choices=[
            ('REG', 'Regular Day'),
            ('HD', 'Regular Holiday'),
            ('SHD', 'Special Holiday'),
            ('VL', 'Vacation Leave'),
            ('SL', 'Sick Leave'),
        ],
        default='REG'
    )
    history = HistoricalRecords()


    class Meta:
        verbose_name = "Working Hours"
        verbose_name_plural = "Working Hours"
        constraints = [
            models.UniqueConstraint(
                fields=['date',
                        'manager',
                        'staff'],
                name='unique hours in'),
        ]


    def __str__(self):
        return str(self.staff) + " " + str(self.date)

    def get_dailies(staff, day, date):
        if day == '8':
            up_limit = date.replace(day=6)

            dt1 = date.replace(day=1)
            dt2 = dt1 - timedelta(days=1)
            low_limit = dt2.replace(day=22)
        else:
            up_limit = date.replace(day=21)
            low_limit = date.replace(day=7)


        return Hours_In.objects.filter(staff=staff).filter(date__gte=low_limit).filter(date__lte=up_limit)


class Bimonthly_In(models.Model):
    staff = models.ForeignKey(get_user_model(),
                             related_name='bimonthly_in',
                             on_delete=models.CASCADE)
    manager = models.ForeignKey(get_user_model(),
                                related_name='staff_bimonthly_in',
                                on_delete=models.CASCADE,
                                blank=True)
    date = models.DateField()
    day = models.CharField(
        max_length=5,
        choices=[
            ('8', '8'),
            ('23', '23'),
        ]
    )
    hrs_reg = models.FloatField(default=0)
    pay_reg = models.FloatField(default=0)
    hrs_hd = models.FloatField(default=0)
    pay_hd = models.FloatField(default=0)
    hrs_shd = models.FloatField(default=0)
    pay_shd = models.FloatField(default=0)
    hrs_vl = models.FloatField(default=0)
    pay_vl = models.FloatField(default=0)
    hrs_sl = models.FloatField(default=0)
    pay_sl = models.FloatField(default=0)

    pay_tot = models.FloatField()
    extr_alw = models.FloatField(default=0)

    bene_a = models.FloatField(blank=True, null=True)
    bene_a_desc = models.CharField(max_length=128, blank=True, null=True)
    bene_b = models.FloatField(blank=True, null=True)
    bene_b_desc = models.CharField(max_length=128, blank=True, null=True)
    bene_c = models.FloatField(blank=True, null=True)
    bene_c_desc = models.CharField(max_length=128, blank=True, null=True)
    bene_d = models.FloatField(blank=True, null=True)
    bene_d_desc = models.CharField(max_length=128, blank=True, null=True)

    ded_a = models.FloatField(blank=True, null=True)
    ded_a_desc = models.CharField(max_length=128, blank=True, null=True)
    ded_b = models.FloatField(blank=True, null=True)
    ded_b_desc = models.CharField(max_length=128, blank=True, null=True)
    ded_c = models.FloatField(blank=True, null=True)
    ded_c_desc = models.CharField(max_length=128, blank=True, null=True)
    ded_d = models.FloatField(blank=True, null=True)
    ded_d_desc = models.CharField(max_length=128, blank=True, null=True)

    giv_a = models.FloatField(blank=True, null=True)
    giv_a_desc = models.CharField(max_length=128, blank=True, null=True)
    giv_b = models.FloatField(blank=True, null=True)
    giv_b_desc = models.CharField(max_length=128, blank=True, null=True)
    giv_c = models.FloatField(blank=True, null=True)
    giv_c_desc = models.CharField(max_length=128, blank=True, null=True)
    giv_d = models.FloatField(blank=True, null=True)
    giv_d_desc = models.CharField(max_length=128, blank=True, null=True)

    pay_sss = models.BooleanField(default=False)
    pay_ph = models.BooleanField(default=False)
    pay_pi = models.BooleanField(default=False)


    class Meta:
        verbose_name = "Working BiMonthly"
        verbose_name_plural = "Working BiMonthly"
        constraints = [
            models.UniqueConstraint(
                fields=['day',
                        'manager',
                        'staff',
                        'date'],
                name='unique bimonthly in'),
        ]


    def __str__(self):
        return str(self.staff) + " " + str(self.day)


class Government_Benefits(models.Model):
    staff = models.ForeignKey(get_user_model(),
                             related_name='government_benefits',
                             on_delete=models.CASCADE)
    manager = models.ForeignKey(get_user_model(),
                                related_name='staff_government_benefits',
                                on_delete=models.CASCADE,
                                blank=True)
    institute = models.CharField(
        max_length=5,
        choices=[
            ('SSS', 'SSS'),
            ('PH', 'Phil Health'),
            ('PI', 'Pag Ibig'),
        ]
    )
    total = models.FloatField(default=0)
    staff_cont = models.FloatField(default=0)
    mngr_cont = models.FloatField(default=0)

    def __str__(self):
        return str(self.staff) + " " + str(self.institute)


    class Meta:
        verbose_name = "Government Benefits"
        verbose_name_plural = "Government Benefits"
        constraints = [
            models.UniqueConstraint(
                fields=['manager',
                        'staff',
                        'institute'],
                name='unique government benefit'),
        ]


class Loans(models.Model):
    manager = models.ForeignKey(get_user_model(),
                                related_name='staff_government_loans',
                                on_delete=models.CASCADE,
                                blank=True)
    institute = models.ForeignKey(Government_Benefits,
                                  related_name='loans',
                                  on_delete=models.CASCADE)
    loan_type = models.CharField(
        max_length=5,
        choices=[
            ('SAL', 'Salary Loan'),
            ('EME', 'Emergency Loan'),
            ('CAL', 'Calamity Loan'),
        ]
    )
    date_str = models.DateField()
    date_end = models.DateField()

    total = models.FloatField()
    mnth_pay = models.FloatField()
    total_paid = models.FloatField()
    interest = models.FloatField()

    is_paid = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=True)


    class Meta:
        verbose_name = "Loan"
        verbose_name_plural = "Loans"

    def __str__(self):
        return str(self.institute)


class Branch_Attendance(models.Model):


    def user_directory_path(instance, filename):
        return str(instance.manager.id) + "/" + \
        instance.branch.location + instance.date.strftime("/%Y/%m") + \
        "/branch-attendance/" + instance.date.strftime("/%d.") + \
        filename.split(".")[-1]


    manager = models.ForeignKey(get_user_model(),
                                related_name='branch_attendance',
                                on_delete=models.CASCADE,
                                blank=True)
    branch = models.ForeignKey(Branches,
                                  related_name='attendance',
                                  on_delete=models.CASCADE)
    date = models.DateField()
    image = PrivateFileField(null=True, upload_to=user_directory_path, max_file_size=15728640)


    class Meta:
        verbose_name = "Branch Attendance"
        verbose_name_plural = "Branch Attendance"
        constraints = [
            models.UniqueConstraint(
                fields=['manager',
                        'branch',
                        'date'],
                name='unique branch attendance'),
        ]

    # def __str__(self):
    #     return str(self.institute)

class Companies(models.Model):

    manager = models.ForeignKey(get_user_model(),
                                related_name='companies',
                                on_delete=models.CASCADE,
                                blank=True)
    name = models.CharField(max_length=256)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        constraints = [
            models.UniqueConstraint(
                fields=['name',
                        'manager'],
                name='unique company'),
        ]

    def __str__(self):
        return self.name

# class Hours_In_Summary(Hours_In):
#     class Meta:
#         proxy = True
#         verbose_name = 'Hours In Summary'
#         verbose_name_plural = 'Hours In Summary'


# class Staff_Attendance(models.Model):
#     staff = models.ForeignKey(get_user_model(),
#                              related_name='attendance',
#                              on_delete=models.CASCADE)
#     manager = models.ForeignKey(get_user_model(),
#                                 related_name='staff_attendance',
#                                 on_delete=models.CASCADE,
#                                 blank=True)
#     year = models.IntegerField()
#     days_sick = models.IntegerField()
#     days_vaca = models.IntegerField()
#     days_work = models.IntegerField()


#     class Meta:
#         verbose_name = "Staff Attendance"
#         verbose_name_plural = "Staff Attendance"
#         constraints = [
#             models.UniqueConstraint(
#                 fields=['manager',
#                         'branch',
#                         'year'],
#                 name='unique staff attendance'),
#         ]