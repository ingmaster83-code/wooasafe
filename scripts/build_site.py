# -*- coding: utf-8 -*-
"""우아안전 정적 사이트 생성기 → _site/.  사용: python scripts/build_site.py"""
import sys, json, re, shutil, time, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from common import *

FIRE = json.loads((ROOT / "data" / "fire.json").read_text(encoding="utf-8"))
POL = json.loads((ROOT / "data" / "police.json").read_text(encoding="utf-8"))
CHI = json.loads((ROOT / "data" / "chian.json").read_text(encoding="utf-8"))
ASOF_F, ASOF_P = "2026년 7월 1일", "2025년 12월 31일"

def table(heads, rows, num=()):
    th = "".join('<th%s>%s</th>' % (' class="num"' if i in num else "", h) for i, h in enumerate(heads))
    body = "".join("<tr>%s</tr>" % "".join('<td%s>%s</td>' % (' class="num"' if i in num else "", v) for i, v in enumerate(r)) for r in rows)
    return '<div class="tbl-wrap"><table class="tbl"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (th, body)

def chips(items): return '<div class="chips">%s</div>' % "".join('<a class="chip" href="%s">%s</a>' % (u, esc(t)) for t, u in items)
def sl(s): return re.sub(r"[^0-9A-Za-z가-힣]+", "-", s).strip("-") or "x"
SIDO_ORDER = ["서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시", "대전광역시", "울산광역시", "세종특별자치시", "경기도", "강원특별자치도", "충청북도", "충청남도", "전북특별자치도", "전라남도", "전남광주통합특별시", "경상북도", "경상남도", "제주특별자치도"]
SIDOS = [s for s in SIDO_ORDER if any(d["sido"] == s for d in FIRE + POL)]
URGENT = "긴급 상황에서는 이 사이트를 보기 전에 먼저 119(화재·구급)나 112(범죄·긴급)로 신고하세요."
NOTE_F = "119안전센터 현황은 소방청 공공데이터(%s 기준)를 정리한 참고용이며 위치·전화번호가 바뀔 수 있습니다. %s" % (ASOF_F, URGENT)
NOTE_P = "지구대·파출소 현황은 경찰청 공공데이터(%s 기준)를 정리한 참고용이며 위치가 바뀔 수 있고 전화번호는 데이터에 없습니다. %s" % (ASOF_P, URGENT)

# 슬러그
used = set()
for d in FIRE:
    s = sl(d["name"]); base = s; n = 2
    while (d["sido"], d["sg"], s) in used: s = "%s-%d" % (base, n); n += 1
    used.add((d["sido"], d["sg"], s)); d["slug"] = s; d["path"] = "/fire/%s/%s/%s/" % (d["sido"], d["sg"], s)
used = set()
for d in POL:
    s = sl(d["name"] + d["kind"]); base = s; n = 2
    while (d["sido"], d["sg"], s) in used: s = "%s-%s" % (base, sl(d["office"])) if n == 2 else "%s-%d" % (base, n); n += 1
    used.add((d["sido"], d["sg"], s)); d["slug"] = s; d["path"] = "/police/%s/%s/%s/" % (d["sido"], d["sg"], s)
FIRE_BY_SG = collections.defaultdict(list); POL_BY_SG = collections.defaultdict(list); BY_STATION = collections.defaultdict(list); BY_OFFICE = collections.defaultdict(list); CHI_BY_OFFICE = collections.defaultdict(list)
for d in FIRE: FIRE_BY_SG[(d["sido"], d["sg"])].append(d); BY_STATION[(d["sido"], d["station"])].append(d)
for d in POL: POL_BY_SG[(d["sido"], d["sg"])].append(d); BY_OFFICE[(d["hq"], d["office"])].append(d)
for d in CHI: CHI_BY_OFFICE[(d["hq"], d["office"])].append(d)
SG_KEYS = sorted(set(FIRE_BY_SG) | set(POL_BY_SG))
FH = ["119안전센터", "소방서", "시군구", "전화번호"]
PH = ["지구대·파출소", "구분", "관할 경찰서", "시군구"]
def frows(lst): return [['<a href="%s">%s</a>' % (d["path"], esc(d["name"])), esc(d["station"]), esc(d["sg"]), esc(d["tel"])] for d in lst]
def prows(lst): return [['<a href="%s">%s</a>' % (d["path"], esc(d["name"] + d["kind"] if not d["name"].endswith(d["kind"]) else d["name"])), d["kind"], esc(d["office"]), esc(d["sg"])] for d in lst]

