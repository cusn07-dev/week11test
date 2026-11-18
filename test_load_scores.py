import pytest
from load_scores import load_scores


def write_csv(tmp_path, content, filename="test.csv"):
    p = tmp_path / filename
    p.write_text(content, encoding="utf-8")
    return p


# 케이스 1: 파일이 없는 경우 -> FileNotFoundError 발생
def test_missing_file_raises_error(tmp_path):
    missing = tmp_path / "does_not_exist.csv"
    with pytest.raises(FileNotFoundError):
        load_scores(missing)


# 케이스 2: 헤더만 있는 경우 -> ([], []) 반환
def test_header_only_returns_empty(tmp_path):
    csv_file = write_csv(tmp_path, "이름,점수\n")
    kept, skipped = load_scores(csv_file)
    assert kept == []
    assert skipped == []


# 케이스 3: 정상 데이터 및 경계값(0점, 100점) 처리
def test_valid_and_boundary_scores(tmp_path):
    content = "이름,점수\n김민수,0\n이서연,100\n박지훈,75\n"
    csv_file = write_csv(tmp_path, content)
    kept, skipped = load_scores(csv_file)
    assert kept == [("김민수", 0), ("이서연", 100), ("박지훈", 75)]
    assert skipped == []


# 케이스 4: 열 개수가 2가 아닌 경우(1열, 3열) -> 건너뛰고 skipped 기록
def test_invalid_column_count_skipped(tmp_path):
    content = "이름,점수\n김민수\n이서연,80,추가열\n박지훈,90\n"
    csv_file = write_csv(tmp_path, content)
    kept, skipped = load_scores(csv_file)
    assert kept == [("박지훈", 90)]
    assert len(skipped) == 2
    assert skipped[0][0] == 2
    assert "열 개수" in skipped[0][2]
    assert skipped[1][0] == 3


# 케이스 5: 점수가 비었거나 정수가 아닌 경우(문자, 실수, 공백) -> 건너뛰고 skipped 기록
def test_non_integer_or_empty_score_skipped(tmp_path):
    content = "이름,점수\n김민수,\n이서연,abc\n박지훈,85.5\n최유진,88\n"
    csv_file = write_csv(tmp_path, content)
    kept, skipped = load_scores(csv_file)
    assert kept == [("최유진", 88)]
    assert len(skipped) == 3
    assert skipped[0][0] == 2
    assert skipped[1][0] == 3
    assert skipped[2][0] == 4


# 케이스 6: 점수가 0~100 범위를 벗어난 경우(-1, 101) -> 건너뛰고 skipped 기록
def test_out_of_range_score_skipped(tmp_path):
    content = "이름,점수\n김민수,-1\n이서연,101\n박지훈,60\n"
    csv_file = write_csv(tmp_path, content)
    kept, skipped = load_scores(csv_file)
    assert kept == [("박지훈", 60)]
    assert len(skipped) == 2
    assert skipped[0][0] == 2
    assert "0~100" in skipped[0][2]
    assert skipped[1][0] == 3


# 케이스 7: 이름이 비어 있는 경우(빈 문자열, 공백만 있음) -> 건너뛰고 skipped 기록
def test_empty_name_skipped(tmp_path):
    content = "이름,점수\n,85\n   ,90\n박지훈,95\n"
    csv_file = write_csv(tmp_path, content)
    kept, skipped = load_scores(csv_file)
    assert kept == [("박지훈", 95)]
    assert len(skipped) == 2
    assert skipped[0][0] == 2
    assert "이름" in skipped[0][2]
    assert skipped[1][0] == 3


# 케이스 8: 동명이인(같은 이름 중복) 및 빈 줄 처리 -> 동명이인 모두 유지, 빈 줄은 기록 없이 무시
def test_duplicate_names_kept_and_blank_lines_ignored(tmp_path):
    content = "이름,점수\n김민수,80\n\n김민수,95\n"
    csv_file = write_csv(tmp_path, content)
    kept, skipped = load_scores(csv_file)
    assert kept == [("김민수", 80), ("김민수", 95)]
    assert skipped == []
