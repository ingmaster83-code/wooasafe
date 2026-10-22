# 우아안전 (wooasafe.wooahouse.com)
소방청 119안전센터 현황(15065056, 2026-07-01 기준) 1,139곳 + 경찰청 지구대·파출소 주소 현황(15077036, 2025-12-31) 2,008곳 + 치안센터(15076962) 기반 정적 사이트(약 3,900페이지).
- `python scripts/build_data.py <원본폴더>`(ctr119.bin/jigudae.bin/chian.bin) → `data/*.json`(커밋) → `python scripts/build_site.py` → `_site/`
- 추후: AED(국립중앙의료원 API 15000652, 활용신청 필요)·민방위대피시설(15044951, 파일 다운로드 정보 없음) 추가 검토.
