import re, subprocess, os
c = open(r"D:\algs player data\docs\index.html", "r", encoding="utf-8").read()
js = re.search(r"<script>(.*?)</script>", c, re.DOTALL).group(1)
open("docs/_t.js", "w").write(js)
r = subprocess.run(["node", "--check", "docs/_t.js"], capture_output=True, text=True)
os.remove("docs/_t.js")
if r.returncode != 0:
    print("JS ERROR:", r.stderr[:300])
else:
    print("JS syntax: OK")

# Check if data-col is properly generated  
if "data-col" in js:
    print("data-col: YES")
else:
    print("data-col: MISSING")

# Sample onclick
import re as r2
m = r2.search(r'sortPlayers\([^)]+\)', js)
if m:
    print("onclick:", m.group()[:80])