# ───────────────────────── 119안전센터 ─────────────────────────
def page_fire(d):
    same = [x for x in FIRE_BY_SG[(d["sido"], d["sg"])] if x is not d][:8]; st = BY_STATION[(d["sido"], d["station"])]
    lead = (f"<p class=\"lead\"><b>{esc(d['name'])}</b>은(는) {esc(d['sido'])} {esc(d['sg'])}에 있는 <b>{esc(d['station'])}</b> 소속 119안전센터입니다. 주소는 {esc(d['addr'])}, 전화번호는 <b>{esc(d['tel'])}</b>입니다. "
            f"{esc(d['station'])}에는 119안전센터가 {len(st)}곳 있습니다. {URGENT}</p>")
    rows = [["119안전센터", esc(d["name"])], ["소방서", '<a href="/station/%s/%s/">%s</a>' % (d["sido"], sl(d["station"]), esc(d["station"]))], ["소방본부", esc(d["hq"])], ["주소", esc(d["addr"])], ["전화", '<a href="tel:%s">%s</a>' % (re.sub(r"[^0-9]", "", d["tel"]), esc(d["tel"]))]]
    if d["fax"]: rows.append(["팩스", esc(d["fax"])])
    nb = ('<h2 class="group-title">📍 %s의 다른 119안전센터</h2>' % esc(d["sg"]) + table(FH, frows(same))) if same else ""
    body = f"""
<div class="page-head"><h1>{esc(d['name'])} — {esc(d['sg'])} 119안전센터 전화번호·주소</h1><p>{esc(d['sido'])} {esc(d['sg'])} · {esc(d['station'])}</p></div>
{lead}
{ad()}
<h2 class="group-title">📋 기본 정보</h2>
{table(['항목', '내용'], rows)}
<h2 class="group-title">🚨 긴급 신고 안내</h2>
<p class="lead">화재·구조·구급은 <b>119</b>, 범죄·긴급 상황은 <b>112</b>로 신고하세요. 119안전센터 직통번호보다 119 신고가 가장 빠르게 출동으로 연결됩니다. 신고할 때는 정확한 주소(건물명)와 상황을 알려 주세요.</p>
{nb}
<p class="note">{NOTE_F}</p>
{chips([(d["sg"] + " 안전시설", "/region/%s/%s/" % (d["sido"], d["sg"])), (d["station"], "/station/%s/%s/" % (d["sido"], sl(d["station"]))), ("119 신고 요령", "/guide/119/"), ("심폐소생술", "/guide/cpr/")])}
"""
    faq = [(f"{d['name']} 전화번호는?", d["tel"]), (f"{d['name']}은(는) 어느 소방서 소속인가요?", f"{d['station']} 소속입니다."), ("긴급할 때도 안전센터로 전화하나요?", "아니요. 긴급 상황에서는 119로 신고하세요. 안전센터 직통번호는 일반 문의용입니다.")]
    write(d["path"], layout(d["path"], f"{d['name']} — {d['sg']} 119안전센터 전화번호·주소 ({d['station']})", f"{d['name']}({d['sido']} {d['sg']}, {d['station']}) 전화 {d['tel']}, 주소 {d['addr']}. 119 신고 안내.", body, faq,
          [("홈", "/"), ("119안전센터", "/fire/"), (d["sido"], "/region/%s/" % d["sido"]), (d["sg"], "/region/%s/%s/" % (d["sido"], d["sg"])), (d["name"], d["path"])]), "0.5")

def page_station(sido, station):
    lst = sorted(BY_STATION[(sido, station)], key=lambda x: (x["sg"], x["name"])); path = "/station/%s/%s/" % (sido, sl(station))
    sgs = sorted({d["sg"] for d in lst})
    body = f"""
<div class="page-head"><h1>{esc(station)} 119안전센터 {len(lst)}곳 — 전화번호·주소</h1><p>{esc(sido)} · {esc(', '.join(sgs))}</p></div>
<p class="lead"><b>{esc(station)}</b>({esc(sido)})에는 119안전센터가 {len(lst)}곳 있습니다. 안전센터 이름을 누르면 주소와 전화번호를 볼 수 있습니다. {URGENT}</p>
{ad()}
{table(FH, frows(lst))}
<p class="note">{NOTE_F}</p>
{chips([("119안전센터 전체", "/fire/"), ("119 신고 요령", "/guide/119/")])}
"""
    faq = [(f"{station}에는 119안전센터가 몇 곳 있나요?", f"공공데이터 기준 {len(lst)}곳입니다."), ("소방서와 119안전센터는 어떻게 다른가요?", "소방서가 관할 구역을 총괄하고 119안전센터는 현장 출동을 담당하는 지역 거점입니다.")]
    write(path, layout(path, f"{station}({sido}) 119안전센터 {len(lst)}곳 — 전화번호·주소 목록", f"{station}({sido}) 소속 119안전센터 {len(lst)}곳의 주소와 전화번호.", body, faq, [("홈", "/"), ("119안전센터", "/fire/"), (station, path)]), "0.5")

