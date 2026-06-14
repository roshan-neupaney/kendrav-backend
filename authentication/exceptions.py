from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # Convert default errors to your format
        if isinstance(response.data, dict):
            errors = []
            
            # Handle field errors
            for key, value in response.data.items():
                if isinstance(value, list):
                    errors.extend(value)
                else:
                    errors.append(str(value))
            
            response.data = {
                "message": errors,
                "status": response.status_code
            }
        else:
            response.data = {
                "message": [str(response.data)],
                "status": response.status_code
            }

    return response