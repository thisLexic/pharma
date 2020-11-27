from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q

from private_storage.fields import PrivateFileField

from location.models import Branches
from adminApiModel.validators import file_size_15


class Purchases(models.Model):


    def invoice_user_directory_path(instance, filename):
        return str(instance.manager.id) + "/" + \
        instance.branch.location + instance.date.strftime("/%Y/%m") + \
        "/invoice/" + instance.date.strftime("/%d.") + \
        filename.split(".")[-1]


    def payment_user_directory_path(instance, filename):
        return str(instance.manager.id) + "/" + \
        instance.branch.location + instance.date.strftime("/%Y/%m") + \
        "/payment/" + instance.date.strftime("/%d.") + \
        filename.split(".")[-1]


    manager = models.ForeignKey(get_user_model(),
                               related_name='purchases',
                               on_delete=models.CASCADE,
                               null=True,
                               blank=True)
    retailer = models.ForeignKey(get_user_model(),
                               related_name='retailer_purchases',
                               on_delete=models.CASCADE,
                               null=True,
                               blank=True)
    staff = models.ForeignKey(get_user_model(),
                               related_name='staff_purchases',
                               on_delete=models.CASCADE,
                               null=True,
                               blank=True)
    branch = models.ForeignKey(Branches,
                               related_name='purchases',
                               on_delete=models.CASCADE)
    payment_method = models.ForeignKey('Purchase_Payment_Method',
                               related_name='purchases',
                               on_delete=models.CASCADE,
                               null=True,
                               blank=True)
    distributor = models.ForeignKey('Distributor',
                               related_name='purchases',
                               on_delete=models.CASCADE,
                               null=True)
    short_or_over = models.FloatField(blank=True, null=True)
    delivered_worth = models.FloatField(blank=True, null=True)
    invoice_worth = models.FloatField(blank=True, null=True)
    remark = models.CharField(max_length=512, default='', blank=True)
    is_paid = models.BooleanField()
    is_valid = models.BooleanField(default=True)
    date = models.DateField()
    invoice_range = models.CharField(max_length=256)
    invoice_file = PrivateFileField(blank=True, null=True, upload_to=invoice_user_directory_path, max_file_size=15728640)
    proof_of_payment = PrivateFileField(blank=True, null=True, upload_to=payment_user_directory_path, max_file_size=15728640)


    class Meta:
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"

    def __str__(self):
        return str(self.branch) + " " + str(self.date)

    def save(self, *args, **kwargs):
        if self.invoice_worth and self.delivered_worth:
            self.short_or_over = self.invoice_worth - self.delivered_worth
        else:
            self.short_or_over = None
        return super(Purchases, self).save(*args, **kwargs)


class Purchase_Payment_Method(models.Model):
    manager = models.ForeignKey(get_user_model(),
                                on_delete=models.CASCADE,
                                related_name='purchase_payment_methods',
                                blank=True)
    name = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True)


    class Meta:
        verbose_name = "Purchase Payment Method"
        verbose_name_plural = "Purchase Payment Methods"
        constraints = [
            models.UniqueConstraint(
                fields=['manager',
                        'name',],
                name='unique purchase payment method')
        ]


    def __str__(self):
        return self.name


class Distributor(models.Model):
    manager = models.ForeignKey(get_user_model(),
                                on_delete=models.CASCADE,
                                related_name='distributors',
                                blank=True)
    name = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True)


    class Meta:
        verbose_name = "Distributor"
        verbose_name_plural = "Distributors"
        constraints = [
            models.UniqueConstraint(
                fields=['manager',
                        'name',],
                name='unique distributor')
        ]


    def __str__(self):
        return self.name


class Products(models.Model):


    manager = models.ForeignKey(get_user_model(),
                               related_name='products',
                               on_delete=models.CASCADE,
                               null=True,
                               blank=True)
    name = models.CharField(max_length=256)
    size = models.CharField(max_length=128)
    price = models.FloatField()
    is_active = models.BooleanField(default=True)
    date_start = models.DateField(editable=False, blank=False)
    product_id = models.CharField(max_length=128)
    items_per_package = models.IntegerField()
    cost = models.FloatField(null=True)


    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        constraints = [
            models.UniqueConstraint(
                fields=['manager',
                        'name',
                        'size',
                        'date_start',],
                name='unique product'),
            models.UniqueConstraint(
                fields=['manager',
                        'product_id',],
                name='unique product id'),
        ]


    def __str__(self):
        return str(self.name) + " " + str(self.size)

    def save(self, *args, **kwargs):
        if not self.id:
            self.date_start = timezone.now().date()
        return super(Products, self).save(*args, **kwargs)


class Transactions(models.Model):


    manager = models.ForeignKey(get_user_model(),
                               related_name='transactions',
                               on_delete=models.CASCADE,
                               null=True,
                               blank=True)
    retailer = models.ForeignKey(get_user_model(),
                               related_name='retailer_transactions',
                               on_delete=models.CASCADE,
                               null=True,
                               blank=True)
    branch = models.ForeignKey(Branches,
                               related_name='transactions',
                               on_delete=models.CASCADE,
                               null=True,
                               blank=True)
    product = models.ForeignKey(Products,
                                related_name='transactions',
                                on_delete=models.PROTECT)
    count = models.IntegerField()
    is_valid = models.BooleanField(default=True)
    date = models.DateField(editable=False, blank=True)
    time = models.TimeField(editable=False, blank=True, null = True)


    def save(self, *args, **kwargs):
        if not self.id:
            self.date = timezone.now().date()
            self.time = timezone.now().time()
        return super(Transactions, self).save(*args, **kwargs)


    def __str__(self):
        return str(self.retailer) + " " + str(self.product) + " " + str(self.count)
