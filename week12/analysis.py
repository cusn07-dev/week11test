"""12주차 데이터 정제 및 분석
실행: python analysis.py
필요 패키지: pandas
"""
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
원본 = pd.read_csv(DATA_DIR / "scores_2026.csv", encoding="utf-8", dtype={"학번": str})
미니원본 = pd.read_csv(DATA_DIR / "mini.csv", encoding="utf-8", dtype={"학번": str})


def 정제(df):
    """원본을 보존하고 결측·중복·공백·점수 범위를 정리한 복사본을 반환한다."""
    결과 = df.copy()

    # 점수가 비어 있는 행은 계산할 수 없으므로 삭제한다.
    결과 = 결과.dropna(subset=["점수"])
    print("점수 빈칸 삭제 후:", len(결과), "행")

    # 모든 열이 완전히 같은 중복 행은 한 행만 남긴다.
    결과 = 결과.drop_duplicates()
    print("완전 중복 제거 후:", len(결과), "행")

    # 반과 과목 이름의 앞뒤 공백을 제거한다.
    결과["반"] = 결과["반"].astype(str).str.strip()
    결과["과목"] = 결과["과목"].astype(str).str.strip()
    print("공백 제거 후:", len(결과), "행")

    # 점수를 숫자로 바꾸고 0~100 범위를 벗어난 행은 삭제한다.
    결과["점수"] = pd.to_numeric(결과["점수"], errors="coerce")
    결과 = 결과[결과["점수"].between(0, 100)].copy()
    결과["점수"] = 결과["점수"].astype(int)
    print("점수 범위 검사 후:", len(결과), "행")
    return 결과


def 반별평균(df):
    """반 이름을 키로 하는 평균값 Series를 반환한다."""
    return df.groupby("반")["점수"].mean().round(2)


def 분석(df):
    """실습에서 요구한 그룹화·통계 결과를 출력한다."""
    print("\n[수학 필터링]")
    수학 = df[df["과목"] == "수학"]
    print(수학)
    print("수학 행 수:", len(수학))

    print("\n[응용 필터링: 1반이면서 90점 이상]")
    print(df[(df["반"] == "1반") & (df["점수"] >= 90)])

    print("\n[반별 평균]")
    print(df.groupby("반")["점수"].mean().round(2))

    print("\n[과목 × 반 평균]")
    print(df.groupby(["과목", "반"])["점수"].mean().round(2))

    print("\n[반별 개수·평균·중앙값·최댓값]")
    print(df.groupby("반")["점수"].agg(
        개수="count", 평균="mean", 중앙값="median", 최댓값="max"
    ).round(2))

    print("\n[합계 검증]")
    반별합계 = df.groupby("반")["점수"].sum()
    print("반별 합계의 합:", int(반별합계.sum()))
    print("전체 합계:", int(df["점수"].sum()))


if __name__ == "__main__":
    print("=== scores_2026.csv 정제 ===")
    정제데이터 = 정제(원본)
    분석(정제데이터)
    print("\n[mini.csv 손계산 대조]")
    미니정제 = 정제(미니원본)
    print("반별 평균:", 반별평균(미니정제).to_dict())
