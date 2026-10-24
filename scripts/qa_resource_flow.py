"""Compatibility entrypoint: current React Flow QA uses the online diagram API.
Requires the disposable PostgreSQL/browser harness described in deployment.md.
"""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('qa_diagrams_online.py')),run_name='__main__')
