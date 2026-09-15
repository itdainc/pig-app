import pandas as pd
import numpy as np
import io
from datetime import datetime
import sys

# ----------------- 농가/사료사 매핑 모듈 불러오기 -----------------
try:
    from farm_data import get_farm_with_feed
except ImportError:
    def get_farm_with_feed(farm_name):
        return str(farm_name).strip() if pd.notna(farm_name) else ''

# ==============================================================================
# 📌 [1] 업체별 목표 두수 변수 설정 (여기서 수량을 자유롭게 변경하세요)
# ==============================================================================
TARGET_COUNTS = {
    "염주골": 20,
    "마루푸드": 15,
    "프라임미트": 110,
    "흥부축산": 25,
    "자운": 15,
    "승민": 5,
    "제이이": 15,
    "돼랑이": 10,
    "민강": 60,
    "대용식품": 15,
    "명성": 4,
    "예소야": 20,
    "미소": 60
}

# ==============================================================================
# 📌 [2] 거래처별 스펙 및 우선순위 설정 (위 TARGET_COUNTS 변수가 자동 입력됨)
# ==============================================================================
DEFAULT_SPECS = [
    {"업체명": "염주골", "우선순위": 1, "목표두수": TARGET_COUNTS.get("염주골", 0), "지급률": "105.0%", "중량(kg)": "98~109", "등지방(mm)": "20~27", "등급": "2", "암 비율": "50%", "배제농가": ""},
    {"업체명": "마루푸드", "우선순위": 2, "목표두수": TARGET_COUNTS.get("마루푸드", 0), "지급률": "105.0%", "중량(kg)": "82~105", "등지방(mm)": "29~35", "등급": "1,1+,2", "암 비율": "50%", "배제농가": ""},
    {"업체명": "프라임미트", "우선순위": 3, "목표두수": TARGET_COUNTS.get("프라임미트", 0), "지급률": "104.5%", "중량(kg)": "80~103", "등지방(mm)": "20~34", "등급": "1,1+,2", "암 비율": "70%", "배제농가": ""},
    {"업체명": "흥부축산", "우선순위": 4, "목표두수": TARGET_COUNTS.get("흥부축산", 0), "지급률": "103.5%", "중량(kg)": "75~86", "등지방(mm)": "18~22", "등급": "1,1+,2", "암 비율": "60%", "배제농가": ""},
    {"업체명": "자운", "우선순위": 5, "목표두수": TARGET_COUNTS.get("자운", 0), "지급률": "107.5%", "중량(kg)": "85~95", "등지방(mm)": "22~25", "등급": "1,1+", "암 비율": "100%", "배제농가": ""},
    {"업체명": "승민", "우선순위": 6, "목표두수": TARGET_COUNTS.get("승민", 0), "지급률": "107.5%", "중량(kg)": "84~88", "등지방(mm)": "20~22", "등급": "1,1+", "암 비율": "100%", "배제농가": ""},
    {"업체명": "제이이", "우선순위": 7, "목표두수": TARGET_COUNTS.get("제이이", 0), "지급률": "107.0%", "중량(kg)": "88~97", "등지방(mm)": "25~27", "등급": "1,1+", "암 비율": "50%", "배제농가": ""},
    {"업체명": "돼랑이", "우선순위": 8, "목표두수": TARGET_COUNTS.get("돼랑이", 0), "지급률": "105.0%", "중량(kg)": "85~90", "등지방(mm)": "25~26", "등급": "1,1+", "암 비율": "50%", "배제농가": ""},
    {"업체명": "민강", "우선순위": 9, "목표두수": TARGET_COUNTS.get("민강", 0), "지급률": "107.0%", "중량(kg)": "85~97", "등지방(mm)": "21~25", "등급": "1,1+", "암 비율": "50%", "배제농가": ""},
    {"업체명": "대용식품", "우선순위": 10, "목표두수": TARGET_COUNTS.get("대용식품", 0), "지급률": "107.0%", "중량(kg)": "85~89", "등지방(mm)": "18~21", "등급": "1,1+", "암 비율": "60%", "배제농가": ""},
    {"업체명": "명성", "우선순위": 11, "목표두수": TARGET_COUNTS.get("명성", 0), "지급률": "107.0%", "중량(kg)": "87~97", "등지방(mm)": "20~22", "등급": "1,1+", "암 비율": "80%", "배제농가": ""},
    {"업체명": "예소야", "우선순위": 12, "목표두수": TARGET_COUNTS.get("예소야", 0), "지급률": "107.0%", "중량(kg)": "85~97", "등지방(mm)": "18~27", "등급": "1,1+,2", "암 비율": "50%", "배제농가": ""},
    {"업체명": "미소", "우선순위": 13, "목표두수": TARGET_COUNTS.get("미소", 0), "지급률": "105.0%", "중량(kg)": "80~97", "등지방(mm)": "17~25", "등급": "1,1+", "암 비율": "60%", "배제농가": ""}
]

