import pytest
from scores import load_scores  # 원본 코드 파일명에 맞게 수정하세요


@pytest.fixture
def make_csv(tmp_path):
    """임시 CSV 파일을 생성해 경로(Path)를 반환하는 헬퍼 픽스처"""
    def _make(content: str, encoding: str = "utf-8"):
        file_path = tmp_path / "test_scores.csv"
        file_path.write_text(content, encoding=encoding)
        return file_path
    return _make


# ==========================================
# 1. 정상 케이스 (Normal Cases)
# ==========================================

def test_valid_rows_and_whitespace_stripping(make_csv):
    """일반적인 유효 데이터와 이름/점수 앞뒤 공백 제거를 확인한다."""
    csv_text = (
        "이름,점수\n"
        "홍길동,85\n"
        "  김철수  ,  92  \n"
        "이영희,70\n"
    )
    path = make_csv(csv_text)

    kept, skipped = load_scores(path)

    assert kept == [("홍길동", 85), ("김철수", 92), ("이영희", 70)]
    assert skipped == []


def test_utf8_bom_encoding(make_csv):
    """UTF-8 BOM(utf-8-sig)으로 저장된 파일도 첫 번째 열이 깨지지 않고 정상 처리된다."""
    csv_text = "이름,점수\n박민수,88\n"
    path = make_csv(csv_text, encoding="utf-8-sig")

    kept, skipped = load_scores(path)

    assert kept == [("박민수", 88)]
    assert skipped == []


# ==========================================
# 2. 경계값 케이스 (Boundary Cases)
# ==========================================

@pytest.mark.parametrize(
    "raw_score, expected_valid, expected_score",
    [
        ("-1", False, None),   # 하한선 바로 아래 (무효)
        ("0", True, 0),        # 하한선 경계 (유효)
        ("1", True, 1),        # 하한선 바로 위 (유효)
        ("99", True, 99),      # 상한선 바로 아래 (유효)
        ("100", True, 100),    # 상한선 경계 (유효)
        ("101", False, None),  # 상한선 바로 위 (무효)
    ],
)
def test_score_boundaries(make_csv, raw_score, expected_valid, expected_score):
    """0점과 100점 경계 및 인접값(-1, 1, 99, 101)을 검증한다."""
    path = make_csv(f"이름,점수\n학생,{raw_score}\n")

    kept, skipped = load_scores(path)

    if expected_valid:
        assert kept == [("학생", expected_score)]
        assert skipped == []
    else:
        assert kept == []
        assert skipped == [(2, f"학생,{raw_score}", "점수가 0~100 밖")]


def test_empty_file_and_header_only(make_csv):
    """완전히 빈 파일과 헤더만 있는 파일은 빈 리스트를 반환한다."""
    empty_path = make_csv("")
    header_only_path = make_csv("이름,점수\n")

    assert load_scores(empty_path) == ([], [])
    assert load_scores(header_only_path) == ([], [])


def test_blank_lines_ignored_without_skip_record(make_csv):
    """빈 줄은 무시되며 skipped에 기록되지 않고, 이후 행 번호는 유지된다."""
    csv_text = (
        "이름,점수\n"
        "\n"
        "홍길동,90\n"
        "\n"
        "김철수,200\n"
    )
    path = make_csv(csv_text)

    kept, skipped = load_scores(path)

    assert kept == [("홍길동", 90)]
    # 5번째 줄의 행 번호(5)가 정확히 기록되어야 함
    assert skipped == [(5, "김철수,200", "점수가 0~100 밖")]


# ==========================================
# 3. 데이터 오류 및 예외 케이스 (Error & Exception Cases)
# ==========================================

@pytest.mark.parametrize(
    "line_no, row_text, expected_reason",
    [
        (2, "홍길동", "열 개수가 2가 아님"),
        (2, "홍길동,80,추가열", "열 개수가 2가 아님"),
        (2, ",80", "이름이 비어 있음"),
        (2, "   ,80", "이름이 비어 있음"),
        (2, "홍길동,", "점수가 비어 있음"),
        (2, "홍길동,   ", "점수가 비어 있음"),
        (2, "홍길동,abc", "점수가 정수가 아님"),
        (2, "홍길동,85.5", "점수가 정수가 아님"),
        (2, "홍길동,-50", "점수가 0~100 밖"),
        (2, "홍길동,150", "점수가 0~100 밖"),
    ],
)
def test_invalid_rows_recorded_in_skipped(make_csv, line_no, row_text, expected_reason):
    """유효하지 않은 각 행이 정확한 행 번호, 원본 문자열, 사유와 함께 skipped에 기록된다."""
    path = make_csv(f"이름,점수\n{row_text}\n")

    kept, skipped = load_scores(path)

    assert kept == []
    assert skipped == [(line_no, row_text, expected_reason)]


def test_validation_priority_order(make_csv):
    """한 행에 여러 오류가 동시에 있을 때 우선순위(열 개수 -> 이름 -> 점수 공백 -> 정수 -> 범위)대로 처리된다."""
    csv_text = (
        "이름,점수\n"
        ",abc\n"          # 이름 공백 + 점수 비정수 -> '이름이 비어 있음' 우선
        " , \n"           # 이름 공백 + 점수 공백 -> '이름이 비어 있음' 우선
        ",10,20\n"        # 이름 공백 + 열 3개 -> '열 개수가 2가 아님' 우선
    )
    path = make_csv(csv_text)

    kept, skipped = load_scores(path)

    assert kept == []
    assert skipped == [
        (2, ",abc", "이름이 비어 있음"),
        (3, " , ", "이름이 비어 있음"),
        (4, ",10,20", "열 개수가 2가 아님"),
    ]


def test_mixed_valid_and_invalid_rows(make_csv):
    """정상 행, 빈 줄, 다양한 오류 행이 섞여 있을 때 통합 동작을 검증한다."""
    csv_text = (
        "이름,점수\n"
        "김하나,100\n"
        "\n"
        "이둘,점수없음\n"
        "박셋,0\n"
        "최넷\n"
    )
    path = make_csv(csv_text)

    kept, skipped = load_scores(path)

    assert kept == [("김하나", 100), ("박셋", 0)]
    assert skipped == [
        (4, "이둘,점수없음", "점수가 정수가 아님"),
        (6, "최넷", "열 개수가 2가 아님"),
    ]


def test_file_not_found_raises_error(tmp_path):
    """존재하지 않는 파일 경로를 전달하면 FileNotFoundError가 발생한다."""
    missing_path = tmp_path / "does_not_exist.csv"

    with pytest.raises(FileNotFoundError):
        load_scores(missing_path)


def test_invalid_encoding_raises_error(tmp_path):
    """UTF-8이 아닌 인코딩(예: CP949/EUC-KR) 파일은 UnicodeDecodeError가 발생한다."""
    cp949_file = tmp_path / "cp949_scores.csv"
    cp949_file.write_bytes("이름,점수\n홍길동,95\n".encode("cp949"))

    with pytest.raises(UnicodeDecodeError):
        load_scores(cp949_file)
