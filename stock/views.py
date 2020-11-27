from django.utils import timezone

from rest_framework import permissions, mixins, viewsets
from rest_framework.response import Response

from .models import Transactions, Products
from .serializers import TransactionReadSerializer, \
                         TransactionCreateSerializer


class TransactionViewSet(mixins.ListModelMixin,
                         mixins.CreateModelMixin,
                         viewsets.GenericViewSet):
    # put retailer, product restrictions

    permission_classes = [
        permissions.IsAuthenticated,
    ]
    serializer_class = TransactionReadSerializer


    def get_queryset(self):
        # branch filter
        return Transactions.objects.filter(date=timezone.now()
                                    ).filter(is_valid=True
                                    ).filter(manager=self.request.user.roles.manager
                                    ).order_by('-time')


    def create(self, request, *args, **kwargs):
        write_serializer = TransactionCreateSerializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        instance = self.perform_create(write_serializer)
        read_serializer = TransactionReadSerializer(instance)
        return Response(read_serializer.data)


    def perform_create(self, serializer):
        return serializer.save(manager=self.request.user.roles.manager, branch=self.request.user.cur_branch)