import io
import pandas as pd

# ==============================================================================
# 업체별 세부 배정 조건 초기 변수 데이터 구조화
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
        "fat_min": 20,
        "fat_max": 27,
        "grade_str": "2",
        "grades": ["2"],
        "defect_str": "",
        "no_defect_only": False,
        "exclude_farms": "",
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
        "fat_min": 18,
        "fat_max": 22,
        "grade_str": "1,1+,2",
        "grades": ["1", "1+", "2"],
        "defect_str": "",
        "no_defect_only": False,
        "exclude_farms": "",
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
        "fat_min": 20,
        "fat_max": 34,
        "grade_str": "1,1+,2",
        "grades": ["1", "1+", "2"],
        "defect_str": "",
        "no_defect_only": False,
        "exclude_farms": "",
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
        "fat_min": 26,
        "fat_max": 29,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "",
        "no_defect_only": False,
        "exclude_farms": "",
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
        "fat_min": 21,
        "fat_max": 25,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "하자 없음",
        "no_defect_only": True,
        "exclude_farms": "",
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
        "fat_min": 25,
        "fat_max": 27,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "하자 없음",
        "no_defect_only": True,
        "exclude_farms": "",
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
        "fat_min": 22,
        "fat_max": 25,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "하자 없음",
        "no_defect_only": True,
        "exclude_farms": "",
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
        "fat_min": 20,
        "fat_max": 20,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "하자 없음",
        "no_defect_only": True,
        "exclude_farms": "",
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
        "fat_min": 18,
        "fat_max": 21,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "하자 없음",
        "no_defect_only": True,
        "exclude_farms": "",
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
        "fat_min": 18,
        "fat_max": 21,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "하자 없음",
        "no_defect_only": True,
        "exclude_farms": "",
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
        "fat_min": 20,
        "fat_max": 22,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "하자 없음",
        "no_defect_only": True,
        "exclude_farms": "",
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
        "fat_min": 17,
        "fat_max": 27,
        "grade_str": "1,1+",
        "grades": ["1", "1+"],
        "defect_str": "",
        "no_defect_only": False,
        "exclude_farms": "",
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
        "최소 중량": item["weight_min"],
        "최대 중량": item["weight_max"],
        "최소 등지방": item["fat_min"],
        "최대 등지방": item["fat_max"],
        "등급": item["grade_str"],
        "하자": item["defect_str"],
        "배제농가": item.get("exclude_farms", ""),
    })
  return pd.DataFrame(rows)


def get_company_conditions_excel_bytes(conditions_list=None):
  """배정 조건표 엑셀 다운로드 파일 반환 함수"""
  df = get_company_conditions_df(conditions_list)
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="1차배정조건표", index=False)
  return output.getvalue()


def run_100pct_strict_allocation(df_valid, custom_conditions_df=None):
  """동적 커스텀 조건표를 반영한 1차 100% 스펙 일치 자동 배정 연산 로직"""
  pigs = df_valid.copy()
  pigs["배정거래처"] = "미분류"

  summary_rows = []

  # 커스텀 조건표 딕셔너리화
  custom_dict = {}
  if custom_conditions_df is not None and not custom_conditions_df.empty:
    custom_dict = custom_conditions_df.set_index("거래처").to_dict("index")

  sorted_specs = sorted(
      INITIAL_COMPANY_CONDITIONS, key=lambda x: (x["order"], -x["importance"])
  )

  for spec in sorted_specs:
    comp_name = spec["company"]

    # 사용자 지정 동적 수정 조건 반영
    if comp_name in custom_dict:
      row_c = custom_dict[comp_name]
      try:
        target_cnt = int(row_c.get("목표두수", spec["target_cnt"]))
      except Exception:
        target_cnt = spec["target_cnt"]

      try:
        weight_min = float(row_c.get("최소 중량", spec["weight_min"]))
      except Exception:
        weight_min = spec["weight_min"]

      try:
        weight_max = float(row_c.get("최대 중량", spec["weight_max"]))
      except Exception:
        weight_max = spec["weight_max"]

      try:
        fat_min = float(row_c.get("최소 등지방", spec["fat_min"]))
      except Exception:
        fat_min = spec["fat_min"]

      try:
        fat_max = float(row_c.get("최대 등지방", spec["fat_max"]))
      except Exception:
        fat_max = spec["fat_max"]

      grade_str_val = str(row_c.get("등급", spec["grade_str"]))
      grades = [g.strip() for g in grade_str_val.split(",") if g.strip()]

      defect_val = str(row_c.get("하자", spec["defect_str"])).strip()
      no_defect_only = True if "없음" in defect_val else False

      exclude_str = str(
          row_c.get("배제농가", spec.get("exclude_farms", ""))
      ).strip()
      if exclude_str.lower() in ["nan", "none"]:
        exclude_str = ""
    else:
      target_cnt = spec["target_cnt"]
      weight_min = spec["weight_min"]
      weight_max = spec["weight_max"]
      fat_min = spec["fat_min"]
      fat_max = spec["fat_max"]
      grades = spec["grades"]
      no_defect_only = spec["no_defect_only"]
      exclude_str = spec.get("exclude_farms", "")

    unassigned_mask = pigs["배정거래처"] == "미분류"

    cond_weight = (pigs["w_num"] >= weight_min) & (pigs["w_num"] <= weight_max)
    cond_fat = (pigs["f_num"] >= fat_min) & (pigs["f_num"] <= fat_max)
    cond_grade = pigs["grade_str"].isin(grades)

    strict_mask = unassigned_mask & cond_weight & cond_fat & cond_grade

    if no_defect_only:
      strict_mask = strict_mask & (pigs["no_defect"] == True)

    if exclude_str and "farm_name" in pigs.columns:
      exclude_list = [
          f.strip() for f in str(exclude_str).split(",") if f.strip()
      ]
      if exclude_list:
        cond_not_excluded = ~pigs["farm_name"].isin(exclude_list)
        strict_mask = strict_mask & cond_not_excluded

    matched_indices = pigs[strict_mask].index

    allocated_indices = matched_indices[:target_cnt]
    pigs.loc[allocated_indices, "배정거래처"] = comp_name

    allocated_cnt = len(allocated_indices)

    summary_rows.append({
        "배정순서": spec["order"],
        "거래처명": comp_name,
        "목표두수": target_cnt,
        "1차 배정두수": allocated_cnt,
    })

  unallocated_df = pigs[pigs["배정거래처"] == "미분류"].copy()
  unallocated_cnt = len(unallocated_df)

  summary_rows.append({
      "배정순서": "-",
      "거래처명": "미분류 (잔여 물량)",
      "목표두수": "-",
      "1차 배정두수": unallocated_cnt,
  })

  summary_df = pd.DataFrame(summary_rows)

  return pigs, unallocated_df, summary_df
