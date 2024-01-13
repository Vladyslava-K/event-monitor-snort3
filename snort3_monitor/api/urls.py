from django.urls import path

from .views import EventsList, EventsCount, RequestList, RulesList, ExecuteCommand, UpdateRules, StartRuleProfiler, RuleProfilerLast


urlpatterns = [
    path('events', EventsList.as_view(), name='events_list'),
    path('events/count', EventsCount.as_view(), name='events_count'),
    path('requests-log', RequestList.as_view()),
    path('rules', RulesList.as_view(), name='rules_list'),
    path('execute', ExecuteCommand.as_view(), name='execute_command'),
    path('update-rules', UpdateRules.as_view(), name='update_rules'),
    path('rule-profiler', StartRuleProfiler.as_view(), name='rule_profiler'),
    path('rule-profiler-last', RuleProfilerLast.as_view(), name='rule_profiler_last'),
]
