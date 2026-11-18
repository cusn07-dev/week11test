# 성적 CSV 검증 및 로더 (load_scores)

## ① 무엇을 하나요 (What)

성적 CSV 파일을 읽어 0~100 사이의 유효한 정수 점수만 골라내고, 형식이나 범위가 잘못된 줄은 줄 번호와 사유를 함께 기록해 돌려줍니다.

## ② 왜 만들었나요 (Why)

실제 성적 CSV 파일에는 빈 칸, 숫자가 아닌 문자열, 0~100 범위를 벗어난 점수, 열 개수가 맞지 않는 줄이 섞여 있어 단순 파싱 시 프로그램이 중단되거나 잘못된 데이터가 집계됩니다. 또한 동명이인 학생이 존재할 수 있으므로 이름을 기준으로 임의 삭제하지 않고 모두 보존하되, 문제가 있는 행만 안전하게 걸러내기 위해 만들었습니다.

## ③ 어떻게 쓰나요 (How)

```bash
# 설치
pip install pytest pytest-cov

# 실행
python load_scores.py scores.csv
```

## ④ 어떻게 테스트하나요

```bash
pytest test_load_scores.py -v
pytest --cov=load_scores --cov-report=term-missing
```

```
========================= test session starts ==========================
collected 8 items

test_load_scores.py::test_missing_file_raises_error PASSED       [ 12%]
test_load_scores.py::test_header_only_returns_empty PASSED       [ 25%]
test_load_scores.py::test_valid_and_boundary_scores PASSED       [ 37%]
test_load_scores.py::test_invalid_column_count_skipped PASSED    [ 50%]
test_load_scores.py::test_non_integer_or_empty_score_skipped PASSED [ 62%]
test_load_scores.py::test_out_of_range_score_skipped PASSED      [ 75%]
test_load_scores.py::test_empty_name_skipped PASSED              [ 87%]
test_load_scores.py::test_duplicate_names_kept_and_blank_lines_ignored PASSED [100%]

========================== 8 passed in 0.03s ===========================
```

## ⑤ 파일 구성

| 파일 | 하는 일 |
| --- | --- |
| `load_scores.py` | 성적 CSV 파일을 읽어 `(kept, skipped)` 튜플로 반환하는 핵심 모듈 |
| `test_load_scores.py` | 코드를 보지 않고 명세만으로 직접 설계한 8개 단위 테스트 (`pytest`) |
| `test_ai_A.py` | AI에게 `load_scores.py` 코드를 제공하고 받은 단위 테스트 |
| `test_ai_B.py` | AI에게 10주차 명세서 6칸만 제공하고 받은 단위 테스트 |
| `README.md` | 프로그램 소개, 실행 방법, 테스트 방법 및 AI 활용 내역 안내 문서 |
| `LICENSE` | 본 저장소 코드의 이용 허락 조건을 명시한 MIT 라이선스 파일 |

## ⑥ 만든 사람 · AI를 어디에 썼는지

- 만든 사람 : 신윤수 (2026101038)
- AI를 쓴 곳 : 프롬프트 실험(`test_ai_A.py`, `test_ai_B.py`) 비교용 테스트 코드 생성 및 `README.md` 초안 구조화
- 내가 직접 판단한 것 : 명세 기반 8개 테스트 케이스 설계 및 경계값(0, 100, -1, 101) 선정, AI 생성 테스트의 검증 기준 부합 여부 및 함정 코드(`bug3_logic.py`) 버그 정답 고착 여부 판별

## 라이선스

MIT License (LICENSE 파일 참고)
