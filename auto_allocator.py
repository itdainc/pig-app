import pandas as pd
import numpy as np

# ----------------- 농가/사료사 매핑 모듈 불러오기 -----------------
try:
    from farm_data import get_farm_with_feed
except ImportError:
    def get_farm_with_feed(farm_name):
        return str(farm_name).strip() if pd.notna(farm_name) else ''

# ==============================================================================
# 📌 [1] 기본 업체별 목표 두수 변수 (초기 기본값)
# ==============================================================================
DEFAULT_TARGET_COUNTS = {
    "염주골 1": 20, "염주골 2": 0,
    "마루푸드": 15,
    "프라임미트": 110,
    "흥부축산 1": 25, "흥부축산 2": 0,
    "자운": 15,
    "승민 1": 5, "승민 2": 0,
    "제이이": 15,
    "돼랑이": 10,
    "민강 1": 60, "민강 2": 0,
    "대용식품": 15,
    "명성": 4,
    "예소야": 20,
    "미소 1": 60, "미소 2": 0, "미소 3": 0
}

# ==============================================================================
# 📌 [2] 거래처별 기본 스펙 템플릿
# ==============================================================================
def get_default_specs(custom_targets=None):
    targets = custom_targets if custom_targets else DEFAULT_TARGET_COUNTS
    return [
        {"업체명": "염주골 1", "우선순위": 1, "목표두수": targets.get("염주골 1", 20), "지급률": "105.0%", "중량(kg)": "98~109", "등지방(mm)": "20~27", "등급": "2", "암 비율": "50%", "배제농가": ""},
        {"업체명": "염주골 2", "우선순위": 2, "목표두수": targets.get("염주골 2", 0), "지급률": "105.0%", "중량(kg)": "110~120", "등지방(mm)": "20~35", "등급": "2,등외", "암 비율": "50%", "배제농가": ""},
        
        {"업체명": "마루푸드", "우선순위": 3, "목표두수": targets.get("마루푸드", 15), "지급률": "105.0%", "중량(kg)": "82~105", "등지방(mm)": "29~35", "등급": "1,1+,2", "암 비율": "50%", "배제농가": ""},
        {"업체명": "프라임미트", "우선순위": 4, "목표두수": targets.get("프라임미트", 110), "지급률": "104.5%", "중량(kg)": "80~103", "등지방(mm)": "20~34", "등급": "1,1+,2", "암 비율": "70%", "배제농가": ""},
        
        {"업체명": "흥부축산 1", "우선순위": 5, "목표두수": targets.get("흥부축산 1", 25), "지급률": "103.5%", "중량(kg)": "80~86", "등지방(mm)": "18~22", "등급": "1,1+", "암 비율": "60%", "배제농가": ""},
        {"업체명": "흥부축산 2", "우선순위": 6, "목표두수": targets.get("흥부축산 2", 0), "지급률": "103.5%", "중량(kg)": "75~79", "등지방(mm)": "18~24", "등급": "1,1+,2", "암 비율": "60%", "배제농가": ""},
        
        {"업체명": "자운", "우선순위": 7, "목표두수": targets.get("자운", 15), "지급률": "107.5%", "중량(kg)": "85~95", "등지방(mm)": "22~25", "등급": "1,1+", "암 비율": "100%", "배제농가": ""},
        
        {"업체명": "승민 1", "우선순위": 8, "목표두수": targets.get("승민 1", 5), "지급률": "107.5%", "중량(kg)": "84~88", "등지방(mm)": "20~22", "등급": "1,1+", "암 비율": "100%", "배제농가": ""},
        {"업체명": "승민 2", "우선순위": 9, "목표두수": targets.get("승민 2", 0), "지급률": "107.5%", "중량(kg)": "80~83", "등지방(mm)": "18~25", "등급": "1,1+,2", "암 비율": "100%", "배제농가": ""},
        
        {"업체명": "제이이", "우선순위": 10, "목표두수": targets.get("제이이", 15), "지급률": "107.0%", "중량(kg)": "88~97", "등지방(mm)": "25~27", "등급": "1,1+", "암 비율": "50%", "배제농가": ""},
        {"업체명": "돼랑이", "우선순위": 11, "목표두수": targets.get("돼랑이", 10), "지급률": "105.0%", "중량(kg)": "85~90", "등지방(mm)": "25~26", "등급": "1,1+", "암 비율": "50%", "배제농가": ""},
        
        {"업체명": "민강 1", "우선순위": 12, "목표두수": targets.get("민강 1", 60), "지급률": "107.0%", "중량(kg)": "85~97", "등지방(mm)": "21~25", "등급": "1,1+", "암 비율": "50%", "배제농가": ""},
        {"업체명": "민강 2", "우선순위": 13, "목표두수": targets.get("민강 2", 0), "지급률": "107.0%", "중량(kg)": "83~84", "등지방(mm)": "18~25", "등급": "1,1+,2", "암 비율": "50%", "배제농가": ""},
        
        {"업체명": "대용식품", "우선순위": 14, "목표두수": targets.get("대용식품", 15), "지급률": "107.0%", "중량(kg)": "85~89", "등지방(mm)": "18~21", "등급": "1,1+", "암 비율": "60%", "배제농가": ""},
        {"업체명": "명성", "우선순위": 15, "목표두수": targets.get("명성", 4), "지급률": "107.0%", "중량(kg)": "87~97", "등지방(mm)": "20~22", "등급": "1,1+", "암 비율": "80%", "배제농가": ""},
        {"업체명": "예소야", "우선순위": 16, "목표두수": targets.get("예소야", 20), "지급률": "107.0%", "중량(kg)": "85~97", "등지방(mm)": "18~27", "등급": "1,1+,2", "암 비율": "50%", "배제농가": ""},
        
        {"업체명": "미소 1", "우선순위": 17, "목표두수": targets.get("미소 1", 60), "지급률": "105.0%", "중량(kg)": "85~97", "등지방(mm)": "17~25", "등급": "1,1+", "암 비율": "60%", "배제농가": ""},
        {"업체명": "미소 2", "우선순위": 18, "목표두수": targets.get("미소 2", 0), "지급률": "105.0%", "중량(kg)": "80~84", "등지방(mm)": "18~25", "등급": "1,1+,2", "암 비율": "60%", "배제농가": ""},
        {"업체명": "미소 3", "우선순위": 19, "목표두수": targets.get("미소 3", 0), "지급률": "105.0%", "중량(kg)": "84~97", "등지방(mm)": "15~16", "등급": "1,1+,2", "암 비율": "60%", "배제농가": ""}
    ]

