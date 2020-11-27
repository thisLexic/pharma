from rest_framework import generics, permissions
from rest_framework.response import Response

from knox.models import AuthToken

from .serializers import LoginSerializer, StaffSerializer


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = serializer.validated_data
        _, token = AuthToken.objects.create(staff)
        return Response({
          "staff": StaffSerializer(staff, context=self.get_serializer_context()).data,
          "token": token
        })


class StaffView(generics.RetrieveAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    serializer_class = StaffSerializer

    def get_object(self):
        return self.request.user
