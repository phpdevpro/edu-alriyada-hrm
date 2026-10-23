"""Static check of every file in the app: Python compiles (and pyflakes, if installed, finds no undefined
names), every JS parses (node --check, also the inline scripts of the www pages), every JSON loads, and the
Arabic translations keep their placeholders. No site needed.

    python3 tests/checks/files.py
"""
import csv, glob, json, os, re, subprocess, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(ROOT)
files = subprocess.run(["git", "ls-files", "-z"], capture_output=True, text=True).stdout.split("\0")
files = [f for f in files if f and os.path.exists(f)]
problems = []


def run(cmd, **kw):
	return subprocess.run(cmd, capture_output=True, text=True, **kw)


py = [f for f in files if f.endswith(".py")]
for f in py:
	r = run([sys.executable, "-m", "py_compile", f])
	if r.returncode:
		problems.append(f"python does not compile: {f}: {r.stderr.strip()[-200:]}")
try:
	import pyflakes  # noqa: F401
	# tests/e2e/qa_* get `frappe` from fx.py
	r = run([sys.executable, "-m", "pyflakes"] + [f for f in py if not os.path.basename(f).startswith("qa_")])
	for line in r.stdout.splitlines():
		if "undefined name" in line or "syntax" in line.lower():
			problems.append(f"pyflakes: {line}")
except ImportError:
	print("(pyflakes not installed: undefined-name check skipped)")

js = [f for f in files if f.endswith(".js")]
for f in js:
	src = open(f, encoding="utf-8").read()
	module = re.search(r"^\s*(import|export) ", src, re.M)
	r = run(["node", "--check", "--input-type=module"] if module else ["node", "--check", f], input=src if module else None)
	if r.returncode:
		problems.append(f"js does not parse: {f}: {r.stderr.strip()[:200]}")
for f in [f for f in files if f.endswith(".html")]:
	src = open(f, encoding="utf-8").read()
	for i, block in enumerate(re.findall(r"<script(?![^>]*src=)[^>]*>(.*?)</script>", src, re.S)):
		block = re.sub(r"\{%.*?%\}", "", re.sub(r"\{\{.*?\}\}", "X", block, flags=re.S), flags=re.S)
		with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as t:
			t.write(block)
		r = run(["node", "--check", t.name])
		os.unlink(t.name)
		if r.returncode:
			problems.append(f"inline script {i} in {f} does not parse: {r.stderr.strip()[:200]}")

for f in [f for f in files if f.endswith(".json")]:
	try:
		json.load(open(f, encoding="utf-8"))
	except Exception as e:
		problems.append(f"json does not load: {f}: {e}")

ph = lambda s: sorted(re.findall(r"\{\d+\}", s))
seen = set()
for path in glob.glob("medical_hrms/translations/*.csv"):
	for n, row in enumerate(csv.reader(open(path, encoding="utf-8")), 1):
		if not row:
			continue
		if len(row) < 2 or not row[1].strip():
			problems.append(f"{path}:{n}: no translation for {row[0][:50]!r}")
		elif ph(row[0]) != ph(row[1]):
			problems.append(f"{path}:{n}: placeholders differ: {row[0][:50]!r}")
		if (path, row[0]) in seen:
			problems.append(f"{path}:{n}: duplicate {row[0][:50]!r}")
		seen.add((path, row[0]))

odd = [f for f in files if " copy." in f or f.endswith(":Zone.Identifier")]
problems += [f"stray file: {f}" for f in odd]

print(f"python {len(py)}, js {len(js)}, json {len([f for f in files if f.endswith('.json')])}, translations {len(seen)}")
print("PROBLEMS:", len(problems))
print("\n".join(problems))
sys.exit(1 if problems else 0)