def hub_fire():
    by = collections.defaultdict(list)
    for (s, st), lst in BY_STATION.items(): by[s].append((st, len(lst)))
    secs = "".join('<h2 class="group-title">%s</h2>%s' % (esc(s), chips([("%s (%d)" % (st, c), "/station/%s/%s/" % (s, sl(st))) for st, c in sorted(by[s])])) for s in SIDOS if by.get(s))
    body = f"""
<div class="page-head"><h1>119안전센터 {len(FIRE):,}곳 — 소방서별 전화번호·주소</h1><p>소방청 공공데이터 · {ASOF_F} 기준</p></div>
<p class="lead">전국 119안전센터 {len(FIRE):,}곳을 소방서별로 정리했습니다. 소방서를 누르면 소속 안전센터의 주소와 전화번호를 볼 수 있습니다. {URGENT}</p>
{ad()}
{secs}
<p class="note">{NOTE_F}</p>
"""
    write("/fire/", layout("/fire/", f"119안전센터 {len(FIRE):,}곳 — 소방서별 전화번호·주소 목록", f"전국 119안전센터 {len(FIRE):,}곳을 소방서별로 정리. 주소·전화번호와 119 신고 안내.", body, [("전국 119안전센터는 몇 곳인가요?", f"공공데이터 기준 {len(FIRE):,}곳입니다."), ("119안전센터 전화번호는 어디서 찾나요?", "소방서를 선택한 뒤 안전센터 이름을 누르세요.")], [("홈", "/"), ("119안전센터", "/fire/")], coupang=True), "0.9")

# ───────────────────────── 지구대·파출소 ─────────────────────────
PN = collections.Counter()
def page_police(d):
    full = d["name"] if d["name"].endswith(d["kind"]) else d["name"] + d["kind"]
    off = BY_OFFICE[(d["hq"], d["office"])]; same = [x for x in POL_BY_SG[(d["sido"], d["sg"])] if x is not d][:8]
    chi = [c for c in CHI_BY_OFFICE[(d["hq"], d["office"])] if c["parent"] == d["name"]]
    lead = (f"<p class=\"lead\"><b>{esc(full)}</b>는 {esc(d['hq'])} <b>{esc(d['office'])}경찰서</b> 관할 {d['kind']}입니다. 주소는 {esc(d['addr'])}입니다. {esc(d['office'])}경찰서에는 지구대·파출소가 {len(off)}곳 있습니다. "
            f"{('이 ' + d['kind'] + ' 소속 치안센터는 ' + str(len(chi)) + '곳(' + ', '.join(esc(c['name']) for c in chi[:4]) + ')입니다. ') if chi else ''}범죄·긴급 상황은 <b>112</b>로 신고하세요.</p>")
    rows = [["관서", esc(full)], ["구분", d["kind"]], ["관할 경찰서", '<a href="/office/%s/%s/">%s경찰서</a>' % (sl(d["hq"]), sl(d["office"]), esc(d["office"]))], ["지방경찰청", esc(d["hq"])], ["주소", esc(d["addr"])], ["긴급 신고", "112"]]
    if chi: rows.append(["소속 치안센터", esc(", ".join(c["name"] + "(" + c["addr"] + ")" for c in chi))])
    nb = ('<h2 class="group-title">📍 %s의 다른 지구대·파출소</h2>' % esc(d["sg"]) + table(PH, prows(same))) if same else ""
    body = f"""
<div class="page-head"><h1>{esc(full)} — {esc(d['sg'])} {d['kind']} 위치·관할 {esc(d['office'])}경찰서</h1><p>{esc(d['sido'])} {esc(d['sg'])}</p></div>
{lead}
{ad()}
<h2 class="group-title">📋 기본 정보</h2>
{table(['항목', '내용'], rows)}
{nb}
<p class="note">{NOTE_P}</p>
{chips([(d["office"] + "경찰서 관할", "/office/%s/%s/" % (sl(d["hq"]), sl(d["office"]))), (d["sg"] + " 안전시설", "/region/%s/%s/" % (d["sido"], d["sg"])), ("112 신고 요령", "/guide/112/")])}
"""
    faq = [(f"{full}은(는) 어느 경찰서 소속인가요?", f"{d['hq']} {d['office']}경찰서 관할입니다."), (f"{full} 주소는?", d["addr"]), ("전화번호는 어디서 확인하나요?", "이 데이터에는 지구대·파출소 전화번호가 없습니다. 긴급 신고는 112, 일반 문의는 관할 경찰서 대표번호를 이용하세요.")]
    PN[(full, d["sg"], d["office"])] += 1
    sfx = (" (%d)" % PN[(full, d["sg"], d["office"])]) if PN[(full, d["sg"], d["office"])] > 1 else ""
    write(d["path"], layout(d["path"], f"{full}{sfx} — {d['sg']} {d['kind']} 위치·관할 경찰서 ({d['office']})", f"{full}({d['sido']} {d['sg']}) 주소 {d['addr']}, 관할 {d['office']}경찰서. 112 신고 안내.", body, faq,
          [("홈", "/"), ("지구대·파출소", "/police/"), (d["sido"], "/region/%s/" % d["sido"]), (d["sg"], "/region/%s/%s/" % (d["sido"], d["sg"])), (full, d["path"])]), "0.5")

