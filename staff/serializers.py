from django.contrib.auth import get_user_model, authenticate

from rest_framework import serializers

from .models import Roles
from location.models import Current_Branch, Branches


class BranchSerializer(serializers.ModelSerializer):

    class Meta:
        model = Branches
        fields = ('location',)


class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Roles
        fields = ('staff_id', 'is_retailer')


class CurrentBranchSerializer(serializers.ModelSerializer):
    branch = BranchSerializer(read_only=True)

    class Meta:
        model = Current_Branch
        fields = ('branch',)


class StaffSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(read_only=True)
    cur_branch = CurrentBranchSerializer(read_only=True)


    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'roles', 'cur_branch')


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError('Incorrect Credentials')
