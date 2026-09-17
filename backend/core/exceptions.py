"""
Custom exception handler for QAIP.
Returns consistent JSON error envelope:
  { "success": false, "error": { "code": "...", "message": "...", "details": {} } }
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Wrap DRF's default exception handler output in a consistent envelope."""
    # Let DRF handle the exception first
    response = exception_handler(exc, context)

    if response is not None:
        # Map DRF status codes to human-readable codes
        code_map = {
            400: 'BAD_REQUEST',
            401: 'UNAUTHORIZED',
            403: 'FORBIDDEN',
            404: 'NOT_FOUND',
            405: 'METHOD_NOT_ALLOWED',
            409: 'CONFLICT',
            429: 'TOO_MANY_REQUESTS',
            500: 'INTERNAL_SERVER_ERROR',
        }

        error_code = code_map.get(response.status_code, 'ERROR')

        # Extract the error message and field-level details
        data = response.data
        if isinstance(data, dict):
            # DRF validation errors often have a 'detail' key or field-level keys
            if 'detail' in data:
                message = str(data['detail'])
                details = {}
            else:
                # Field-level validation errors
                message = 'Validation failed. Please check the details.'
                details = {
                    field: [str(e) for e in errors] if isinstance(errors, list) else [str(errors)]
                    for field, errors in data.items()
                }
        elif isinstance(data, list):
            message = ' '.join(str(item) for item in data)
            details = {}
        else:
            message = str(data)
            details = {}

        response.data = {
            'success': False,
            'error': {
                'code': error_code,
                'message': message,
                'details': details,
            }
        }

    else:
        # Unhandled exception — log it and return 500
        logger.exception('Unhandled exception in request processing', exc_info=exc)
        response = Response(
            {
                'success': False,
                'error': {
                    'code': 'INTERNAL_SERVER_ERROR',
                    'message': 'An unexpected error occurred. Please try again later.',
                    'details': {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
