from django.db import models


class Rule(models.Model):
    """
    Model representing an intrusion detection or prevention rule.

    Attributes:
    - id (str): Combination of sid and rev, primary key
    - sid (SnortLogEvent): The SnortLogEvent ForeignKey representing the associated log event.
    - rev (int): The revision number of a given Snort rule.
    - action (str): Rule actions tell Snort how to handle matching packets (e.g., "alert" or "drop").
    - msg (str): The message associated with the rule, providing additional information about the rule.
    - json (json): Whole rule entry saved in json format.
    """
    id = models.CharField(max_length=20, primary_key=True)
    sid = models.IntegerField()
    rev = models.IntegerField()
    action = models.CharField(max_length=10)
    msg = models.TextField()
    json = models.JSONField()

    def save(self, *args, **kwargs):
        self.id = f"{self.sid}/{self.rev}"
        super().save(*args, **kwargs)


class Event(models.Model):
    """
    Model representing a Snort Intrusion Detection / Prevention System log event.

    Attributes:
    - rule_id (str): Rule ForeignKey representing associated rule.
    - timestamp (datetime): The date and time when the event occurred.
    - src_addr (str): The source IP address from which the event originated.
    - src_port (int, optional): The source port number if applicable, otherwise None.
    - dst_addr (str): The destination IP address to which the event is directed.
    - dst_port (int, optional): The destination port number if applicable, otherwise None.
    - proto (str): The network protocol used for the communication (e.g., TCP, UDP).
    - is_deleted (bool): States whether an entry was deleted by user and would be returned on requests.
    """
    rule_id = models.ForeignKey(Rule, on_delete=models.CASCADE, to_field='id')
    timestamp = models.DateTimeField()
    src_addr = models.CharField(max_length=30)
    src_port = models.IntegerField(null=True, blank=True)
    dst_addr = models.CharField(max_length=30)
    dst_port = models.IntegerField(null=True, blank=True)
    proto = models.CharField(max_length=10)
    is_deleted = models.BooleanField(default=False)
