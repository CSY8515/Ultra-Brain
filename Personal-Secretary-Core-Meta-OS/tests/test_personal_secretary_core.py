from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import date,datetime,timezone
from personal_secretary_core import AuthorizationError,PersonalSecretaryCore,ValidationError
from personal_secretary_core.models import ContextItem,DecisionOption,Goal,Reminder,ScheduleItem,SecretaryGrant,Task
NOW=datetime(2026,8,1,12,tzinfo=timezone.utc)
OPS=("daily_briefing","weekly_review","monthly_review","reminder_support","recommendation","priority_management","decision_support","personal_assistance","context_support","scheduling_support")
def grant(**changes):
    values=dict(id="grant-1",user_id="user-1",approved=True,safety_decision_id="safety-1",valid_from="2026-07-01T00:00:00Z",expires_at="2026-09-01T00:00:00Z",allowed_operations=OPS,allowed_context_categories=("general","work","health"),max_items=100,max_horizon_days=60,allow_sensitive_context=False); values.update(changes); return SecretaryGrant(**values)
def task(identifier="task-1",**changes):
    values=dict(id=identifier,title="Prepare report",status="open",due_at="2026-08-01T18:00:00Z",importance=5,effort_minutes=60,created_at="2026-07-30T00:00:00Z",category="work",sensitive=False); values.update(changes); return Task(**values)
class CoreTests(unittest.TestCase):
    def setUp(self): self.core=PersonalSecretaryCore(clock=lambda:NOW)
    def test_daily_briefing(self):
        result=self.core.daily_briefing(grant(),date(2026,8,1),tasks=[task()],schedule=[ScheduleItem("meet","Planning","2026-08-01T13:00:00Z","2026-08-01T14:00:00Z","work")],reminders=[Reminder("rem","Check","2026-08-01T11:00:00Z")],context=[ContextItem("ctx","work","Finance section","2026-08-01T10:00:00Z","user")])
        self.assertEqual(result.sections["due_today"],("task-1",)); self.assertEqual(result.sections["schedule"],("meet",)); self.assertEqual(result.sections["reminders"],("rem",))
    def test_reviews(self):
        tasks=[task("done",status="completed"),task("late",due_at="2026-07-31T10:00:00Z",status="blocked")]; goals=[Goal("goal","Ship","monthly","in_progress",0.5)]; schedule=[ScheduleItem("meet","Meeting","2026-08-01T09:00:00Z","2026-08-01T10:00:00Z","work")]
        weekly=self.core.weekly_review(grant(),date(2026,8,1),tasks=tasks,goals=goals,schedule=schedule); monthly=self.core.monthly_review(grant(),date(2026,8,1),tasks=tasks,goals=goals,schedule=schedule)
        self.assertEqual(weekly.metrics["completed_tasks"],1); self.assertEqual(weekly.metrics["scheduled_minutes"],60); self.assertEqual(weekly.attention,("late",)); self.assertEqual(monthly.kind,"monthly")
    def test_reminders_priorities_recommendations(self):
        view=self.core.reminder_support(grant(),reminders=[Reminder("due","Due","2026-08-01T10:00:00Z"),Reminder("next","Next","2026-08-02T10:00:00Z")]); self.assertEqual(view.sections,{"due":("due",),"upcoming":("next",)})
        plan=self.core.priority_management(grant(),tasks=[task("later",importance=3,due_at="2026-08-10T00:00:00Z"),task("overdue",due_at="2026-07-31T00:00:00Z")]); self.assertEqual(plan.items[0].task_id,"overdue"); self.assertIn("overdue",plan.items[0].reasons)
        schedule=[ScheduleItem("a","A","2026-08-01T13:00:00Z","2026-08-01T15:00:00Z","work"),ScheduleItem("b","B","2026-08-01T14:00:00Z","2026-08-01T16:00:00Z","work")]
        recs=self.core.recommendation(grant(),tasks=[task("late",due_at="2026-07-31T00:00:00Z")],schedule=schedule); self.assertEqual(recs.recommendations[0].evidence_ids,("late",)); self.assertTrue(all(x.requires_confirmation for x in recs.recommendations))
    def test_decision_assistance_context(self):
        options=[DecisionOption("a","A",{"impact":0.9,"cost":0.3}),DecisionOption("b","B",{"impact":0.6,"cost":0.9})]; result=self.core.decision_support(grant(),criteria={"impact":2,"cost":1},options=options)
        self.assertEqual(result.ranking,("a","b")); self.assertEqual(result.decision_owner,"user"); self.assertEqual(result.tradeoffs["a"],("cost",))
        assistance=self.core.personal_assistance(grant(),"Prepare release",tasks=[task()]); context=self.core.context_support(grant(),"finance section",context=[ContextItem("ctx","work","Needs finance section","2026-08-01T10:00:00Z","user-note")])
        self.assertEqual(assistance.status,"proposal"); self.assertTrue(assistance.steps[0].requires_confirmation); self.assertEqual(context.matched_ids,("ctx",)); self.assertEqual(context.matches[0].source,"user-note")
    def test_scheduling(self):
        schedule=[ScheduleItem("a","A","2026-08-01T13:00:00Z","2026-08-01T16:00:00Z","work"),ScheduleItem("b","B","2026-08-01T14:00:00Z","2026-08-01T15:00:00Z","work"),ScheduleItem("c","C","2026-08-01T15:00:00Z","2026-08-01T15:30:00Z","work")]
        result=self.core.scheduling_support(grant(),window_start="2026-08-01T12:00:00Z",window_end="2026-08-01T18:00:00Z",duration_minutes=60,schedule=schedule)
        self.assertEqual(result.proposed_slots,(("2026-08-01T12:00:00Z","2026-08-01T13:00:00Z"),("2026-08-01T16:00:00Z","2026-08-01T17:00:00Z"))); self.assertEqual(result.conflict_ids,("a","b","c")); self.assertEqual(result.status,"proposal")
    def test_fail_closed_controls(self):
        with self.assertRaises(AuthorizationError): self.core.priority_management(grant(allowed_operations=("daily_briefing",)),tasks=[])
        with self.assertRaises(AuthorizationError): self.core.priority_management(grant(expires_at="2026-08-01T11:00:00Z"),tasks=[])
        with self.assertRaises(AuthorizationError): self.core.context_support(grant(),"private",context=[ContextItem("x","health","private","2026-08-01T10:00:00Z","user",True)])
        with self.assertRaises(AuthorizationError): self.core.priority_management(grant(),tasks=[task(category="finance")])
        with self.assertRaises(ValidationError): self.core.priority_management(grant(max_items=1),tasks=[task("a"),task("b")])
        with self.assertRaises(ValidationError): self.core.priority_management(grant(),tasks=[task("same"),task("same")])
        with self.assertRaises(ValidationError): self.core.priority_management(grant(),tasks=[{"id":"x","unexpected":True}])
    def test_immutable_serializable(self):
        item=task(); option=DecisionOption("x","X",{"impact":0.5})
        with self.assertRaises(FrozenInstanceError): item.title="changed"
        with self.assertRaises(TypeError): option.scores["impact"]=1.0
        self.assertEqual(item.to_dict()["id"],"task-1")
if __name__=="__main__": unittest.main()
