import io
import pandas as pd

# ==============================================================================
# 업체별 세부 배정 조건 초기 변수 데이터 구조화
# (중량 변수를 최소중량, 최대중량 2개로 분리)
# ==============================================================================
INITIAL_COMPANY_CONDITIONS = [
    {
        "order": 1,
        "company": "염주골",
        "importance": 5,
        "target_cnt": 20,
        "female_ratio": "100.00%",
        "payment_rate": "105.0%",
        "weight_min": 98,
        "weight_max": 109,
        "fat_str": "20~27",
        "fat_min": 20,
        "fat_max": 27,
        "grade_str": "2",
        "grades": ["2"],
        "defect_str": "",
        "no_defect_only": False,
    },
    {
        "order": 2,
        "company": "흥부축산",
        "importance": 5,
        "target_cnt": 25,
        "female_ratio": "",
        "payment_rate": "103.5%",
        "weight_min": 83,
        "weight_max": 88,
        "fat_str": "18~22",
        "fat_min": 18,
        "fat_max": 22,
        "grade_str": "1,1+,2",
        "grades": ["1", "1+", "2"],
        "defect_str": "",
        "no_defect_only": False,
    },
    {
        "order": 3,
        "company": "프라임미트",
        "importance": 4,
        "target_cnt": 110,
        "female_ratio": "70.00%",
        "payment_rate": "104.5%",
        "weight_min": 80,
        "weight_max": 103,
        "fat_str": "20~34",
        "fat_min": 20,
        "fat_max": 34,
        "grade_str": "1,1+,2",
        "grades": ["1", "1+", "2"],
        "defect_str": "",
        "no_defect_only": False,
    },
    {
        "order": 4,
        "company": "돼랑이",
        "importance": 4,
        "target_cnt": 5,
        "female_ratio": "50.00%",
        "payment_rate": "105.0%",
        "weight_min": 85,
        "weight_max": 90,
        "fat_str": "26~29",
        "fat_min": 26,
        "fat_max": 29,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "",
        "no_defect_only": False,
    },
    {
        "order": 5,
        "company": "민강",
        "importance": 1,
        "target_cnt": 60,
        "female_ratio": "100.00%",
        "payment_rate": "107.0%",
        "weight_min": 85,
        "weight_max": 97,
        "fat_str": "21~25",
        "fat_min": 21,
        "fat_max": 25,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "하자 없음",
        "no_defect_only": True,
    },
    {
        "order": 6,
        "company": "제이이",
        "importance": 2,
        "target_cnt": 15,
        "female_ratio": "100.00%",
        "payment_rate": "107.0%",
        "weight_min": 88,
        "weight_max": 97,
        "fat_str": "25~27",
        "fat_min": 25,
        "fat_max": 27,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "하자 없음",
        "no_defect_only": True,
    },
    {
        "order": 7,
        "company": "자운",
        "importance": 2,
        "target_cnt": 15,
        "female_ratio": "100.00%",
        "payment_rate": "107.5%",
        "weight_min": 85,
        "weight_max": 95,
        "fat_str": "22~25",
        "fat_min": 22,
        "fat_max": 25,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "하자 없음",
        "no_defect_only": True,
    },
    {
        "order": 8,
        "company": "승민",
        "importance": 2,
        "target_cnt": 5,
        "female_ratio": "100.00%",
        "payment_rate": "107.5%",
        "weight_min": 84,
        "weight_max": 88,
        "fat_str": "20",
        "fat_min": 20,
        "fat_max": 20,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "하자 없음",
        "no_defect_only": True,
    },
    {
        "order": 9,
        "company": "대용식품",
        "importance": 3,
        "target_cnt": 15,
        "female_ratio": "60.00%",
        "payment_rate": "107.0%",
        "weight_min": 85,
        "weight_max": 90,
        "fat_str": "18~21",
        "fat_min": 18,
        "fat_max": 21,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "하자 없음",
        "no_defect_only": True,
    },
    {
        "order": 10,
        "company": "예소야",
        "importance": 3,
        "target_cnt": 15,
        "female_ratio": "60.00%",
        "payment_rate": "107.0%",
        "weight_min": 85,
        "weight_max": 90,
        "fat_str": "18~21",
        "fat_min": 18,
        "fat_max": 21,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "하자 없음",
        "no_defect_only": True,
    },
    {
        "order": 11,
        "company": "명성",
        "importance": 3,
        "target_cnt": 4,
        "female_ratio": "80.00%",
        "payment_rate": "107.0%",
        "weight_min": 87,
        "weight_max": 97,
        "fat_str": "20~22",
        "fat_min": 20,
        "fat_max": 22,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "하자 없음",
        "no_defect_only": True,
    },
    {
        "order": 12,
        "company": "미소",
        "importance": 4,
        "target_cnt": 60,
        "female_ratio": "60.00%",
        "payment_rate": "105.0%",
        "weight_min": 85,
        "weight_max": 97,
        "fat_str": "17~27",
        "fat_min": 17,
        "fat_max": 27,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "",
        "no_defect_only": False,
    },
]


