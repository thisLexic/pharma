from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Q, Max

from private_storage.fields import PrivateFileField
from simple_history.models import HistoricalRecords

from location.models import Branches
from adminApiModel.validators import file_size_15


class Sales(models.Model):


    def user_directory_path(instance, filename):
        return str(instance.manager.id) + "/" + \
        instance.branch.location + instance.date.strftime("/%Y/%m") + \
        "/sale/" + instance.date.strftime("/%d.") + \
        filename.split(".")[-1]

    manager = models.ForeignKey(get_user_model(),
                                on_delete=models.CASCADE,
                                related_name='sales',
                                blank=True)
    retailer = models.ForeignKey(get_user_model(),
                                on_delete=models.CASCADE,
                                related_name='retailer_sales',
                                null=True,
                                blank=True)
    branch = models.ForeignKey(Branches,
                                on_delete=models.CASCADE,
                                related_name='sales')
    date = models.DateField()
    short_or_over = models.FloatField(blank=True)
    caja_minus_deposit = models.FloatField(blank=True, null=True)
    gross_sales = models.FloatField()
    cash_on_caja = models.FloatField()
    cash_for_deposit = models.FloatField()
    num_trxn = models.IntegerField(null=True)
    num_cstmr = models.IntegerField(null=True)
    num_rcpt = models.FloatField(null=True)
    OR_nums = models.CharField(max_length=128, null=True)
    total_disc = models.FloatField(null=True)
    petty_cash = models.FloatField(null=True)
    remark = models.CharField(max_length=512, default='', blank=True)
    bank = models.ForeignKey('Banks',
                                on_delete=models.CASCADE,
                                blank=True,
                                null=True)
    was_deposited = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=True)
    file = PrivateFileField(blank=True, null=True, upload_to=user_directory_path, max_file_size=15728640)
    history = HistoricalRecords()



    class Meta:
        verbose_name = "Sale Report"
        verbose_name_plural = "Sales Report"
        constraints = [
            models.UniqueConstraint(
                fields=['manager',
                        'branch',
                        'date',],
                condition=Q(is_valid=True),
                name='unique sale')
        ]



    def __str__(self):
        return str(self.branch) + " " + str(self.date)

    def save(self, *args, **kwargs):
        self.short_or_over = self.cash_on_caja - self.gross_sales
        self.caja_minus_deposit = self.cash_on_caja - self.cash_for_deposit
        return super(Sales, self).save(*args, **kwargs)


class Expense_Types(models.Model):
    manager = models.ForeignKey(get_user_model(),
                                on_delete=models.CASCADE,
                                related_name='expense_types',
                                blank=True)
    name = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True)


    class Meta:
        verbose_name = "Expense Type"
        verbose_name_plural = "Expense Types"
        constraints = [
            models.UniqueConstraint(
                fields=['manager',
                        'name',],
                name='unique expense type')
        ]


    def __str__(self):
        return self.name


class Expense_Methods(models.Model):
    manager = models.ForeignKey(get_user_model(),
                                on_delete=models.CASCADE,
                                related_name='expense_methods',
                                blank=True)
    name = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True)


    class Meta:
        verbose_name = "Expense Payment Method"
        verbose_name_plural = "Expense Payment Methods"
        constraints = [
            models.UniqueConstraint(
                fields=['manager',
                        'name',],
                name='unique expense method')
        ]


    def __str__(self):
        return self.name


class Banks(models.Model):
    manager = models.ForeignKey(get_user_model(),
                                on_delete=models.CASCADE,
                                related_name='banks',
                                blank=True)
    name = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True)


    class Meta:
        verbose_name = "Bank"
        verbose_name_plural = "Banks"
        constraints = [
            models.UniqueConstraint(
                fields=['manager',
                        'name',],
                name='unique bank')
        ]


    def __str__(self):
        return self.name


