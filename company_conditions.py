import io
import pandas as pd

# 이미지 표 기준 1차 배정 조건 데이터 (표에 표시된 행 순서 그대로 유지)
COMPANY_CONDITIONS_DATA = [
    {
        "배정순서": 1,
        "거래처": "염주골",
        "중요도": 5,
        "목표두수": 20,
        "암 비율": "100.00%",
        "지급률": "105.0%",
        "중량(kg)": "98~109",
        "등지방(mm)": "20~27",
        "등급": "2",
        "하자": "",
        "w_min": 98,
        "w_max": 109,
        "f_min": 20,
        "f_max": 27,
        "grades": ["2"],
        "no_defect_only": False,
    },
    {
        "배정순서": 3,
        "거래처": "프라임미트",
        "중요도": 4,
        "목표두수": 110,
        "암 비율": "70.00%",
        "지급률": "104.5%",
        "중량(kg)": "80~103",
        "등지방(mm)": "20~34",
        "등급": "1,1+,2",
        "하자": "",
        "w_min": 80,
        "w_max": 103,
        "f_min": 20,
        "f_max": 34,
        "grades": ["1", "1+", "2"],
        "no_defect_only": False,
    },
    {
        "배정순서": 2,
        "거래처": "흥부축산",
        "중요도": 5,
        "목표두수": 25,
        "암 비율": "",
        "지급률": "103.5%",
        "중량(kg)": "83~88",
        "등지방(mm)": "18~22",
        "등급": "1,1+,2",
        "하자": "",
        "w_min": 83,
        "w_max": 88,
        "f_min": 18,
        "f_max": 22,
        "grades": ["1", "1+", "2"],
        "no_defect_only": False,
    },
    {
        "배정순서": 7,
        "거래처": "자운",
        "중요도": 2,
        "목표두수": 15,
        "암 비율": "100.00%",
        "지급률": "107.5%",
        "중량(kg)": "85~95",
        "등지방(mm)": "22~25",
        "등급": "1,1+",
        "하자": "하자 없음",
        "w_min": 85,
        "w_max": 95,
        "f_min": 22,
        "f_max": 25,
        "grades": ["1", "1+"],
        "no_defect_only": True,
    },
    {
        "배정순서": 8,
        "거래처": "승민",
        "중요도": 2,
        "목표두수": 5,
        "암 비율": "100.00%",
        "지급률": "107.5%",
        "중량(kg)": "84~88",
        "등지방(mm)": "20",
        "등급": "1,1+",
        "하자": "하자 없음",
        "w_min": 84,
        "w_max": 88,
        "f_min": 20,
        "f_max": 20,
        "grades": ["1", "1+"],
        "no_defect_only": True,
    },
    {
        "배정순서": 6,
        "거래처": "제이이",
        "중요도": 2,
        "목표두수": 15,
        "암 비율": "100.00%",
        "지급률": "107.0%",
        "중량(kg)": "88~97",
        "등지방(mm)": "25~27",
        "등급": "1,1+",
        "하자": "하자 없음",
        "w_min": 88,
        "w_max": 97,
        "f_min": 25,
        "f_max": 27,
        "grades": ["1", "1+"],
        "no_defect_only": True,
    },
    {
        "배정순서": 4,
        "거래처": "돼랑이",
        "중요도": 4,
        "목표두수": 5,
        "암 비율": "50.00%",
        "지급률": "105.0%",
        "중량(kg)": "85~90",
        "등지방(mm)": "26~29",
        "등급": "1,1+",
        "하자": "",
        "w_min": 85,
        "w_max": 90,
        "f_min": 26,
        "f_max": 29,
        "grades": ["1", "1+"],
        "no_defect_only": False,
    },
    {
        "배정순서": 5,
        "거래처": "민강",
        "중요도": 1,
        "목표두수": 60,
        "암 비율": "100.00%",
        "지급률": "107.0%",
        "중량(kg)": "85~97",
        "등지방(mm)": "21~25",
        "등급": "1,1+",
        "하자": "하자 없음",
        "w_min": 85,
        "w_max": 97,
        "f_min": 21,
        "f_max": 25,
        "grades": ["1", "1+"],
        "no_defect_only": True,
    },
    {
        "배정순서": 9,
        "거래처": "대용식품",
        "중요도": 3,
        "목표두수": 15,
        "암 비율": "60.00%",
        "지급률": "107.0%",
        "중량(kg)": "85~90",
        "등지방(mm)": "18~21",
        "등급": "1,1+",
        "하자": "하자 없음",
        "w_min": 85,
        "w_max": 90,
        "f_min": 18,
        "f_max": 21,
        "grades": ["1", "1+"],
        "no_defect_only": True,
    },
    {
        "배정순서": 10,
        "거래처": "예소야",
        "중요도": 3,
        "목표두수": 15,
        "암 비율": "60.00%",
        "지급률": "107.0%",
        "중량(kg)": "85~90",
        "등지방(mm)": "18~21",
        "등급": "1,1+",
        "하자": "하자 없음",
        "w_min": 85,
        "w_max": 90,
        "f_min": 18,
        "f_max": 21,
        "grades": ["1", "1+"],
        "no_defect_only": True,
    },
    {
        "배정순서": 11,
        "거래처": "명성",
        "중요도": 3,
        "목표두수": 4,
        "암 비율": "80.00%",
        "지급률": "107.0%",
        "중량(kg)": "87~97",
        "등지방(mm)": "20~22",
        "등급": "1,1+",
        "하자": "하자 없음",
        "w_min": 87,
        "w_max": 97,
        "f_min": 20,
        "f_max": 22,
        "grades": ["1", "1+"],
        "no_defect_only": True,
    },
    {
        "배정순서": 12,
        "거래처": "미소",
        "중요도": 4,
        "목표두수": 60,
        "암 비율": "60.00%",
        "지급률": "105.0%",
        "중량(kg)": "85~97",
        "등지방(mm)": "17~27",
        "등급": "1,1+",
        "하자": "",
        "w_min": 85,
        "w_max": 97,
        "f_min": 17,
        "f_max": 27,
        "grades": ["1", "1+"],
        "no_defect_only": False,
    },
]


