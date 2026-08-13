from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # Convert default errors to your format
        if isinstance(response.data, dict):
            errors = []

            # Handle field errors
            for key, value in response.data.items():
                if isinstance(value, list):
                    for error in value:
                        error_str = str(error)
                        if key == "non_field_errors" or not error_str.startswith("This"):
                            errors.append(error_str)
                        else:
                            errors.append(
                                f"{key.capitalize().replace('_', ' ')} {error_str.removeprefix('This ')}"
                            )

                else:
                    value_str = str(value)
                    if key == "non_field_errors" or not value_str.startswith("This"):
                        errors.append(value_str)
                    else:
                        errors.append(
                            f"{key.capitalize().replace('_', ' ')} {value_str.removeprefix('This ')}"
                        )

            response.data = {"message": errors, "status": response.status_code}
        elif isinstance(response.data, list):
            errors = [str(error) for error in response.data]
        else:
            errors = [str(response.data)]
        
        response.data = {"message": errors, "status": response.status_code}

    return response
