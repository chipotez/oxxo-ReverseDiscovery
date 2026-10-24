"""Application entitlements and verified identity directory. Unknown users fail closed."""
from flask import session

def sync_identity(identity):
    from diagrams import connection
    sub=identity['sub'];email=identity.get('email','').strip().lower()
    verified=identity.get('email_verified') is True
    with connection(sub) as conn:
        conn.execute('INSERT INTO workspace_principals(subject,email,email_verified,display_name) VALUES(%s,%s,%s,%s) ON CONFLICT(subject) DO UPDATE SET email=EXCLUDED.email,email_verified=EXCLUDED.email_verified,display_name=EXCLUDED.display_name,last_login_at=now()',
                     (sub,email,verified,identity.get('name','')[:200]))
        conn.execute('SELECT activate_diagram_invites()')

def is_member(conn):
    return conn.execute('SELECT workspace_member() AS allowed').fetchone()['allowed']

def capabilities(conn):
    member=is_member(conn)
    return dict(tier='member' if member else 'guest',can_create=member,can_share=member)