def get_company_conditions_df():
  """이미지 표 순서 그대로 데이터프레임 생성하여 반환"""
  df = pd.DataFrame(COMPANY_CONDITIONS_DATA)
  cols = [
      "배정순서",
      "거래처",
      "중요도",
      "목표두수",
      "암 비율",
      "지급률",
      "중량(kg)",
      "등지방(mm)",
      "등급",
      "하자",
  ]
  return df[cols]


def get_company_conditions_excel_bytes():
  """배정 조건표 엑셀 바이트 파일 생성"""
  df = get_company_conditions_df()
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="1차배정조건표", index=False)
  return output.getvalue()


def run_100pct_strict_allocation(df_valid):
  """1차 배정: 스펙(중량, 등지방, 등급, 하자) 100% 일치 시에만 배정하는 로직

  - 배정순서(1~12) 순으로 차례대로 처리
  - 목표두수를 채우지 못하더라도 조건 일치 건만 배정
  - 남아있는 물량은 모두 '미분류'로 반환
  """
  pigs = df_valid.copy()
  pigs["배정거래처"] = "미분류"

  summary_rows = []

  # 배정순서(1 -> 2 -> 3 ... -> 12) 숫자 순으로 정렬 후 순차 배정
  sorted_specs = sorted(COMPANY_CONDITIONS_DATA, key=lambda x: x["배정순서"])

  for spec in sorted_specs:
    comp_name = spec["거래처"]
    target_cnt = spec["목표두수"]

    # 아직 배정되지 않은 미분류 개체 필터링
    unassigned_mask = pigs["배정거래처"] == "미분류"

    # 100% 조건 판별
    cond_weight = (pigs["w_num"] >= spec["w_min"]) & (
        pigs["w_num"] <= spec["w_max"]
    )
    cond_fat = (pigs["f_num"] >= spec["f_min"]) & (
        pigs["f_num"] <= spec["f_max"]
    )
    cond_grade = pigs["grade_str"].isin(spec["grades"])

    if spec["no_defect_only"]:
      cond_defect = pigs["no_defect"] == True
      strict_mask = (
          unassigned_mask & cond_weight & cond_fat & cond_grade & cond_defect
      )
    else:
      strict_mask = unassigned_mask & cond_weight & cond_fat & cond_grade

    matched_indices = pigs[strict_mask].index

    # 목표두수 한도 내 배정 (부족하면 있는 수량만큼만 할당)
    allocated_indices = matched_indices[:target_cnt]
    pigs.loc[allocated_indices, "배정거래처"] = comp_name

    allocated_cnt = len(allocated_indices)
    achieve_rate = (
        f"{(allocated_cnt / target_cnt * 100):.1f}%" if target_cnt > 0 else "-"
    )

    summary_rows.append({
        "배정순서": spec["배정순서"],
        "거래처명": comp_name,
        "중요도": spec["중요도"],
        "목표두수": target_cnt,
        "1차 배정두수": allocated_cnt,
        "달성률": achieve_rate,
    })

  # 미분류(조건 불일치 잔여 물량) 추출
  unallocated_df = pigs[pigs["배정거래처"] == "미분류"].copy()
  unallocated_cnt = len(unallocated_df)

  summary_rows.append({
      "배정순서": "-",
      "거래처명": "미분류 (잔여 물량)",
      "중요도": "-",
      "목표두수": "-",
      "1차 배정두수": unallocated_cnt,
      "달성률": "-",
  })

  summary_df = pd.DataFrame(summary_rows)

  return pigs, unallocated_df, summary_df
