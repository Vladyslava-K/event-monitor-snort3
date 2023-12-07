from django.utils import timezone
from request.models import RequestLog


class RequestLogMiddleware:
    """Middleware for logging user requests"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        log = None
        if request.META['PATH_INFO'].startswith('/api/v1'):
            log = RequestLog(timestamp=timezone.now(),
                             user_ip=request.META['REMOTE_ADDR'],
                             http_method=request.method,
                             endpoint=request.META['PATH_INFO'],
                             request_data=dict(request.GET))

        response = self.get_response(request)

        if request.META['PATH_INFO'].startswith('/api/v1'):
            log.response_status_code = response.status_code
            log.save()
        return response