def run_allocation(file_path):
    """
    등급판정 엑셀 파일을 읽어서 자동 배정을 수행하고 엑셀 결과물 생성
    """
    print(f"📄 등급판정 파일 읽는 중: {file_path}")

    # 1. 헤더 위치 파악
    raw_df = pd.read_excel(file_path, header=None)
    header_row_idx = 3
    for r_idx in range(min(10, len(raw_df))):
        row_vals = [str(v) for v in raw_df.iloc[r_idx].values]
        if any('도체' in v for v in row_vals) and any('중량' in v or '도체중' in v for v in row_vals):
            header_row_idx = r_idx
            break

    df_g = pd.read_excel(file_path, header=header_row_idx)

    # 2. 열 찾기 함수
    def find_col(possible_names, default_idx):
        for col in df_g.columns:
            col_clean = str(col).replace('\n', '').replace(' ', '')
            for p in possible_names:
                if p in col_clean:
                    return col
        if df_g.shape[1] > default_idx:
            return df_g.columns[default_idx]
        return None

    col_pig_no = find_col(['도체번호', '도체'], 4)
    col_sex = find_col(['성별', '성'], 7)
    col_weight = find_col(['도체중', '중량'], 8)
    col_fat = find_col(['등지방', '지방두께'], 9)
    col_grade = find_col(['최종등급', '등급'], 22)
    col_farm = find_col(['출하농가', '농가명', '농가', '출하자'], 21)
    col_history = find_col(['이력번호', '이력'], 999)

    def clean_history_no(val):
        if pd.isna(val) or val is None:
            return ''
        s_val = str(val).strip()
        if '.' in s_val:
            s_val = s_val.split('.')[0]
        if s_val in ['nan', 'None', '0']:
            return ''
        return s_val

    def parse_farm_with_feed(val):
        if pd.isna(val) or val is None:
            return ''
        s_val = str(val).strip()
        if s_val in ['nan', 'None', '0']:
            return ''
        return get_farm_with_feed(s_val)

    # 3. 돼지 개체 데이터 생성
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

    # 4. 스펙 파싱 및 정렬
    specs = []
    specs_dict = {}
    spec_df = pd.DataFrame(DEFAULT_SPECS)

    for idx, row in spec_df.iterrows():
        name = str(row['업체명']).strip()
        prio = int(row['우선순위']) if pd.notna(row['우선순위']) else 99
        base_target = int(row['목표두수']) if pd.notna(row['목표두수']) else 0
        
        # 목표두수 ±10% 허용범위 설정
        max_target = int(round(base_target * 1.10)) if base_target > 0 else 0
        
        weight_str = str(row['중량(kg)'])
        fat_str = str(row['등지방(mm)'])
        grade_str = str(row['등급'])
        f_ratio_str = str(row['암 비율'])
        
        exclude_farms_str = str(row.get('배정농가', row.get('배제농가', '')))
        exclude_farms = [f.strip() for f in exclude_farms_str.split(',') if f.strip() and f.strip() != 'nan']

        w_min, w_max = (map(float, weight_str.split('~')) if '~' in weight_str 
                        else (float(weight_str), float(weight_str)) if weight_str!='nan' else (0, 999))
        f_min, f_max = (map(float, fat_str.split('~')) if '~' in fat_str 
                        else (float(fat_str), float(fat_str)) if fat_str!='nan' else (0, 999))
        grades = [g.strip() for g in grade_str.split(',')] if grade_str != 'nan' else []

        f_ratio_val = float(f_ratio_str.replace('%', '')) / 100.0 if '%' in f_ratio_str else 0.5
        c_ratio_val = 1.0 - f_ratio_val

        spec_obj = {
            '업체명': name, '우선순위': prio, '목표두수': base_target, '최대목표두수': max_target,
            'w_min': w_min, 'w_max': w_max,
            'f_min': f_min, 'f_max': f_max, 'grades': grades,
            '암비율_val': f_ratio_val, '거세비율_val': c_ratio_val,
            'weight_str': weight_str, 'fat_str': fat_str, 'grade_str': grade_str,
            'f_ratio_str': f_ratio_str, '배제농가': exclude_farms
        }
        specs.append(spec_obj)
        specs_dict[name] = spec_obj

    specs.sort(key=lambda x: x['우선순위'])

    pigs['배정거래처'] = '미배정'

    # 5. 순차 배정 실행 (우선순위별 배정)
    for spec in specs:
        company = spec['업체명']
        target = spec['최대목표두수']
        if target <= 0:
            continue

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
            target_f = int(round(target * spec['암비율_val']))
            target_c = target - target_f

            matched_f = matched_all[matched_all['성별'] == '암'].head(target_f)
            matched_c = matched_all[matched_all['성별'] == '거세'].head(target_c)

            pigs.loc[matched_f.index, '배정거래처'] = company
            pigs.loc[matched_c.index, '배정거래처'] = company

            curr_assigned = len(pigs[pigs['배정거래처'] == company])
            if curr_assigned < target:
                needed = target - curr_assigned
                rem_matched = pigs[cond_spec & (pigs['배정거래처'] == '미배정')].head(needed)
                pigs.loc[rem_matched.index, '배정거래처'] = company

        curr_assigned = len(pigs[pigs['배정거래처'] == company])
        if curr_assigned < target:
            needed = target - curr_assigned
            candidates = pigs[cond_base & (pigs['배정거래처'] == '미배정')].copy()
            if not candidates.empty:
                w_diff = np.maximum(0, np.maximum(spec['w_min'] - candidates['중량'], candidates['중량'] - spec['w_max']))
                f_diff = np.maximum(0, np.maximum(spec['f_min'] - candidates['등지방'], candidates['등지방'] - spec['f_max']))
                candidates['score'] = w_diff * 1.5 + f_diff

                matched_relaxed = candidates.sort_values('score').head(needed)
                pigs.loc[matched_relaxed.index, '배정거래처'] = company

    # 6. '잇다' 배정 (최대 110두 제한)
    unassigned_indices = pigs[pigs['배정거래처'] == '미배정'].index
    ita_indices = unassigned_indices[:110]
    pigs.loc[ita_indices, '배정거래처'] = '잇다'

    # 110두 초과 잔여 물량 '예소야' 및 타 거래처 추가 흡수
    over_indices = unassigned_indices[110:]
    if len(over_indices) > 0:
        yesoya_spec = specs_dict.get('예소야')
        if yesoya_spec:
            assign_yesoya = over_indices[:yesoya_spec['최대목표두수']]
            pigs.loc[assign_yesoya, '배정거래처'] = '예소야'
            over_indices = over_indices[len(assign_yesoya):]

        if len(over_indices) > 0:
            for spec in specs:
                comp = spec['업체명']
                if comp == '예소야' or len(over_indices) == 0:
                    continue
                rem_needed = spec['최대목표두수'] - len(pigs[pigs['배정거래처'] == comp])
                if rem_needed > 0:
                    assign_now = over_indices[:rem_needed]
                    pigs.loc[assign_now, '배정거래처'] = comp
                    over_indices = over_indices[rem_needed:]

        pigs.loc[pigs['배정거래처'] == '미배정', '배정거래처'] = '잇다'

    # 7. 요약표 및 엑셀 다운로드 생성
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_filename = f"{today_str}_배정결과.xlsx"

    summary = pigs.groupby(['배정거래처', '성별']).size().unstack(fill_value=0)
    if '거세' not in summary.columns: summary['거세'] = 0
    if '암' not in summary.columns: summary['암'] = 0
    summary['합계'] = summary['거세'] + summary['암']
    summary = summary[['합계', '거세', '암']]

    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
        pigs.to_excel(writer, sheet_name='전체배정내역', index=True)
        summary.to_excel(writer, sheet_name='요약')

    print(f"✅ 배정 완료! 결과 파일이 저장되었습니다: {output_filename}")
    print("\n[📊 거래처별 배정 요약]")
    print(summary)

# ----------------- 실행부 -----------------
if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input("📌 등급판정 엑셀 파일 경로를 입력하세요: ").strip().strip('"')
    
    run_allocation(file_path)
