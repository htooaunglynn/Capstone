"""Shared API response helpers for SkillSprint."""

from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import exception_handler


def success_payload(message, data=None):
    return {
        'ok': True,
        'message': message,
        'data': data or {},
    }


def error_payload(message, errors=None):
    return {
        'ok': False,
        'message': message,
        'errors': errors or {},
    }


def api_success(message, data=None, response_status=status.HTTP_200_OK):
    return Response(success_payload(message, data), status=response_status)


def api_error(message, errors=None, response_status=status.HTTP_400_BAD_REQUEST):
    return Response(error_payload(message, errors), status=response_status)


def json_success(message, data=None, response_status=200):
    return JsonResponse(success_payload(message, data), status=response_status)


def json_error(message, errors=None, response_status=400):
    return JsonResponse(error_payload(message, errors), status=response_status)


def standard_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return None

    detail = response.data.get('detail') if isinstance(response.data, dict) else None
    message = str(detail or 'Request failed.')
    errors = response.data if isinstance(response.data, dict) else {'detail': response.data}

    return Response(error_payload(message, errors), status=response.status_code, headers=response.headers)