def page_office(hq, office):
    lst = sorted(BY_OFFICE[(hq, office)], key=lambda x: (x["kind"], x["name"])); chi = CHI_BY_OFFICE.get((hq, office), []); path = "/office/%s/%s/" % (sl(hq), sl(office))
    kc = collections.Counter(d["kind"] for d in lst)
    crow = [[esc(c["name"]), esc(c["parent"] + c["kind"]), esc(c["addr"])] for c in chi]
    body = f"""
<div class="page-head"><h1>{esc(office)}경찰서 관할 지구대·파출소 {len(lst)}곳</h1><p>{esc(hq)} · {' · '.join('%s %d곳' % (k, c) for k, c in kc.items())}{(' · 치안센터 ' + str(len(chi)) + '곳') if chi else ''}</p></div>
<p class="lead"><b>{esc(office)}경찰서</b>({esc(hq)})는 지구대·파출소 {len(lst)}곳을 관할합니다({', '.join('%s %d곳' % (k, c) for k, c in kc.items())}). 이름을 누르면 주소와 관할을 볼 수 있습니다. 범죄·긴급 상황은 112로 신고하세요.</p>
{ad()}
{table(PH, prows(lst))}
{('<h2 class="group-title">🏠 치안센터</h2>' + table(['치안센터', '소속', '주소'], crow)) if chi else ''}
<p class="note">{NOTE_P}</p>
{chips([("지구대·파출소 전체", "/police/"), ("112 신고 요령", "/guide/112/")])}
"""
    faq = [(f"{office}경찰서 관할 지구대·파출소는 몇 곳인가요?", f"공공데이터 기준 {len(lst)}곳입니다."), ("지구대와 파출소의 차이는?", "지구대는 여러 파출소를 통합한 규모가 큰 치안 거점이고 파출소는 상대적으로 작은 단위입니다. 112 신고 출동은 양쪽 모두 담당합니다.")]
    write(path, layout(path, f"{office}경찰서 관할 지구대·파출소 {len(lst)}곳 목록", f"{office}경찰서({hq}) 관할 지구대·파출소 {len(lst)}곳과 치안센터 {len(chi)}곳 주소.", body, faq, [("홈", "/"), ("지구대·파출소", "/police/"), (office + "경찰서", path)]), "0.4")

def hub_police():
    by = collections.defaultdict(list)
    for (hq, off), lst in BY_OFFICE.items(): by[hq].append((off, len(lst)))
    secs = "".join('<h2 class="group-title">%s</h2>%s' % (esc(h), chips([("%s (%d)" % (o, c), "/office/%s/%s/" % (sl(h), sl(o))) for o, c in sorted(by[h])])) for h in sorted(by))
    body = f"""
<div class="page-head"><h1>지구대·파출소 {len(POL):,}곳 — 경찰서별 위치·관할</h1><p>경찰청 공공데이터 · {ASOF_P} 기준</p></div>
<p class="lead">전국 지구대·파출소 {len(POL):,}곳(지구대 {len([d for d in POL if d['kind'] == '지구대'])}곳, 파출소 {len([d for d in POL if d['kind'] == '파출소']):,}곳)을 경찰서별로 정리했습니다. 경찰서를 누르면 관할 지구대·파출소와 치안센터를 볼 수 있습니다. 범죄·긴급 상황은 112로 신고하세요.</p>
{ad()}
{secs}
<p class="note">{NOTE_P}</p>
"""
    write("/police/", layout("/police/", f"지구대·파출소 {len(POL):,}곳 — 경찰서별 위치·관할 목록", f"전국 지구대·파출소 {len(POL):,}곳을 지방경찰청·경찰서별로 정리. 주소와 관할, 112 신고 안내.", body, [("전국 지구대·파출소는 몇 곳인가요?", f"공공데이터 기준 {len(POL):,}곳입니다."), ("지구대·파출소 전화번호는?", "데이터에 전화번호가 없어 긴급 신고는 112, 일반 문의는 관할 경찰서 대표번호를 이용하세요.")], [("홈", "/"), ("지구대·파출소", "/police/")], coupang=True), "0.9")

