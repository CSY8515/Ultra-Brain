"""Fail-closed validation for caller-supplied personal assistance records."""
from __future__ import annotations
from dataclasses import fields
from datetime import timezone
from typing import Mapping, Sequence
from .models import ContextItem, DecisionOption, Goal, Reminder, ScheduleItem, SecretaryGrant, Task, freeze
from datetime import datetime

class ValidationError(ValueError): pass
class AuthorizationError(PermissionError): pass
OPERATIONS={"daily_briefing","weekly_review","monthly_review","reminder_support","recommendation","priority_management","decision_support","personal_assistance","context_support","scheduling_support"}
STATUSES={"open","in_progress","blocked","completed","cancelled"}

def parse_time(value, label="time"):
    if not isinstance(value,str) or len(value)>40: raise ValidationError(f"{label}:invalid")
    try: parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc: raise ValidationError(f"{label}:invalid") from exc
    if parsed.tzinfo is None: raise ValidationError(f"{label}:timezone-required")
    return parsed.astimezone(timezone.utc)

def text(value,label,maximum=500):
    if not isinstance(value,str) or not value.strip() or len(value)>maximum: raise ValidationError(f"{label}:invalid")
    return value.strip()

def _record(value,cls,label):
    if isinstance(value,cls): return value
    if not isinstance(value,Mapping): raise ValidationError(f"{label}:object-required")
    if set(value)-{item.name for item in fields(cls)}: raise ValidationError(f"{label}:unknown-field")
    try:
        payload=dict(value)
        if cls is DecisionOption and "scores" in payload: payload["scores"]=freeze(payload["scores"])
        return cls(**payload)
    except (TypeError,ValueError) as exc: raise ValidationError(f"{label}:invalid") from exc

def validate_grant(value,operation,now):
    grant=_record(value,SecretaryGrant,"grant")
    text(grant.id,"grant:id",100); text(grant.user_id,"grant:user",100); text(grant.safety_decision_id,"grant:safety-decision",100)
    if not grant.approved: raise AuthorizationError("grant:not-approved")
    if operation not in OPERATIONS or operation not in grant.allowed_operations: raise AuthorizationError("operation:not-allowed")
    if not 1<=grant.max_items<=1000 or not 1<=grant.max_horizon_days<=366: raise ValidationError("grant:budget-invalid")
    if not set(grant.allowed_operations)<=OPERATIONS or len(set(grant.allowed_operations))!=len(grant.allowed_operations): raise ValidationError("grant:operations-invalid")
    if not grant.allowed_context_categories or len(set(grant.allowed_context_categories))!=len(grant.allowed_context_categories): raise ValidationError("grant:categories-invalid")
    start,end=parse_time(grant.valid_from),parse_time(grant.expires_at); current=now.astimezone(timezone.utc)
    if end<=start or current<start or current>=end: raise AuthorizationError("grant:not-current")
    return grant

def validate_items(values: Sequence,cls,grant,label):
    if isinstance(values,(str,bytes)) or len(values)>grant.max_items: raise ValidationError(f"{label}:item-budget-exceeded")
    result=tuple(_record(value,cls,f"{label}:item") for value in values); ids=set()
    for item in result:
        item_id=text(item.id,f"{label}:id",100)
        if item_id in ids: raise ValidationError(f"{label}:duplicate-id")
        ids.add(item_id)
        if hasattr(item,"category") and text(item.category,f"{label}:category",100) not in grant.allowed_context_categories: raise AuthorizationError("context:category-not-allowed")
        if getattr(item,"sensitive",False) and not grant.allow_sensitive_context: raise AuthorizationError("context:sensitive-not-allowed")
        _specific(item,label)
    return result

def _specific(item,label):
    if isinstance(item,Task):
        text(item.title,f"{label}:title"); parse_time(item.created_at)
        if item.due_at is not None: parse_time(item.due_at)
        if item.status not in STATUSES or not 1<=item.importance<=5 or not 1<=item.effort_minutes<=10080: raise ValidationError(f"{label}:task-invalid")
    elif isinstance(item,ScheduleItem):
        text(item.title,f"{label}:title")
        if parse_time(item.end_at)<=parse_time(item.start_at): raise ValidationError(f"{label}:interval-invalid")
    elif isinstance(item,Reminder):
        text(item.title,f"{label}:title"); parse_time(item.remind_at)
        if len(item.source_id)>100: raise ValidationError(f"{label}:source-invalid")
    elif isinstance(item,ContextItem):
        text(item.content,f"{label}:content",2000); text(item.source,f"{label}:source",200); parse_time(item.observed_at)
    elif isinstance(item,Goal):
        text(item.title,f"{label}:title"); text(item.period,f"{label}:period",100)
        if item.status not in STATUSES or isinstance(item.progress,bool) or not isinstance(item.progress,(int,float)) or not 0<=item.progress<=1: raise ValidationError(f"{label}:goal-invalid")
    elif isinstance(item,DecisionOption):
        text(item.label,f"{label}:label")
        if not item.scores or len(item.scores)>20: raise ValidationError(f"{label}:scores-invalid")
        for criterion,score in item.scores.items():
            text(criterion,f"{label}:criterion",100)
            if isinstance(score,bool) or not isinstance(score,(int,float)) or not 0<=score<=1: raise ValidationError(f"{label}:score-invalid")