DEFAULT_SPECS = get_default_specs()

def parse_range(val_str, default_min=0.0, default_max=999.0):
    if pd.isna(val_str) or val_str is None: return default_min, default_max
    s = str(val_str).strip()
    if s.lower() in ['none', 'nan', '', '-']: return default_min, default_max
    if '~' in s:
        parts = s.split('~')
        try: return float(parts[0].strip()), float(parts[1].strip())
        except ValueError: return default_min, default_max
    else:
        try:
            v = float(s)
            return v, v
        except ValueError: return default_min, default_max

def parse_ratio(f_ratio_str, default_ratio=0.5):
    if pd.isna(f_ratio_str) or f_ratio_str is None: return default_ratio
    s = str(f_ratio_str).strip()
    if s.lower() in ['none', 'nan', '', '-']: return default_ratio
    s = s.replace('%', '')
    try:
        val = float(s)
        return val / 100.0 if val > 1.0 else val
    except ValueError: return default_ratio

def allocate_pigs_data(uploaded_file, current_spec_df=None):
    raw_df = pd.read_excel(uploaded_file, header=None)
    header_row_idx = 3
    for r_idx in range(min(10, len(raw_df))):
        row_vals = [str(v) for v in raw_df.iloc[r_idx].values]
        if any('도체' in v for v in row_vals) and any('중량' in v or '도체중' in v for v in row_vals):
            header_row_idx = r_idx
            break

    df_g = pd.read_excel(uploaded_file, header=header_row_idx)

    def find_col(possible_names, default_idx):
        for col in df_g.columns:
            col_clean = str(col).replace('\n', '').replace(' ', '')
            for p in possible_names:
                if p in col_clean: return col
        if df_g.shape[1] > default_idx: return df_g.columns[default_idx]
        return None

    col_pig_no = find_col(['도체번호', '도체'], 4)
    col_sex = find_col(['성별', '성'], 7)
    col_weight = find_col(['도체중', '중량'], 8)
    col_fat = find_col(['등지방', '지방두께'], 9)
    col_grade = find_col(['최종등급', '등급'], 22)
    col_farm = find_col(['출하농가', '농가명', '농가', '출하자'], 21)
    col_history = find_col(['이력번호', '이력'], 999)

    def clean_history_no(val):
        if pd.isna(val) or val is None: return ''
        s_val = str(val).strip()
        if '.' in s_val: s_val = s_val.split('.')[0]
        if s_val in ['nan', 'None', '0']: return ''
        return s_val

    def parse_farm_with_feed(val):
        if pd.isna(val) or val is None: return ''
        s_val = str(val).strip()
        if s_val in ['nan', 'None', '0']: return ''
        return get_farm_with_feed(s_val)

    pigs = pd.DataFrame({
        '도체번호': pd.to_numeric(df_g[col_pig_no], errors='coerce').fillna(0).astype(int) if col_pig_no else 0,
        '성별': df_g[col_sex].astype(str).str.strip() if col_sex else '',
        '중량': pd.to_numeric(df_g[col_weight], errors='coerce') if col_weight else 0.0,
        '등지방': pd.to_numeric(df_g[col_fat], errors='coerce') if col_fat else 0.0,
        '등급': df_g[col_grade].astype(str).str.strip() if col_grade else '',
        '출하농가': df_g[col_farm].apply(parse_farm_with_feed) if col_farm else '',
        '이력번호': df_g[col_history].apply(clean_history_no) if col_history else ''
    }).dropna(subset=['중량']).copy()

    pigs.reset_index(drop=True, inplace=True)
    pigs.index = pigs.index + 1

    spec_data = current_spec_df if (current_spec_df is not None and not current_spec_df.empty) else pd.DataFrame(DEFAULT_SPECS)

    specs = []
    specs_dict = {}
    for idx, row in spec_data.iterrows():
        name = str(row['업체명']).strip()
        if not name or name.lower() in ['none', 'nan']: continue
            
        prio = int(row['우선순위']) if (pd.notna(row['우선순위']) and str(row['우선순위']).isdigit()) else 99
        base_target = int(row['목표두수']) if (pd.notna(row['목표두수']) and str(row['목표두수']).isdigit()) else 0
        max_target = int(round(base_target * 1.10)) if base_target > 0 else 0
        
        weight_str = str(row['중량(kg)'])
        fat_str = str(row['등지방(mm)'])
        grade_str = str(row['등급'])
        f_ratio_str = str(row['암 비율'])
        
        exclude_farms_str = str(row.get('배정농가', row.get('배제농가', '')))
        exclude_farms = [f.strip() for f in exclude_farms_str.split(',') if f.strip() and f.strip().lower() not in ['nan', 'none']]

        w_min, w_max = parse_range(weight_str, 0.0, 999.0)
        f_min, f_max = parse_range(fat_str, 0.0, 999.0)
        
        grades = [g.strip() for g in grade_str.split(',') if g.strip() and g.strip().lower() not in ['nan', 'none']] if grade_str.lower() not in ['nan', 'none'] else []

        f_ratio_val = parse_ratio(f_ratio_str, 0.5)
        c_ratio_val = 1.0 - f_ratio_val

        spec_obj = {
            '업체명': name, '우선순위': prio, '목표두수': base_target, '최대목표두수': max_target,
            'w_min': w_min, 'w_max': w_max, 'f_min': f_min, 'f_max': f_max, 'grades': grades,
            '암비율_val': f_ratio_val, '거세비율_val': c_ratio_val,
            'weight_str': weight_str, 'fat_str': fat_str, 'grade_str': grade_str,
            'f_ratio_str': f_ratio_str, '배제농가': exclude_farms
        }
        specs.append(spec_obj)
        specs_dict[name] = spec_obj

    specs.sort(key=lambda x: x['우선순위'])
    pigs['배정거래처'] = '미배정'

    # 1. 잇다 2 (스펙 불량 개체 우선 흡수: 등지방 10mm 이하, 등외 등)
    bad_pigs_mask = (pigs['등지방'] <= 10.0) | (pigs['등급'] == '등외')
    pigs.loc[bad_pigs_mask, '배정거래처'] = '잇다 2'

    # 2. 일반 거래처 순차 배정
    for spec in specs:
        company = spec['업체명']
        target = spec['최대목표두수']
        if target <= 0 and "2" not in company and "3" not in company: continue

        cond_base = (pigs['배정거래처'] == '미배정')
        if spec['배제농가']:
            for farm in spec['배제농가']:
                cond_base &= (~pigs['출하농가'].str.contains(farm, na=False))

        cond_spec = cond_base & (
            (pigs['중량'] >= spec['w_min']) & (pigs['중량'] <= spec['w_max']) &
            (pigs['등지방'] >= spec['f_min']) & (pigs['등지방'] <= spec['f_max'])
        )
        if spec['grades']:
            cond_spec &= (pigs['등급'].isin(spec['grades']))

        matched_all = pigs[cond_spec]

        if not matched_all.empty:
            target_f = int(round(target * spec['암비율_val'])) if target > 0 else len(matched_all)
            target_c = (target - target_f) if target > 0 else len(matched_all)

            matched_f = matched_all[matched_all['성별'] == '암'].head(max(0, target_f))
            matched_c = matched_all[matched_all['성별'] == '거세'].head(max(0, target_c))

            pigs.loc[matched_f.index, '배정거래처'] = company
            pigs.loc[matched_c.index, '배정거래처'] = company

            curr_assigned = len(pigs[pigs['배정거래처'] == company])
            if target > 0 and curr_assigned < target:
                needed = target - curr_assigned
                rem_matched = pigs[cond_spec & (pigs['배정거래처'] == '미배정')].head(needed)
                pigs.loc[rem_matched.index, '배정거래처'] = company

    # 3. '잇다 1' 채널 배정 (100~110두 보장)
    unassigned_indices = pigs[pigs['배정거래처'] == '미배정'].index
    unassigned_cnt = len(unassigned_indices)

    if unassigned_cnt < 100:
        needed_for_ita = 100 - unassigned_cnt
        for spec in reversed(specs):
            if needed_for_ita <= 0: break
            comp = spec['업체명']
            comp_indices = pigs[pigs['배정거래처'] == comp].index
            if len(comp_indices) > 0:
                take_cnt = min(needed_for_ita, len(comp_indices))
                take_indices = comp_indices[-take_cnt:]
                pigs.loc[take_indices, '배정거래처'] = '미배정'
                needed_for_ita -= take_cnt

        unassigned_indices = pigs[pigs['배정거래처'] == '미배정'].index

    ita_count = min(110, max(100, len(unassigned_indices)))
    ita_indices = unassigned_indices[:ita_count]
    pigs.loc[ita_indices, '배정거래처'] = '잇다 1'

    # 초과분 추가 흡수
    over_indices = pigs[pigs['배정거래처'] == '미배정'].index
    if len(over_indices) > 0:
        yesoya_spec = specs_dict.get('예소야')
        if yesoya_spec:
            assign_yesoya = over_indices[:yesoya_spec['최대목표두수']]
            pigs.loc[assign_yesoya, '배정거래처'] = '예소야'
            over_indices = pigs[pigs['배정거래처'] == '미배정'].index

        if len(over_indices) > 0:
            for spec in specs:
                comp = spec['업체명']
                if comp == '예소야' or len(over_indices) == 0: continue
                rem_needed = spec['최대목표두수'] - len(pigs[pigs['배정거래처'] == comp])
                if rem_needed > 0:
                    assign_now = over_indices[:rem_needed]
                    pigs.loc[assign_now, '배정거래처'] = comp
                    over_indices = pigs[pigs['배정거래처'] == '미배정'].index

        pigs.loc[pigs['배정거래처'] == '미배정', '배정거래처'] = '잇다 1'

    return pigs, specs_dict
