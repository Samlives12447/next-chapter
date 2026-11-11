"""Fetch teaching jobs from the DfE Teaching Vacancies open API and keep the
full-time teaching / leadership jobs within 20 miles of home. Writes data/jobs.json.
Data: Teaching Vacancies API, Open Government Licence v3."""
import json, math, re, time, urllib.request, datetime, os
HOME = (50.8619, -0.1110)          # Coldean, Brighton (area centre)
RADIUS = 20
KEEP = re.compile(r"teacher|leader|head|sendco|senco", re.I)
UA = {"User-Agent": "next-chapter-jobs/1.0 (personal job list)", "Accept": "application/json"}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "postcodes.json")

def get(url, body=None):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, data=body, headers={**UA, **({"Content-Type": "application/json"} if body else {})})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:
            print("retry", url, e); time.sleep(3 * (attempt + 1))
    raise SystemExit("could not fetch " + url)

def miles(a, b):
    R = 3958.8; p1, p2 = map(math.radians, (a[0], b[0])); dl = math.radians(b[1] - a[1])
    return 2 * R * math.asin(math.sqrt(math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))

jobs, page = [], 1
while True:
    d = get(f"https://teaching-vacancies.service.gov.uk/api/v1/jobs.json?page={page}")
    jobs += d["data"]
    if not d["links"].get("next"): break
    page += 1; time.sleep(0.4)
print("fetched", len(jobs))

cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
def loc(j):
    l = j.get("jobLocation")
    if isinstance(l, list): l = l[0] if l else None
    return (l or {}).get("address") or {}
def pc(j):
    return (loc(j).get("postalCode") or "").upper().strip()
cands = [j for j in jobs if KEEP.search(str(j.get("occupationalCategory"))) and "FULL_TIME" in (j.get("employmentType") or [])]
need = sorted({pc(j) for j in cands if pc(j) and pc(j) not in cache})
for i in range(0, len(need), 100):
    r = get("https://api.postcodes.io/postcodes", json.dumps({"postcodes": need[i:i + 100]}).encode())
    for x in r["result"]:
        cache[x["query"]] = [x["result"]["latitude"], x["result"]["longitude"]] if x["result"] else None
    time.sleep(0.3)
json.dump(cache, open(CACHE, "w"))

PRIMARY = re.compile(r"primary|infant|junior|first school|prep|nursery|c of e school|cofe school|ce school", re.I)
SCHOOLS = os.path.join(ROOT, "data", "schools.json")
known = {re.sub(r"^the ", "", x["name"].lower()) for x in json.load(open(SCHOOLS))} if os.path.exists(SCHOOLS) else set()
out, seen = [], set()
for j in cands:
    key = (j["title"].strip().lower(), (j.get("hiringOrganization") or {}).get("name", ""))
    if key in seen: continue
    seen.add(key)
    ll = cache.get(pc(j))
    if not ll: continue
    m = miles(HOME, ll)
    if m > RADIUS: continue
    org = j.get("hiringOrganization") or {}
    addr = loc(j)
    pay = (((j.get("baseSalary") or {}).get("value") or {}).get("value")) or ""
    out.append({
        "title": j["title"].strip(), "school": org.get("name", "").strip(), "town": addr.get("addressLocality") or "",
        "lat": round(ll[0], 4), "lon": round(ll[1], 4), "miles": round(m, 1),
        "pay": re.sub(r"\s+", " ", str(pay)).strip()[:140], "posted": j.get("datePosted"),
        "closes": (j.get("validThrough") or "")[:16], "url": j["url"],
        "kind": "lead" if re.search(r"leader|head|sendco", str(j.get("occupationalCategory")), re.I) else "teach",
        "primary": bool(PRIMARY.search(org.get("name", ""))) or re.sub(r"^the ", "", org.get("name", "").strip().lower()) in known, "website": org.get("sameAs") or "",
    })
out.sort(key=lambda x: (x["posted"] or ""), reverse=True)
json.dump({"updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes"), "jobs": out},
          open(os.path.join(ROOT, "data", "jobs.json"), "w"), indent=0, ensure_ascii=False)
print("kept", len(out))