# ───────────────────────── 지역 ─────────────────────────
def page_sg(sido, sg):
    f = sorted(FIRE_BY_SG.get((sido, sg), []), key=lambda x: x["name"]); p = sorted(POL_BY_SG.get((sido, sg), []), key=lambda x: (x["kind"], x["name"])); path = "/region/%s/%s/" % (sido, sg)
    body = f"""
<div class="page-head"><h1>{esc(sido)} {esc(sg)} 119안전센터·지구대·파출소 — 위치·전화번호</h1><p>119안전센터 {len(f)}곳 · 지구대·파출소 {len(p)}곳</p></div>
<p class="lead"><b>{esc(sido)} {esc(sg)}</b>의 119안전센터 {len(f)}곳과 지구대·파출소 {len(p)}곳입니다. 이름을 누르면 주소와 전화번호(119안전센터)를 볼 수 있습니다. {URGENT}</p>
{ad()}
{('<h2 class="group-title">🚒 119안전센터</h2>' + table(FH, frows(f))) if f else ''}
{('<h2 class="group-title">🚓 지구대·파출소</h2>' + table(PH, prows(p))) if p else ''}
<p class="note">{NOTE_F} {NOTE_P}</p>
{chips([(sido, "/region/%s/" % sido), ("119 신고 요령", "/guide/119/"), ("112 신고 요령", "/guide/112/")])}
"""
    faq = [(f"{sg}에는 119안전센터가 몇 곳 있나요?", f"공공데이터 기준 {len(f)}곳입니다."), (f"{sg}에는 지구대·파출소가 몇 곳 있나요?", f"공공데이터 기준 {len(p)}곳입니다.")]
    write(path, layout(path, f"{sido} {sg} 119안전센터·지구대·파출소 — 위치·전화번호", f"{sido} {sg} 119안전센터 {len(f)}곳, 지구대·파출소 {len(p)}곳의 주소와 전화번호.", body, faq, [("홈", "/"), ("지역별", "/region/"), (sido, "/region/%s/" % sido), (sg, path)]), "0.7")

def page_sido(sido):
    sgs = sorted({sg for (s, sg) in SG_KEYS if s == sido}); path = "/region/%s/" % sido
    nf = sum(len(FIRE_BY_SG.get((sido, sg), [])) for sg in sgs); np_ = sum(len(POL_BY_SG.get((sido, sg), [])) for sg in sgs)
    body = f"""
<div class="page-head"><h1>{esc(sido)} 119안전센터·지구대·파출소 — 시군구별</h1><p>119안전센터 {nf}곳 · 지구대·파출소 {np_}곳</p></div>
<p class="lead"><b>{esc(sido)}</b>에는 119안전센터 {nf}곳과 지구대·파출소 {np_}곳이 있습니다. 시군구를 눌러 가까운 안전시설을 찾아보세요. {URGENT}</p>
{ad()}
{chips([("%s (🚒%d·🚓%d)" % (sg, len(FIRE_BY_SG.get((sido, sg), [])), len(POL_BY_SG.get((sido, sg), []))), "/region/%s/%s/" % (sido, sg)) for sg in sgs])}
<p class="note">{NOTE_F}</p>
{chips([("지역별", "/region/"), ("긴급 안내", "/guide/")])}
"""
    faq = [(f"{sido}에는 119안전센터가 몇 곳 있나요?", f"공공데이터 기준 {nf}곳입니다."), (f"{sido}에는 지구대·파출소가 몇 곳 있나요?", f"공공데이터 기준 {np_}곳입니다.")]
    write(path, layout(path, f"{sido} 119안전센터·지구대·파출소 목록 — 시군구별 위치", f"{sido} 119안전센터 {nf}곳과 지구대·파출소 {np_}곳을 시군구별로 정리했습니다.", body, faq, [("홈", "/"), ("지역별", "/region/"), (sido, path)]), "0.8")

def hub_region():
    rows = [['<a href="/region/%s/">%s</a>' % (s, s), len([d for d in FIRE if d["sido"] == s]), len([d for d in POL if d["sido"] == s])] for s in SIDOS]
    body = f"""
<div class="page-head"><h1>지역별 119안전센터·지구대·파출소</h1><p>시도·시군구별 안전시설</p></div>
<p class="lead">전국 119안전센터 {len(FIRE):,}곳과 지구대·파출소 {len(POL):,}곳을 시도·시군구별로 찾아보세요. {URGENT}</p>
{ad()}
{table(['시도', '119안전센터', '지구대·파출소'], rows, (1, 2))}
<p class="note">{NOTE_F}</p>
{chips([("119안전센터", "/fire/"), ("지구대·파출소", "/police/"), ("긴급 안내", "/guide/")])}
"""
    write("/region/", layout("/region/", "지역별 119안전센터·지구대·파출소 — 시도·시군구 목록", f"전국 119안전센터 {len(FIRE):,}곳, 지구대·파출소 {len(POL):,}곳을 시도·시군구별로 정리.", body, [("가까운 119안전센터는 어떻게 찾나요?", "시도와 시군구를 선택하면 해당 지역의 119안전센터 목록이 나옵니다.")], [("홈", "/"), ("지역별", "/region/")], coupang=True), "0.9")

# ───────────────────────── 긴급 안내 ─────────────────────────
GN = "이 안내는 일반적인 응급 대처 요령이며 상황에 따라 다를 수 있습니다. 119 상황요원의 지시를 가장 우선하세요."
def guide(slug, title, h1, intro, steps, faq, desc):
    body = f"""
<div class="page-head"><h1>{h1}</h1><p>일반 안내 · 119/112 지시 우선</p></div>
<p class="lead">{intro}</p>
{ad()}
{''.join('<h2 class="group-title">%d. %s</h2><p class="lead">%s</p>' % (i + 1, t, d) for i, (t, d) in enumerate(steps))}
<p class="note">{GN}</p>
{chips([("119 신고 요령", "/guide/119/"), ("112 신고 요령", "/guide/112/"), ("심폐소생술", "/guide/cpr/"), ("AED 사용법", "/guide/aed/"), ("119안전센터 찾기", "/fire/")])}
"""
    path = "/guide/%s/" % slug
    write(path, layout(path, title, desc, body, faq, [("홈", "/"), ("긴급 안내", "/guide/"), (h1, path)]), "0.7")

