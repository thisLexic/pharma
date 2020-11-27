from rest_framework import serializers

from .models import Transactions, Products


class TransactionReadSerializer(serializers.ModelSerializer):
    retailer = serializers.StringRelatedField()
    product = serializers.SlugRelatedField(slug_field='product_id', read_only=True)


    class Meta:
        model = Transactions 
        fields = ['retailer', 'time', 'product', 'count']


class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transactions 
        fields = ['retailer', 'product', 'count']