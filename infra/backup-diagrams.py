#!/usr/bin/env python3
"""Private local PostgreSQL backups; no credentials on the command line."""
import os,subprocess
from pathlib import Path
from datetime import datetime,timezone
os.umask(0o077)
folder=Path('/home/mip/backups/koodaria-diagrams');folder.mkdir(mode=0o700,exist_ok=True)
filename=folder/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.dump')
temporary=filename.with_suffix('.partial')
with temporary.open('xb') as f:
    result=subprocess.run(['podman','exec','koodaria-diagrams-db','pg_dump','-U','koodaria_owner','-d','koodaria_diagrams','-Fc'],stdout=f)
if result.returncode:
    temporary.unlink(missing_ok=True);raise SystemExit(result.returncode)
temporary.replace(filename)
# Only backups produced by this script; retain the newest fourteen successful dumps.
for old in sorted(folder.glob('????????T??????Z.dump'),reverse=True)[14:]:old.unlink()
print('Diagram database backup completed.')
