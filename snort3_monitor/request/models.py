from django.db import models


class RequestLog(models.Model):
    """
    Model representing user requests log.

    Attributes:
    - timestamp (datetime): Request time
    - user_ip (str): users IP address
    - http_method (str): HTTP request method
    - request_data (json): contains query parameters and endpoint
    """
    timestamp = models.DateTimeField()
    user_ip = models.CharField(max_length=30)
    http_method = models.CharField()
    response_status_code = models.IntegerField()
    endpoint = models.CharField()
    request_data = models.JSONField()
