from django.db import models
from django.contrib.auth import get_user_model

class Branches(models.Model):
    manager = models.ForeignKey(get_user_model(),
                                related_name='branches',
                                on_delete=models.CASCADE,
                                null=True,
                                blank=True)
    location = models.CharField(max_length=256)
    is_open = models.BooleanField(default=True, blank=True)


    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"
        constraints = [
            models.UniqueConstraint(
                fields=['manager',
                        'location',],
                name='unique branch')
        ]


    def __str__(self):
        return self.location


class Current_Branch(models.Model):
    manager = models.ForeignKey(get_user_model(),
                                related_name='staff_branches',
                                on_delete=models.CASCADE,
                                blank=True)
    user = models.OneToOneField(get_user_model(),
                                related_name='cur_branch',
                                on_delete=models.CASCADE,
                                blank=True)
    branch = models.ForeignKey(Branches,
                               related_name='cur_staff',
                               on_delete=models.CASCADE,
                               null=True,
                               blank=True)


    class Meta:
        verbose_name = "Current Branch"
        verbose_name_plural = "Current Branch"

    def __str__(self):
        return str(self.user)