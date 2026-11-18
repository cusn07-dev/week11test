from pathlib import Path
import pytest

# 테스트 대상 함수 임포트 (실제 모듈 경로에 맞게 수정하세요)
from grade_parser import parse_grades


@pytest.fixture
def create_csv(tmp_path: Path):
    """임시 CSV 파일을 생성해 경로를 반환하는 헬퍼 픽스처"""
    def _create(content: str, filename: str = "grades.csv") -> Path:
        file_path = tmp_path / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path
    return _create


# ==========================================
# 1. 정상 케이스 및 조건·제약 검증
# ==========================================

def test_valid_rows_and_header_skip(create_csv):
    """①②⑥ 첫 줄 헤더 건너뛰기 및 정상 데이터 파싱 검증"""
    csv_data = (
        "이름,점수\n"
        "홍길동,85\n"
        "김철수,92\n"
    )
    path = create_csv(csv_data)
    kept, skipped = parse_grades(path)

    assert kept == [("홍길동", 85), ("김철수", 92)]
    assert skipped == []


def test_duplicate_names_are_preserved(create_csv):
    """④⑥ 동명이인이 여러 번 나와도 삭제하지 않고 모두 유지"""
    csv_data = (
        "name,score\n"
        "이영희,80\n"
        "이영희,95\n"
        "이영희,80\n"
    )
    path = create_csv(csv_data)
    kept, skipped = parse_grades(path)

    assert kept == [("이영희", 80), ("이영희", 95), ("이영희", 80)]
    assert skipped == []


def test_empty_lines_ignored_without_skip_record(create_csv):
    """⑥ 빈 줄(또는 공백만 있는 줄)은 skipped에 기록하지 않고 무시하며, 줄 번호는 유지"""
    csv_data = (
        "name,score\n"      # 1번 줄 (헤더)
        "\n"                # 2번 줄 (빈 줄 - 무시)
        "박지성,88\n"       # 3번 줄 (정상)
        "   \n"             # 4번 줄 (공백 줄 - 무시)
        "손흥민,invalid\n"  # 5번 줄 (오류 - 줄번호 5여야 함)
    )
    path = create_csv(csv_data)
    kept, skipped = parse_grades(path)

    assert kept == [("박지성", 88)]
    assert len(skipped) == 1
    assert skipped[0][0] == 5
    assert skipped[0][1] == "손흥민,invalid"


# ==========================================
# 2. 경계값 테스트 (Boundary Value Analysis)
# ==========================================

@pytest.mark.parametrize("score_str, expected_score, is_valid", [
    ("-1", None, False),   # 하한선 바로 아래 (예외)
    ("0", 0, True),        # 하한선 경계 (정상)
    ("1", 1, True),        # 하한선 바로 위 (정상)
    ("99", 99, True),      # 상한선 바로 아래 (정상)
    ("100", 100, True),    # 상한선 경계 (정상)
    ("101", None, False),  # 상한선 바로 위 (예외)
])
def test_score_boundaries(create_csv, score_str, expected_score, is_valid):
    """②⑤ 점수 0~100 경계값 검증"""
    csv_data = f"name,score\n테스트유저,{score_str}\n"
    path = create_csv(csv_data)
    kept, skipped = parse_grades(path)

    if is_valid:
        assert kept == [("테스트유저", expected_score)]
        assert skipped == []
    else:
        assert kept == []
        assert len(skipped) == 1
        assert skipped[0][0] == 2
        assert skipped[0][1] == f"테스트유저,{score_str}"
        assert skipped[0][2]  # 이유가 비어있지 않은지 확인


def test_only_header_file(create_csv):
    """헤더만 있고 데이터가 없는 빈 성적표 처리"""
    path = create_csv("이름,점수\n")
    kept, skipped = parse_grades(path)

    assert kept == []
    assert skipped == []


def test_empty_file(create_csv):
    """완전히 비어 있는 0바이트 파일 처리"""
    path = create_csv("")
    kept, skipped = parse_grades(path)

    assert kept == []
    assert skipped == []


# ==========================================
# 3. 예외 및 잘못된 형식 처리 (Exception & Skip)
# ==========================================

def test_file_not_found_raises_error(tmp_path: Path):
    """③④⑤ 존재하지 않는 파일 경로 입력 시 FileNotFoundError 발생"""
    non_existent = tmp_path / "does_not_exist.csv"
    with pytest.raises(FileNotFoundError):
        parse_grades(non_existent)


@pytest.mark.parametrize("bad_line", [
    "홍길동",               # 열 개수 1개 (부족)
    "홍길동,90,추가열",      # 열 개수 3개 (초과)
    ",85",                  # 이름 빈 문자열
    "   ,85",               # 이름 공백만 존재
    "홍길동,",               # 점수 빈 문자열
    "홍길동,   ",            # 점수 공백만 존재
    "홍길동,구십점",          # 점수 문자열 (비정수)
    "홍길동,85.5",           # 점수 실수/소수점 (비정수)
])
def test_malformed_rows_are_skipped(create_csv, bad_line):
    """②③⑤ 잘못된 형식의 줄은 건너뛰고 (줄번호, 원본줄, 이유) 형태로 skipped에 기록"""
    csv_data = f"name,score\n{bad_line}\n"
    path = create_csv(csv_data)
    kept, skipped = parse_grades(path)

    assert kept == []
    assert len(skipped) == 1
    line_no, raw_line, reason = skipped[0]
    assert line_no == 2
    assert raw_line == bad_line
    assert isinstance(reason, str) and len(reason.strip()) > 0


# ==========================================
# 4. 복합 시나리오 (통합 검증)
# ==========================================

def test_mixed_valid_invalid_and_empty_lines(create_csv):
    """정상, 동명이인, 빈 줄, 각종 예외 줄이 섞여 있을 때 정확한 줄 번호와 결과 반환"""
    csv_data = (
        "학생명,점수\n"          # 1: 헤더
        "김민수,100\n"           # 2: 정상 (상한 경계)
        "\n"                     # 3: 빈 줄 (무시)
        " ,70\n"                 # 4: 이름 공백 (스킵)
        "김민수,0\n"             # 5: 정상 (동명이인, 하한 경계)
        "이지은,105\n"           # 6: 범위 초과 (스킵)
        "박보검,85,1등급\n"      # 7: 열 개수 초과 (스킵)
        "최우식,77.7\n"          # 8: 비정수 (스킵)
        "정해인,65\n"            # 9: 정상
    )
    path = create_csv(csv_data)
    kept, skipped = parse_grades(path)

    assert kept == [
        ("김민수", 100),
        ("김민수", 0),
        ("정해인", 65),
    ]

    # 스킵된 줄의 줄 번호와 원본 문자열 검증
    assert [(item[0], item[1]) for item in skipped] == [
        (4, " ,70"),
        (6, "이지은,105"),
        (7, "박보검,85,1등급"),
        (8, "최우식,77.7"),
    ]
    # 모든 스킵 항목에 이유(reason)가 문자열로 포함되어 있는지 검증
    assert all(isinstance(item[2], str) and item[2] for item in skipped)