def get_company_conditions_df(conditions_list=None):
  """화면 출력 및 조건표 생성 함수"""
  target_list = (
      conditions_list if conditions_list is not None else INITIAL_COMPANY_CONDITIONS
  )

  rows = []
  for item in target_list:
    rows.append({
        "배정순서": item["order"],
        "거래처": item["company"],
        "중요도": item["importance"],
        "목표두수": item["target_cnt"],
        "암 비율": item["female_ratio"],
        "지급률": item["payment_rate"],
        "최소중량": item["weight_min"],    # 분리된 최소중량 반영
        "최대중량": item["weight_max"],    # 분리된 최대중량 반영
        "등지방(mm)": item["fat_str"],
        "등급": item["grade_str"],
        "하자": item["defect_str"],
    })
  return pd.DataFrame(rows)


def get_company_conditions_excel_bytes(conditions_list=None):
  """배정 조건표 엑셀 다운로드 파일 반환 함수"""
  df = get_company_conditions_df(conditions_list)
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="1차배정조건표", index=False)
  return output.getvalue()


def run_100pct_strict_allocation(df_valid, custom_targets=None):
  """변수 기반 1차 100% 스펙 일치 자동 배정 연산 로직"""
  pigs = df_valid.copy()
  pigs["배정거래처"] = "미분류"

  summary_rows = []

  # 배정순서 오름차순, 동일 시 중요도 내림차순 정렬
  sorted_specs = sorted(
      INITIAL_COMPANY_CONDITIONS, key=lambda x: (x["order"], -x["importance"])
  )

  for spec in sorted_specs:
    comp_name = spec["company"]

    # 동적 수정된 목표두수가 넘어올 경우 변수값 덮어쓰기
    if custom_targets is not None and comp_name in custom_targets:
      target_cnt = int(custom_targets[comp_name])
    else:
      target_cnt = spec["target_cnt"]

    unassigned_mask = pigs["배정거래처"] == "미분류"

    # 변수화된 조건 수치 매칭 (중량, 등지방, 등급, 하자)
    cond_weight = (pigs["w_num"] >= spec["weight_min"]) & (
        pigs["w_num"] <= spec["weight_max"]
    )
    cond_fat = (pigs["f_num"] >= spec["fat_min"]) & (
        pigs["f_num"] <= spec["fat_max"]
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

    # 목표두수 한도 내 할당
    allocated_indices = matched_indices[:target_cnt]
    pigs.loc[allocated_indices, "배정거래처"] = comp_name

    allocated_cnt = len(allocated_indices)
    achieve_rate = (
        f"{(allocated_cnt / target_cnt * 100):.1f}%" if target_cnt > 0 else "-"
    )

    summary_rows.append({
        "배정순서": spec["order"],
        "거래처명": comp_name,
        "목표두수": target_cnt,
        "1차 배정두수": allocated_cnt,
        "달성률": achieve_rate,
    })

  unallocated_df = pigs[pigs["배정거래처"] == "미분류"].copy()
  unallocated_cnt = len(unallocated_df)

  summary_rows.append({
      "배정순서": "-",
      "거래처명": "미분류 (잔여 물량)",
      "목표두수": "-",
      "1차 배정두수": unallocated_cnt,
      "달성률": "-",
  })

  summary_df = pd.DataFrame(summary_rows)

  return pigs, unallocated_df, summary_df
