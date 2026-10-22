# -*- coding: utf-8 -*-
"""소방청 119안전센터 현황(15065056, zip 내 최신 csv)·경찰청 전국 지구대 파출소 주소 현황(15077036)·전국 치안센터 주소 현황(15076962) → data/*.json
사용: python scripts/build_data.py <원본폴더>  (원본: ctr119.bin, jigudae.bin, chian.bin)"""
import sys, csv, io, re, json, zipfile, pathlib
sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path(sys.argv[1])
SIDO = {"서울": "서울특별시", "서울시": "서울특별시", "서울특별시": "서울특별시", "부산": "부산광역시", "부산광역시": "부산광역시", "대구": "대구광역시", "대구광역시": "대구광역시", "인천": "인천광역시", "인천광역시": "인천광역시", "광주": "광주광역시", "광주광역시": "광주광역시",
        "대전": "대전광역시", "대전광역시": "대전광역시", "울산": "울산광역시", "울산광역시": "울산광역시", "세종": "세종특별자치시", "세종특별자치시": "세종특별자치시", "경기": "경기도", "경기도": "경기도", "강원": "강원특별자치도", "강원도": "강원특별자치도", "강원특별자치도": "강원특별자치도",
        "충북": "충청북도", "충청북도": "충청북도", "충남": "충청남도", "충청남도": "충청남도", "전북": "전북특별자치도", "전라북도": "전북특별자치도", "전북특별자치도": "전북특별자치도", "전남": "전라남도", "전라남도": "전라남도", "전남광주통합특별시": "전남광주통합특별시", "전남광주특별시": "전남광주통합특별시",
        "경북": "경상북도", "경상북도": "경상북도", "경남": "경상남도", "경상남도": "경상남도", "제주": "제주특별자치도", "제주도": "제주특별자치도", "제주특별자치도": "제주특별자치도"}
def read(fn, pick=None):
    b = (SRC / fn).read_bytes()
    if b[:2] == b"PK":
        z = zipfile.ZipFile(SRC / fn); names = sorted(z.namelist()); name = names[-1] if pick is None else [n for n in names if pick in n][0]; b = z.read(name); print(fn, "->", name)
    for enc in ("utf-8-sig", "cp949"):
        try: t = b.decode(enc); break
        except Exception: pass
    return list(csv.DictReader(io.StringIO(t)))
def parse(a):
    a = re.sub(r"\s+", " ", (a or "").replace('"', "")).strip(); a = re.sub(r"^(\([^)]*\)\s*)+", "", a)
    p = a.split(); sido = SIDO.get(p[0], "") if p else ""
    sg = p[1] if len(p) > 1 and re.search(r"[시군구]$", p[1]) else ("세종시" if sido == "세종특별자치시" else "")
    return a, sido, sg
def main():
    fire = []
    for r in read("ctr119.bin", "20260701"):
        a, sido, sg = parse(r["주소"])
        if not sido or not sg: continue
        fire.append(dict(hq=r["시도본부"].strip(), station=r["소방서명"].strip(), name=r["119안전센터명"].strip(), addr=a, tel=r["전화번호"].strip(), fax=r["팩스번호"].strip(), sido=sido, sg=sg))
    pol = []
    for r in read("jigudae.bin"):
        a, sido, sg = parse(r["주소"])
        if not sido or not sg: continue
        pol.append(dict(hq=r["시도청"].strip(), office=r["경찰서"].strip(), name=r["관서명"].strip(), kind=r["구분"].strip(), addr=a, sido=sido, sg=sg))
    chi = []
    for r in read("chian.bin"):
        a, sido, sg = parse(r["주소"])
        chi.append(dict(hq=r["시도청"].strip(), office=r["경찰서"].strip(), parent=r["관서명"].strip(), kind=r["지구대 파출소"].strip(), name=r["치안센터명"].strip(), addr=a, sido=sido, sg=sg))
    pmap = {(x["office"], x["name"]): x for x in pol}
    import collections
    omap = collections.defaultdict(collections.Counter)
    for x in pol: omap[x["office"]][(x["sido"], x["sg"])] += 1
    for c in chi:
        if c["sido"] and c["sg"]: continue
        par = pmap.get((c["office"], c["parent"]))
        if par: c["sido"], c["sg"] = par["sido"], par["sg"]
        elif omap.get(c["office"]): c["sido"], c["sg"] = omap[c["office"]].most_common(1)[0][0]
    chi = [c for c in chi if c["sido"] and c["sg"]]
    (ROOT / "data").mkdir(exist_ok=True)
    for n, v in (("fire", fire), ("police", pol), ("chian", chi)): (ROOT / "data" / (n + ".json")).write_text(json.dumps(v, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("119안전센터", len(fire), "지구대·파출소", len(pol), "치안센터", len(chi), "치안센터 지역미확인", sum(1 for c in chi if not c["sido"]))
if __name__ == "__main__": main()
