# Ultra Brain v0.985

## 실제 하위 화면 테마 전파

- Ultra Brain에서 선택한 World Theme가 OS Ecosystem을 거쳐 Living OS와 Universal Learning Engine의 실제 기능 화면까지 적용됩니다.
- Living OS는 홈과 재무, 투자, 직업, 건강, 지식, 루틴을 포함한 전체 등록 화면에 테마 이미지와 시각 조정값을 적용합니다.
- Universal Learning Engine은 홈과 W01~W09 전체 학습 월드에 동일한 테마 이미지와 시각 조정값을 적용합니다.
- 하위 앱에는 별도 UI Studio를 만들지 않았습니다. Ultra Brain UI Studio의 설정만 자동 상속합니다.

## Lock / Override

- 잠금 또는 예외 처리된 대상은 현재 하위 UI를 그대로 유지합니다.
- OS Ecosystem에만 걸린 잠금이 Living OS나 Universal Learning Engine 잠금으로 잘못 전달되지 않습니다.
- 테마, 배경, 색상, 배치, 위치, 크기, 표시 여부와 세부 효과를 항목별로 독립 적용합니다.

## 화면 품질

- 홈과 기능 화면의 밝기, 명암, 채도, 색조, 광원, 그림자, 발광, 질감, 흐림, 투명도를 일치시켰습니다.
- 화면 전환 애니메이션이 테마 필터를 덮어쓰던 문제와 불필요한 선 질감을 제거했습니다.
- 쿼리 없이 직접 접속할 때는 Living OS와 Universal Learning Engine의 기존 기본 UI를 유지합니다.

## 배포

- Ultra Brain Sites 및 Streamlit
- OS Ecosystem Streamlit
- Living OS Streamlit
- Universal Learning Engine Streamlit

각 Production URL의 실제 화면과 기능 이동을 검증한 뒤 배포 완료로 판정합니다.