def guides():
    guide("119", "119 신고 요령 — 화재·구급 신고할 때 말해야 할 것", "119 신고 요령", "화재·구조·구급 상황에서는 119로 신고합니다. 침착하게 필요한 정보를 순서대로 말하면 출동이 빨라집니다.",
          [("119로 전화", "휴대전화·유선 모두 지역번호 없이 119를 누릅니다."), ("위치 먼저 알리기", "주소(건물명·동·호수)나 주변 큰 건물·도로명을 알려 줍니다. 위치를 모르면 주변 표지판이나 건물 이름을 말합니다."), ("무슨 일인지", "불이 났는지, 사람이 쓰러졌는지, 다쳤는지 등 상황을 간단히 말합니다."), ("환자 상태", "의식·호흡 여부, 나이와 증상을 알려 주고 상황요원의 안내를 따릅니다."), ("전화를 먼저 끊지 않기", "요원이 끊으라고 할 때까지 통화를 유지하며 안내에 따라 응급처치를 합니다.")],
          [("119는 어디서나 되나요?", "네. 휴대전화 잠금 상태에서도 긴급통화로 연결됩니다."), ("신고 위치를 모르면?", "주변 건물 이름·도로 표지판·눈에 보이는 상호를 말하세요.")], "119 신고 시 말해야 할 위치·상황·환자 상태와 통화 요령을 순서대로 정리한 안내.")
    guide("112", "112 신고 요령 — 범죄·긴급 상황 신고와 문자 신고", "112 신고 요령", "범죄 피해나 위험한 상황에서는 112로 신고합니다. 말하기 어려운 상황에서는 문자로도 신고할 수 있습니다.",
          [("112로 전화", "긴급 상황은 지역번호 없이 112를 누릅니다."), ("위치와 상황", "현재 위치(주소·건물)와 무슨 일이 일어났는지, 가해자 인상착의나 이동 방향을 말합니다."), ("말하기 어려울 때", "소리를 내기 어려운 상황이라면 112 문자 신고를 이용할 수 있습니다."), ("안전 확보", "가능하면 안전한 곳으로 이동하고 경찰관 도착 전까지 위험을 피합니다.")],
          [("지구대·파출소로 직접 전화해도 되나요?", "긴급 상황은 112 신고가 가장 빠릅니다. 일반 문의는 관할 경찰서나 지구대·파출소에 문의하세요."), ("112는 언제 쓰나요?", "범죄 피해, 위험, 실종 등 긴급한 경찰 도움이 필요할 때 씁니다.")], "112 신고 시 말해야 할 위치·상황과 문자 신고, 안전 확보 요령을 정리한 안내.")
    guide("cpr", "심폐소생술(CPR) 순서 — 가슴압박 위치·깊이·속도", "심폐소생술(CPR) 순서", "심장이 멈춘 사람에게는 빨리 가슴압박을 시작하는 것이 중요합니다. 일반인이 할 수 있는 심폐소생술 순서를 정리했습니다.",
          [("반응 확인·119 신고", "어깨를 두드리며 반응을 확인하고 반응이 없으면 119에 신고합니다. 주변 사람을 지목해 119 신고와 자동심장충격기(AED) 가져오기를 부탁합니다."), ("호흡 확인", "가슴이 움직이는지 10초 이내로 확인합니다. 호흡이 없거나 비정상이면 가슴압박을 시작합니다."), ("가슴압박", "가슴뼈 아래쪽 절반(가슴 중앙)에 손바닥 뒤꿈치를 대고 약 5~6cm 깊이로 분당 100~120회 속도로 강하고 빠르게 누릅니다."), ("AED 사용", "AED가 도착하면 전원을 켜고 음성 안내에 따라 패드를 붙이고 지시를 따릅니다."), ("계속하기", "119 구급대가 올 때까지 가슴압박을 멈추지 않고 이어 갑니다.")],
          [("인공호흡도 해야 하나요?", "교육받지 않은 일반인은 가슴압박만 시행해도 됩니다. 교육받은 경우 가슴압박 30회와 인공호흡 2회를 반복합니다."), ("가슴압박을 하면 갈비뼈가 부러지나요?", "부러질 수 있지만 생명을 살리는 것이 우선이므로 멈추지 말고 계속하세요.")], "심폐소생술(CPR) 순서와 가슴압박 위치·깊이(5~6cm)·속도(분당 100~120회)를 일반인 기준으로 정리.")
    guide("aed", "AED(자동심장충격기) 사용법 — 패드 부착부터 쇼크까지", "AED 사용법", "AED(자동심장충격기)는 심장이 멈춘 사람에게 전기충격을 주어 정상 리듬을 회복하도록 돕는 장치로 음성 안내를 따르면 누구나 사용할 수 있습니다.",
          [("전원 켜기", "AED를 가져와 전원 버튼을 누르거나 뚜껑을 엽니다. 이후 음성 안내가 나옵니다."), ("패드 부착", "환자의 상체를 노출하고 패드를 그림에 표시된 위치(오른쪽 윗가슴, 왼쪽 옆구리)에 붙입니다."), ("분석 중 접촉 금지", "AED가 심장 리듬을 분석하는 동안에는 환자에게서 손을 뗍니다."), ("충격", "‘충격이 필요합니다’ 안내가 나오면 모두 물러선 것을 확인하고 충격 버튼을 누릅니다."), ("바로 심폐소생술", "충격 후에는 즉시 가슴압박을 다시 시작하고 AED의 다음 안내를 따릅니다.")],
          [("AED는 어디에 있나요?", "공공시설·지하철역·학교·아파트 등에 설치되어 있으며 설치 위치는 중앙응급의료센터 서비스 등에서 확인할 수 있습니다."), ("AED를 잘못 쓰면 위험한가요?", "AED는 심장 리듬을 스스로 분석해 필요한 경우에만 충격을 안내하므로 일반인도 안전하게 사용할 수 있습니다.")], "AED(자동심장충격기) 사용 순서와 패드 부착 위치를 일반인 기준으로 정리.")
    body = f"""
<div class="page-head"><h1>긴급 안내 — 119·112 신고와 응급처치</h1><p>위급할 때 알아야 할 것</p></div>
<p class="lead">위급한 상황에서 바로 도움이 되는 신고 요령과 응급처치 순서를 정리했습니다. {URGENT}</p>
{ad()}
{chips([("119 신고 요령", "/guide/119/"), ("112 신고 요령", "/guide/112/"), ("심폐소생술(CPR)", "/guide/cpr/"), ("AED 사용법", "/guide/aed/"), ("119안전센터 찾기", "/fire/"), ("지구대·파출소 찾기", "/police/")])}
<p class="note">{GN}</p>
"""
    write("/guide/", layout("/guide/", "긴급 안내 — 119·112 신고 요령과 심폐소생술·AED", "119·112 신고 요령, 심폐소생술(CPR), AED 사용법 등 위급 상황 대처 안내.", body, None, [("홈", "/"), ("긴급 안내", "/guide/")]), "0.8")

