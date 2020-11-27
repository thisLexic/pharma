from django.core.exceptions import ValidationError

def file_size_5(value):
    limit = 5 * 1024 * 1024
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed 5 MiB.')

def file_size_15(value):
    limit = 15 * 1024 * 1024
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed 15 MiB.')
