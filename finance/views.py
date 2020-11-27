from private_storage.views import PrivateStorageView

from .models import Sales

class SalesView(PrivateStorageView):
    model = Sales
    model_file_field = 'file'

    def get_queryset(self):
        if self.request.user.roles.is_manager:
            return self.request.user.sales

    def can_access_file(self, private_file):
        if self.request.user.roles.is_manager:
            return True
        elif self.request.user.roles.is_assistant:
            return True
        return False