def page_home():
    body = f"""
<div class="hero"><h1>🚒 119안전센터 {len(FIRE):,}곳 · 지구대·파출소 {len(POL):,}곳</h1><p>가까운 안전시설과 긴급 신고 요령을 바로 확인하세요.</p></div>
{ad()}
<div class="card-grid">
<a class="card" href="/fire/"><b>🚒 119안전센터</b><span>소방서별 전화번호·주소</span></a>
<a class="card" href="/police/"><b>🚓 지구대·파출소</b><span>경찰서별 위치·관할</span></a>
<a class="card" href="/region/"><b>📍 지역별</b><span>시도·시군구 안전시설</span></a>
<a class="card" href="/guide/"><b>🆘 긴급 안내</b><span>119·112 신고, 심폐소생술, AED</span></a>
</div>
<p class="lead">우아안전은 소방청·경찰청 공공데이터로 전국 119안전센터와 지구대·파출소의 위치·전화번호를 정리한 사이트입니다. {URGENT} 자세한 기준은 <a href="/about/">데이터 설명</a>을 참고하세요.</p>
"""
    faq = [("긴급 상황에서 어디로 신고하나요?", "화재·구조·구급은 119, 범죄·긴급 상황은 112로 신고하세요."), ("정보는 어디서 가져오나요?", f"소방청 119안전센터 현황({ASOF_F} 기준), 경찰청 전국 지구대·파출소 주소 현황({ASOF_P} 기준)을 사용합니다.")]
    write("/", layout("/", f"우아안전 — 119안전센터·지구대·파출소 위치와 전화번호", f"전국 119안전센터 {len(FIRE):,}곳과 지구대·파출소 {len(POL):,}곳의 위치·전화번호. 119·112 신고 요령, 심폐소생술, AED 사용법.", body, faq), "1.0")

