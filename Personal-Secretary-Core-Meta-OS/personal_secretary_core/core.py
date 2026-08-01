"""Deterministic, non-executing Personal Secretary Core services."""
from __future__ import annotations
from datetime import date, datetime, time, timedelta, timezone
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence
from .models import (AssistancePlan,AssistanceStep,Briefing,ContextItem,ContextResult,DecisionAnalysis,DecisionOption,Goal,PriorityItem,PriorityPlan,Recommendation,RecommendationSet,Reminder,Review,ScheduleItem,SchedulePlan,SecretaryGrant,Task)
from .validation import AuthorizationError,ValidationError,parse_time,text,validate_grant,validate_items

Clock=Callable[[],datetime]
def _utc(value):
    if value.tzinfo is None: raise ValidationError("time:timezone-required")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00","Z")

class PersonalSecretaryCore:
    """Ephemeral assistance facade; retains no records and performs no action."""
    def __init__(self,clock: Clock|None=None): self._clock=clock or (lambda:datetime.now(timezone.utc))
    def _grant(self,grant,operation):
        now=self._clock()
        if now.tzinfo is None: raise ValidationError("clock:timezone-required")
        return validate_grant(grant,operation,now),now.astimezone(timezone.utc)

    def daily_briefing(self,grant,day: date,*,tasks=(),schedule=(),reminders=(),context=()):
        approved,now=self._grant(grant,"daily_briefing")
        if not isinstance(day,date): raise ValidationError("briefing:date-invalid")
        start=datetime.combine(day,time.min,timezone.utc); end=start+timedelta(days=1)
        if abs((day-now.date()).days)>approved.max_horizon_days: raise AuthorizationError("horizon:exceeded")
        tasks=validate_items(tasks,Task,approved,"tasks"); schedule=validate_items(schedule,ScheduleItem,approved,"schedule"); reminders=validate_items(reminders,Reminder,approved,"reminders"); context=validate_items(context,ContextItem,approved,"context")
        overdue=tuple(sorted(x.id for x in tasks if x.status not in {"completed","cancelled"} and x.due_at and parse_time(x.due_at)<start))
        due=tuple(sorted(x.id for x in tasks if x.status not in {"completed","cancelled"} and x.due_at and start<=parse_time(x.due_at)<end))
        events=tuple(x.id for x in sorted(schedule,key=lambda x:(parse_time(x.start_at),x.id)) if start<=parse_time(x.start_at)<end)
        alerts=tuple(x.id for x in sorted(reminders,key=lambda x:(parse_time(x.remind_at),x.id)) if not x.acknowledged and parse_time(x.remind_at)<end)
        recent=tuple(x.id for x in sorted(context,key=lambda x:(parse_time(x.observed_at),x.id),reverse=True) if parse_time(x.observed_at)<end)
        return Briefing("daily",_utc(start),_utc(end),_utc(now),MappingProxyType({"overdue":overdue,"due_today":due,"schedule":events,"reminders":alerts,"context":recent}))

    def weekly_review(self,grant,period_end: date,*,tasks=(),goals=(),schedule=()): return self._review(grant,"weekly_review","weekly",period_end,7,tasks,goals,schedule)
    def monthly_review(self,grant,period_end: date,*,tasks=(),goals=(),schedule=()):
        if not isinstance(period_end,date): raise ValidationError("review:date-invalid")
        return self._review(grant,"monthly_review","monthly",period_end,(period_end-period_end.replace(day=1)).days+1,tasks,goals,schedule)
    def _review(self,grant,operation,kind,period_end,days,tasks,goals,schedule):
        approved,now=self._grant(grant,operation)
        if not isinstance(period_end,date): raise ValidationError("review:date-invalid")
        end=datetime.combine(period_end+timedelta(days=1),time.min,timezone.utc); start=end-timedelta(days=days)
        if days>approved.max_horizon_days or abs((period_end-now.date()).days)>approved.max_horizon_days: raise AuthorizationError("horizon:exceeded")
        tasks=validate_items(tasks,Task,approved,"tasks"); goals=validate_items(goals,Goal,approved,"goals"); schedule=validate_items(schedule,ScheduleItem,approved,"schedule")
        completed=tuple(sorted(x.id for x in tasks if x.status=="completed")); overdue=tuple(sorted(x.id for x in tasks if x.status not in {"completed","cancelled"} and x.due_at and parse_time(x.due_at)<end)); blocked=tuple(sorted(x.id for x in tasks if x.status=="blocked"))
        minutes=sum(int((parse_time(x.end_at)-parse_time(x.start_at)).total_seconds()//60) for x in schedule if start<=parse_time(x.start_at)<end)
        progress=round(sum(x.progress for x in goals)/len(goals),4) if goals else 0.0
        metrics=MappingProxyType({"completed_tasks":len(completed),"open_tasks":sum(x.status in {"open","in_progress","blocked"} for x in tasks),"overdue_tasks":len(overdue),"scheduled_minutes":minutes,"average_goal_progress":progress})
        return Review(kind,_utc(start),_utc(end),_utc(now),metrics,completed,tuple(sorted(set(overdue+blocked))))

    def reminder_support(self,grant,*,reminders=(),horizon_days=7):
        approved,now=self._grant(grant,"reminder_support")
        if not isinstance(horizon_days,int) or not 0<=horizon_days<=approved.max_horizon_days: raise AuthorizationError("horizon:exceeded")
        reminders=validate_items(reminders,Reminder,approved,"reminders"); end=now+timedelta(days=horizon_days); ordered=sorted(reminders,key=lambda x:(parse_time(x.remind_at),x.id))
        due=tuple(x.id for x in ordered if not x.acknowledged and parse_time(x.remind_at)<=now); upcoming=tuple(x.id for x in ordered if not x.acknowledged and now<parse_time(x.remind_at)<=end)
        return Briefing("reminder-view",_utc(now),_utc(end),_utc(now),MappingProxyType({"due":due,"upcoming":upcoming}))

    @staticmethod
    def _scores(tasks,now):
        values=[]
        for item in tasks:
            if item.status in {"completed","cancelled"}: continue
            score=item.importance*20; reasons=[f"importance:{item.importance}"]
            if item.status=="blocked": score+=10; reasons.append("blocked")
            if item.due_at:
                hours=(parse_time(item.due_at)-now).total_seconds()/3600
                if hours<0: score+=40; reasons.append("overdue")
                elif hours<=24: score+=30; reasons.append("due-within-24h")
                elif hours<=168: score+=15; reasons.append("due-within-7d")
            if item.effort_minutes<=30: score+=5; reasons.append("short-effort")
            values.append((score,item.id,tuple(reasons)))
        return sorted(values,key=lambda x:(-x[0],x[1]))
    def priority_management(self,grant,*,tasks=()):
        approved,now=self._grant(grant,"priority_management"); scored=self._scores(validate_items(tasks,Task,approved,"tasks"),now)
        return PriorityPlan(_utc(now),tuple(PriorityItem(item_id,rank,score,reasons) for rank,(score,item_id,reasons) in enumerate(scored,1)))
    @staticmethod
    def _conflicts(schedule: Sequence[ScheduleItem]):
        ordered=sorted(schedule,key=lambda x:(parse_time(x.start_at),x.id)); ids=set()
        for index,left in enumerate(ordered):
            for right in ordered[index+1:]:
                if parse_time(right.start_at)>=parse_time(left.end_at): break
                ids.update((left.id,right.id))
        return tuple(sorted(ids))
    def recommendation(self,grant,*,tasks=(),schedule=()):
        approved,now=self._grant(grant,"recommendation"); tasks=validate_items(tasks,Task,approved,"tasks"); schedule=validate_items(schedule,ScheduleItem,approved,"schedule"); recs=[]
        overdue=tuple(sorted(x.id for x in tasks if x.status not in {"completed","cancelled"} and x.due_at and parse_time(x.due_at)<now))
        if overdue: recs.append(Recommendation("resolve-overdue","Review overdue commitments","Overdue caller-supplied tasks may need renegotiation or completion.",overdue,1.0))
        scored=self._scores(tasks,now)
        if scored: recs.append(Recommendation("protect-focus","Protect time for the highest-ranked task","The score combines explicit importance, due time, status, and effort.",(scored[0][1],),0.8))
        conflicts=self._conflicts(schedule)
        if conflicts: recs.append(Recommendation("resolve-conflicts","Resolve overlapping schedule items","Caller-supplied schedule intervals overlap.",conflicts,1.0))
        return RecommendationSet(_utc(now),tuple(recs))

    def decision_support(self,grant,*,criteria: Mapping[str,float],options):
        approved,now=self._grant(grant,"decision_support")
        if not isinstance(criteria,Mapping) or not criteria or len(criteria)>20: raise ValidationError("decision:criteria-invalid")
        weights={}
        for key,value in criteria.items():
            name=text(key,"decision:criterion",100)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or value<=0 or value>100: raise ValidationError("decision:weight-invalid")
            weights[name]=float(value)
        options=validate_items(options,DecisionOption,approved,"options")
        if len(options)<2 or any(set(x.scores)!=set(weights) for x in options): raise ValidationError("decision:options-invalid")
        total=sum(weights.values()); scores={x.id:round(sum(float(x.scores[k])*weights[k] for k in weights)/total,6) for x in options}
        ranking=tuple(sorted(scores,key=lambda key:(-scores[key],key))); tradeoffs=MappingProxyType({x.id:tuple(sorted(k for k,v in x.scores.items() if v<0.5)) for x in options})
        return DecisionAnalysis(_utc(now),ranking,MappingProxyType(scores),tradeoffs)
    def personal_assistance(self,grant,objective,*,tasks=()):
        approved,now=self._grant(grant,"personal_assistance"); objective=text(objective,"assistance:objective",500); tasks=validate_items(tasks,Task,approved,"tasks")
        steps=tuple(AssistanceStep(index,item_id,f"Prepare and review task {item_id}",True) for index,(_,item_id,_) in enumerate(self._scores(tasks,now),1))
        return AssistancePlan(_utc(now),objective,steps)
    def context_support(self,grant,query,*,context=()):
        approved,_=self._grant(grant,"context_support"); original=text(query,"context:query",200); tokens=tuple(original.casefold().split()); context=validate_items(context,ContextItem,approved,"context")
        matched=tuple(x for x in sorted(context,key=lambda x:x.id) if all(token in x.content.casefold() for token in tokens))
        return ContextResult(original,tuple(x.id for x in matched),matched)
    def scheduling_support(self,grant,*,window_start,window_end,duration_minutes,schedule=(),max_proposals=5):
        approved,now=self._grant(grant,"scheduling_support"); start,end=parse_time(window_start),parse_time(window_end)
        if end<=start or end-start>timedelta(days=approved.max_horizon_days): raise AuthorizationError("horizon:exceeded")
        if not isinstance(duration_minutes,int) or not 1<=duration_minutes<=1440 or not isinstance(max_proposals,int) or not 1<=max_proposals<=20: raise ValidationError("schedule:request-invalid")
        schedule=validate_items(schedule,ScheduleItem,approved,"schedule"); busy=sorted((max(start,parse_time(x.start_at)),min(end,parse_time(x.end_at))) for x in schedule if parse_time(x.end_at)>start and parse_time(x.start_at)<end)
        proposals=[]; cursor=start; duration=timedelta(minutes=duration_minutes)
        for busy_start,busy_end in busy:
            if busy_start-cursor>=duration and len(proposals)<max_proposals: proposals.append((_utc(cursor),_utc(cursor+duration)))
            cursor=max(cursor,busy_end)
        if end-cursor>=duration and len(proposals)<max_proposals: proposals.append((_utc(cursor),_utc(cursor+duration)))
        return SchedulePlan(_utc(now),duration_minutes,tuple(proposals),self._conflicts(schedule))
