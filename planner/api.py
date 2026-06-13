"""Shared API response helpers for SkillSprint."""

from rest_framework.response import Response
from rest_framework.views import exception_handler


def standard_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return None

    detail = response.data.get('detail') if isinstance(response.data, dict) else None
    message = str(detail or 'Request failed.')
    errors = response.data if isinstance(response.data, dict) else {'detail': response.data}

    return Response(
        {
            'ok': False,
            'message': message,
            'errors': errors,
        },
        status=response.status_code,
        headers=response.headers,
    )
