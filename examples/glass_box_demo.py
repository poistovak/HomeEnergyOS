from pathlib import Path

from heos.demo import render_report, run_demo, write_artifacts

run = run_demo()
print(render_report(run.result), end="")
write_artifacts(run, Path("glass-box-output"))
