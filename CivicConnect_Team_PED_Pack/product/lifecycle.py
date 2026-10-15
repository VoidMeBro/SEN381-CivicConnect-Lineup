"""Executable CivicConnect FR-13/05/08 initial service path.

The caller supplies an authenticated actor ID; the service always reloads role,
active state and department. The CLI demo uses synthetic accounts, not a login
system. Python/SQLite are the reference slice runtime, not a whole-app stack.
"""
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

class Forbidden(ValueError): pass
class Conflict(ValueError): pass
class InvalidTransition(ValueError): pass

def timestamp(value):
    try:
        parsed=datetime.fromisoformat(value)
        if parsed.tzinfo is None: raise ValueError('Timezone required')
        return parsed.astimezone(timezone.utc)
    except (TypeError,ValueError) as exc:
        raise InvalidTransition('A valid timezone-aware timestamp is required') from exc

class LifecyclePolicy:
    """FR-13: one explicit transition policy; no infrastructure dependencies."""
    NEXT={'Submitted':{'Accepted','Rejected'},'Accepted':{'In Progress'},
          'In Progress':{'Resolved'},'Resolved':{'Closed'},'Closed':set(),'Rejected':set()}

    @classmethod
    def check(cls, request, target, explanation, assignee, due_at):
        if target not in cls.NEXT.get(request['status'],set()):
            raise InvalidTransition('Transition is not permitted')
        if not isinstance(explanation,str): raise InvalidTransition('Explanation must be text')
        if target in {'Rejected','Resolved'} and not explanation.strip():
            raise InvalidTransition('Rejection and resolution require an explanation')
        if target=='Accepted':
            if not assignee or not due_at: raise InvalidTransition('Acceptance requires an assignee and due time')
            if timestamp(due_at)<=timestamp(request['submitted_at']):
                raise InvalidTransition('Due time must be later than submission')

class SqliteLifecycleStore:
    """Owns one transaction covering current state and mandatory history."""
    def __init__(self,path):
        self.path=str(path)

    def connect(self):
        connection=sqlite3.connect(self.path,timeout=5)
        connection.row_factory=sqlite3.Row
        connection.execute('PRAGMA foreign_keys=ON')
        return connection

    def initialise(self):
        connection=self.connect()
        try:
            connection.executescript(Path(__file__).with_name('schema.sql').read_text(encoding='utf-8'))
        finally: connection.close()

    def change(self,actor_id,reference,target,expected_version,explanation,assignee,due_at,now):
        connection=self.connect()
        try:
            # Serialise writes in this small reference store; the explicit version
            # predicate still detects stale commands instead of overwriting work.
            connection.execute('BEGIN IMMEDIATE')
            actor=connection.execute('SELECT * FROM accounts WHERE id=?',(actor_id,)).fetchone()
            request=connection.execute('SELECT * FROM requests WHERE reference=?',(reference,)).fetchone()
            if (actor is None or not actor['active'] or actor['role']!='Staff'
                    or request is None or actor['department']!=request['department']):
                raise Forbidden('Request is not accessible')
            if type(expected_version) is not int or request['version']!=expected_version:
                raise Conflict('Request changed; reload before retrying')
            LifecyclePolicy.check(request,target,explanation,assignee,due_at)
            if target=='Accepted':
                chosen=connection.execute('SELECT * FROM accounts WHERE id=?',(assignee,)).fetchone()
                if (chosen is None or not chosen['active'] or chosen['role']!='Staff'
                        or chosen['department']!=request['department']):
                    raise InvalidTransition('Assignee must be active staff in the request department')
            else:
                if assignee is not None or due_at is not None:
                    raise InvalidTransition('Assignment and due time are set at acceptance in this path')
                assignee,due_at=request['assignee'],request['due_at']
            at=timestamp(now)
            if at<timestamp(request['submitted_at']):
                raise InvalidTransition('Event time cannot precede submission')
            feedback=explanation.strip() or 'Request status changed to '+target+'.'
            updated=connection.execute('UPDATE requests SET status=?,assignee=?,due_at=?,version=version+1 WHERE reference=? AND version=?',
                                       (target,assignee,due_at,reference,expected_version))
            if updated.rowcount!=1: raise Conflict('Request changed; reload before retrying')
            connection.execute('INSERT INTO lifecycle_events(reference,from_status,to_status,actor,occurred_at,explanation,version) VALUES(?,?,?,?,?,?,?)',
                               (reference,request['status'],target,actor_id,at.isoformat(),feedback,expected_version+1))
            connection.commit()
            return {'reference':reference,'status':target,'version':expected_version+1,'explanation':feedback}
        except Exception:
            connection.rollback()
            raise
        finally: connection.close()

    def history(self,actor_id,reference):
        connection=self.connect()
        try:
            # Account, current status and history come from one consistent read
            # snapshot even if another writer commits between these queries.
            connection.execute('BEGIN')
            actor=connection.execute('SELECT * FROM accounts WHERE id=?',(actor_id,)).fetchone()
            request=connection.execute('SELECT * FROM requests WHERE reference=?',(reference,)).fetchone()
            if (actor is None or not actor['active'] or actor['role']!='Citizen'
                    or request is None or request['citizen_id']!=actor_id):
                raise Forbidden('Request is not accessible')
            events=connection.execute('SELECT from_status,to_status,actor,occurred_at,explanation,version FROM lifecycle_events WHERE reference=? ORDER BY id',(reference,)).fetchall()
            return {'reference':reference,'status':request['status'],'version':request['version'],
                    'events':[dict(row) for row in events]}
        finally: connection.close()

class RequestLifecycleCoordinator:
    """Stable in-process contract delegating transaction details to the store."""
    def __init__(self,store,clock=None):
        self.store=store
        self.clock=clock or (lambda:datetime.now(timezone.utc).isoformat())

    def transition(self,actor_id,reference,target,expected_version,explanation='',assignee=None,due_at=None):
        return self.store.change(actor_id,reference,target,expected_version,explanation,assignee,due_at,self.clock())

def seed_demo(store):
    """Insert a new synthetic fixture; never operates on a real project database."""
    connection=store.connect()
    try:
        with connection:
            connection.executemany('INSERT INTO accounts VALUES(?,?,?,?)',[
                ('citizen-a','Citizen','',1),('citizen-b','Citizen','',1),
                ('staff-a','Staff','Water',1),('staff-b','Staff','Roads',1),
                ('inactive','Staff','Water',0)])
            connection.execute('INSERT INTO requests(reference,citizen_id,department,status,submitted_at) VALUES(?,?,?,?,?)',
                               ('CC-DEMO-001','citizen-a','Water','Submitted','2026-09-24T08:00:00+00:00'))
    finally: connection.close()