def page_about():
    body = f"""
<div class="page-head"><h1>데이터 설명</h1><p>정보의 출처와 한계</p></div>
<h2 class="group-title">📚 출처</h2><p class="lead">소방청 ‘119안전센터 현황’(공공데이터포털 15065056, {ASOF_F} 기준, 주소·전화번호 파일) {len(FIRE):,}곳, 경찰청 ‘전국 지구대 파출소 주소 현황’(15077036, {ASOF_P} 기준) {len(POL):,}곳, ‘전국 치안센터 주소 현황’(15076962) {len(CHI)}곳을 사용했습니다. 주소에서 시도·시군구를 읽을 수 없는 일부 항목은 제외했습니다.</p>
<h2 class="group-title">⚠️ 한계</h2><p class="lead">위치와 전화번호는 변경될 수 있고 지구대·파출소 전화번호는 데이터에 없습니다. 이 사이트는 긴급 신고 수단이 아니며 {URGENT} 응급처치 안내는 일반 대처 요령으로 의료적 조언을 대신하지 않습니다. AED 설치 위치와 민방위대피소는 아직 반영하지 않았습니다.</p>
<h2 class="group-title">📬 문의·정정</h2><p class="lead">오류 제보는 <a href="mailto:ingmaster83@gmail.com">ingmaster83@gmail.com</a> 으로 보내 주세요.</p>
"""
    write("/about/", layout("/about/", "데이터 설명 — 출처와 한계", "우아안전 데이터 출처(소방청·경찰청 공공데이터)와 한계를 공개합니다.", body, None, [("홈", "/"), ("데이터 설명", "/about/")]), "0.5")

def page_privacy():
    body = """
<div class="page-head"><h1>개인정보처리방침</h1></div>
<p class="lead">우아안전(wooasafe.wooahouse.com, 이하 “서비스”)은 회원가입·로그인을 요구하지 않으며 이용자의 개인정보를 직접 수집하지 않습니다.</p>
<h3>자동 수집 정보</h3><p class="lead">서비스 개선을 위해 Google Analytics로 방문자 수·페이지뷰 등 익명 통계를 수집하며, Google AdSense와 쿠팡 파트너스는 맞춤 광고를 위해 쿠키를 사용할 수 있습니다. 쿠키는 브라우저 설정에서 비활성화할 수 있습니다. (<a href="https://policies.google.com/privacy">Google 개인정보처리방침</a>, <a href="https://policies.google.com/technologies/ads">Google 광고 정책</a>)</p>
<h3>쿠팡 파트너스</h3><p class="lead">일부 페이지에는 쿠팡 파트너스 활동의 일환으로 광고가 포함되어 있으며 이에 따른 수수료를 제공받을 수 있습니다.</p>
<h3>문의</h3><p class="lead"><a href="mailto:ingmaster83@gmail.com">ingmaster83@gmail.com</a></p>
<p class="note">최종 수정일: 2026년 10월 22일</p>
"""
    write("/privacy/", layout("/privacy/", "개인정보처리방침", "우아안전 개인정보처리방침", body, None, [("홈", "/"), ("개인정보처리방침", "/privacy/")]), sitemap=False)

def make_og():
    f = ROOT / "assets" / "og-image.png"
    if f.exists(): return
    try: from PIL import Image, ImageDraw, ImageFont
    except Exception: return
    im = Image.new("RGB", (1200, 630), (185, 28, 28)); dr = ImageDraw.Draw(im)
    def font(sz):
        for n in ("malgunbd.ttf", "malgun.ttf", "NanumGothicBold.ttf"):
            try: return ImageFont.truetype(n, sz)
            except Exception: pass
        return ImageFont.load_default()
    dr.rounded_rectangle((90, 90, 1110, 540), 40, fill=(255, 255, 255))
    dr.text((150, 150), "우아안전", font=font(110), fill=(153, 27, 27))
    dr.text((150, 300), "119안전센터 · 지구대 · 파출소", font=font(54), fill=(31, 41, 55))
    dr.text((150, 380), "긴급 신고 요령 · 응급처치", font=font(54), fill=(31, 41, 55))
    dr.text((150, 470), "wooasafe.wooahouse.com", font=font(34), fill=(107, 114, 128))
    im.save(f)

def main():
    t0 = time.time(); make_og()
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)
    for nf in ROOT.glob("naver*.html"): shutil.copy(nf, OUT / nf.name)
    for d in FIRE: page_fire(d)
    for (s, st) in sorted(BY_STATION): page_station(s, st)
    hub_fire()
    for d in POL: page_police(d)
    for (hq, off) in sorted(BY_OFFICE): page_office(hq, off)
    hub_police()
    for (s, sg) in SG_KEYS: page_sg(s, sg)
    for s in SIDOS: page_sido(s)
    hub_region(); guides(); page_home(); page_about(); page_privacy()
    today = time.strftime("%Y-%m-%d")
    urls = "".join("<url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>" % (BASE, q(p), today, pr) for p, pr in WRITTEN)
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>\n' % urls, encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % BASE, encoding="utf-8")
    (OUT / "CNAME").write_text("wooasafe.wooahouse.com\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    nf = layout("/404.html", "페이지를 찾을 수 없습니다", "요청한 페이지를 찾을 수 없습니다.", '<div class="page-head"><h1>페이지를 찾을 수 없습니다</h1></div><div class="chips"><a class="chip" href="/">홈</a><a class="chip" href="/region/">지역별 안전시설</a></div>', None, None, noindex=True)
    (OUT / "404.html").write_text(nf, encoding="utf-8")
    print("pages", len(WRITTEN), "elapsed", round(time.time() - t0), "s")

if __name__ == "__main__":
    main()
