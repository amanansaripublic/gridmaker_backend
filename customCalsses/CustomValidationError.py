

from rest_framework.exceptions import APIException

class CustomValidationError(APIException):
    status_code = 400  # Default to 403
    default_detail = "A validation error occurred."
    default_code = "validation_error"