import random
import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone

from finance.models import Sales
from location.models import Branches

def add_sales(count=10, manager='manager1', date=datetime.datetime(year=2020, month=3, day=27).date()):
    manager = get_user_model().objects.get(username=manager)

    staffs = get_user_model().objects.filter(roles__manager=manager)
    staffs_count = staffs.count()
    staffs_num = [i for i in range(staffs_count)]

    branches = Branches.objects.filter(manager=manager)
    branches_count = branches.count()
    branches_num = [i for i in range(branches_count)]


    for c in range(count):
        cash_on_caja = random.randint(10000, 20000)
        cash_for_deposit = cash_on_caja
        goUp = random.randint(0, 1)
        if goUp:
            gross_sales = cash_on_caja + random.randint(0, 100)
        else:
            gross_sales = cash_on_caja - random.randint(0, 100)
        Sales(
            manager=manager,
            retailer=staffs[random.choice(staffs_num)],
            branch=branches[random.choice(branches_num)],
            date=date,
            gross_sales=gross_sales,
            cash_on_caja=cash_on_caja,
            cash_for_deposit=cash_for_deposit,
        ).save()

        date = date - datetime.timedelta(days=1)