class Expenses(models.Model):


    def user_directory_path(instance, filename):
        return str(instance.manager.id) + "/" + \
        instance.branch.location + instance.date.strftime("/%Y/%m") + \
        "/expense/" + instance.date.strftime("/%d") + \
        "-" + instance.type_of_expense.name + "-bs" + "." + \
        filename.split(".")[-1]


    def user_directory_path_prf_pay(instance, filename):
        return str(instance.manager.id) + "/" + \
        instance.branch.location + instance.date.strftime("/%Y/%m") + \
        "/expense/" + instance.date.strftime("/%d") + \
        "-" + instance.type_of_expense.name + "-pop" + "." + \
        filename.split(".")[-1]


    def user_directory_path_attch_doc(instance, filename):
        return str(instance.manager.id) + "/" + \
        instance.branch.location + instance.date.strftime("/%Y/%m") + \
        "/expense/" + instance.date.strftime("/%d") + \
        "-" + instance.type_of_expense.name + "-" + instance.doc_desc + "." + \
        filename.split(".")[-1]



    manager = models.ForeignKey(get_user_model(),
                                on_delete=models.CASCADE,
                                related_name='expenses',
                                blank=True)
    retailer = models.ForeignKey(get_user_model(),
                                on_delete=models.CASCADE,
                                related_name='retailer_expenses',
                                null=True,
                                blank=True)
    branch = models.ForeignKey(Branches,
                                on_delete=models.CASCADE,
                                related_name='expenses')
    type_of_expense = models.ForeignKey('Expense_Types',
                                on_delete=models.CASCADE)
    method_of_payment = models.ForeignKey('Expense_Methods',
                                on_delete=models.CASCADE)
    bank = models.ForeignKey('Banks',
                                on_delete=models.CASCADE,
                                blank=True,
                                null=True)
    date = models.DateField()
    amount = models.FloatField()
    remark = models.CharField(max_length=512, default='', blank=True)
    is_valid = models.BooleanField(default=True)
    is_paid = models.BooleanField(default=False)
    bill_stmt = PrivateFileField(blank=True, null=True, upload_to=user_directory_path, max_file_size=15728640)
    prf_pay = PrivateFileField(blank=True, null=True, upload_to=user_directory_path_prf_pay, max_file_size=15728640)
    attch_doc = PrivateFileField(blank=True, null=True, upload_to=user_directory_path_attch_doc, max_file_size=15728640)
    doc_desc = models.CharField(max_length=64, default='extra-doc', blank=True)


    class Meta:
        verbose_name = "Expense Report"
        verbose_name_plural = "Expenses Report"


    def __str__(self):
        return str(self.branch) + " " + str(self.date)

class Bank_Status(models.Model):


    def user_directory_path(instance, filename):
        if instance.sale_report:
            return str(instance.manager.id) + "/" + \
            instance.bank.name + instance.date.strftime("/%Y/%m") + \
            "/bank_status/" + instance.date.strftime("/%d") + \
            "-" + "deposit" + "." + \
            filename.split(".")[-1]
        return str(instance.manager.id) + "/" + \
            instance.bank.name + instance.date.strftime("/%Y/%m") + \
            "/bank_status/" + instance.date.strftime("/%d") + \
            "-" + "withdraw" + "." + \
            filename.split(".")[-1]


    manager = models.ForeignKey(get_user_model(),
                                on_delete=models.CASCADE,
                                related_name='bank_statuses',
                                blank=True)
    bank = models.ForeignKey('Banks',
                                on_delete=models.CASCADE)
    sale_report = models.OneToOneField('Sales',
                                on_delete=models.CASCADE,
                                related_name='bank_status',
                                blank=True,
                                null=True)
    expense_report = models.OneToOneField('Expenses',
                                on_delete=models.CASCADE,
                                related_name='bank_status',
                                blank=True,
                                null=True)
    deposit = models.FloatField(blank=True, null=True)
    withdraw = models.FloatField(blank=True, null=True)
    date = models.DateTimeField()
    update = models.FloatField(blank=True, null=True)
    remark = models.CharField(max_length=256, default='', blank=True)
    check = models.BooleanField(default=False)
    online = models.BooleanField(default=False)
    image = PrivateFileField(blank=True, null=True, upload_to=user_directory_path, max_file_size=15728640)


# cannot be changed
# manager
# sale 1-1
# expense 1-1

# automatically changed
# bank
# deposit
# withdraw

# manually changed
# date
# update
# remark
# check
# online
# image

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


    class Meta:
        verbose_name = "Bank Status"
        verbose_name_plural = "Bank Statuses"
        # unique constraint unnecessary since it is reliant on
        # unique sales/expense entries for uniqueness
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=['manager',
        #                 'branch',
        #                 'date',
        #                 'type_of_expense',],
        #         condition=Q(is_valid=True),
        #         name='unique expense')
        # ]

    def __str__(self):
        return str(self.bank) + " " + str(self.date)

    def total(self):
        date = self.date
        bank = self.bank
        prev_record = self.get_prev(date, bank)
        if not prev_record:
            return self.get_deposit_withdraw()

        elif not prev_record.update:
            return prev_record.total() + self.get_deposit_withdraw()

        elif prev_record.update:
            return prev_record.update + self.get_deposit_withdraw()



    def get_prev(self, date, bank):
        m_bank_status = Bank_Status.objects.filter(bank=bank).filter(date__lt=date).order_by('-date')
        if not m_bank_status:
            return None
        return m_bank_status.first()

    def get_deposit_withdraw(self):
        if self.deposit:
            return self.deposit
        if self.withdraw == None:
            return 0
        return -(self.withdraw)

    def error(self):
        if self.update:
            return self.update - self.total()
        return None