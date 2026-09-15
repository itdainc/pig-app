import streamlit as st
import pandas as pd
import io
import numpy as np
from datetime import datetime

# ----------------- 농가/사료사 데이터 모듈 불러오기 -----------------
try:
    from farm_data import get_farm_with_feed
except ImportError:
    def get_farm_with_feed(farm_name):
        return str(farm_name).strip() if pd.notna(farm_name) else ''

st.set_page_config(page_title="주식회사 잇다 / 자동 배정 및 농가 분석 시스템", layout="wide", page_icon="🐖")

# ----------------- 세션 상태(Session State) 초기화 -----------------
if 'main_menu' not in st.session_state:
    st.session_state.main_menu = "배정"

# ----------------- 사이드바 메인 메뉴 (세로 버튼) -----------------
st.sidebar.title("📌 메인 메뉴")

if st.sidebar.button(
    "🏢 1. 거래처 자동 배정 시스템", 
    type="primary" if st.session_state.main_menu == "배정" else "secondary", 
    use_container_width=True
):
    st.session_state.main_menu = "배정"
    st.rerun()

if st.sidebar.button(
    "📊 2. 농가 분석", 
    type="primary" if st.session_state.main_menu == "농가분석" else "secondary", 
    use_container_width=True
):
    st.session_state.main_menu = "농가분석"
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("📁 파일 업로드")
uploaded_grade = st.sidebar.file_uploader("1. 등급판정 결과 파일 (.xls/.xlsx)", type=["xls", "xlsx"])

# 기본 스펙 데이터 설정
default_specs = [
    {"업체명": "대용식품", "우선순위": 3, "목표두수": 15, "지급률": "107.0%", "중량(kg)": "85~90", "등지방(mm)": "18~21", "등급": "1,1+", "암 비율": "60%", "외관": "", "육질": "", "결함": "", "배제농가": ""},
    {"업체명": "민강", "우선순위": 1, "목표두수": 60, "지급률": "107.0%", "중량(kg)": "85~97", "등지방(mm)": "21~25", "등급": "1,1+", "암 비율": "50%", "외관": "", "육질": "", "결함": "", "배제농가": ""},
    {"업체명": "예소야", "우선순위": 3, "목표두수": 20, "지급률": "107.0%", "중량(kg)": "85~97", "등지방(mm)": "22~25", "등급": "1,1+", "암 비율": "60%", "외관": "", "육질": "", "결함": "", "배제농가": ""},
    {"업체명": "승민", "우선순위": 2, "목표두수": 5, "지급률": "107.5%", "중량(kg)": "84~88", "등지방(mm)": "20", "등급": "1,1+", "암 비율": "100%", "외관": "", "육질": "", "결함": "", "배제농가": ""},
    {"업체명": "자운", "우선순위": 2, "목표두수": 15, "지급률": "107.5%", "중량(kg)": "85~95", "등지방(mm)": "22~25", "등급": "1,1+", "암 비율": "100%", "외관": "", "육질": "", "결함": "", "배제농가": ""},
    {"업체명": "제이이", "우선순위": 3, "목표두수": 15, "지급률": "107.0%", "중량(kg)": "88~97", "등지방(mm)": "25~27", "등급": "1,1+", "암 비율": "50%", "외관": "", "육질": "", "결함": "", "배제농가": ""},
    {"업체명": "돼랑이", "우선순위": 99, "목표두수": 0, "지급률": "105.0%", "중량(kg)": "85~90", "등지방(mm)": "25~26", "등급": "1,1+", "암 비율": "50%", "외관": "", "육질": "", "결함": "", "배제농가": ""},
    {"업체명": "명성", "우선순위": 3, "목표두수": 4, "지급률": "107.0%", "중량(kg)": "87~97", "등지방(mm)": "20~22", "등급": "1,1+", "암 비율": "80%", "외관": "", "육질": "", "결함": "", "배제농가": ""},
    {"업체명": "염주골", "우선순위": 5, "목표두수": 20, "지급률": "105.0%", "중량(kg)": "98~109", "등지방(mm)": "20~27", "등급": "2", "암 비율": "50%", "외관": "", "육질": "", "결함": "", "배제농가": ""},
    {"업체명": "흥부축산", "우선순위": 5, "목표두수": 25, "지급률": "103.5%", "중량(kg)": "75~86", "등지방(mm)": "18~22", "등급": "1,1+,2", "암 비율": "60%", "외관": "", "육질": "", "결함": "", "배제농가": ""},
    {"업체명": "미소", "우선순위": 4, "목표두수": 60, "지급률": "105.0%", "중량(kg)": "80~97", "등지방(mm)": "17~25", "등급": "1,1+", "암 비율": "60%", "외관": "", "육질": "", "결함": "", "배제농가": ""},
    {"업체명": "프라임미트", "우선순위": 4, "목표두수": 110, "지급률": "104.5%", "중량(kg)": "80~103", "등지방(mm)": "20~34", "등급": "1,1+,2", "암 비율": "70%", "외관": "", "육질": "", "결함": "", "배제농가": ""}
]

if 'spec_df' not in st.session_state:
    st.session_state.spec_df = pd.DataFrame(default_specs)

def get_centered_column_config(df):
    config = {}
    for col in df.columns:
        if col == "우선순위":
            config[col] = st.column_config.Column(col, alignment="center", width="small")
        else:
            config[col] = st.column_config.Column(col, alignment="center")
    return config

# ----------------- 파일 업로드 및 자동 배정 연산 (메뉴 이동 간 데이터 유지) -----------------
if uploaded_grade:
    try:
        raw_df = pd.read_excel(uploaded_grade, header=None)
        header_row_idx = 3
        for r_idx in range(min(10, len(raw_df))):
            row_vals = [str(v) for v in raw_df.iloc[r_idx].values]
            if any('도체' in v for v in row_vals) and any('중량' in v or '도체중' in v for v in row_vals):
                header_row_idx = r_idx
                break

        df_g = pd.read_excel(uploaded_grade, header=header_row_idx)

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

        specs = []
        specs_dict = {}
        for idx, row in st.session_state.spec_df.iterrows():
            name = str(row['업체명']).strip()
            prio = int(row['우선순위']) if pd.notna(row['우선순위']) else 99
            target_cnt = int(row['목표두수']) if pd.notna(row['목표두수']) else 0
            
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
                '업체명': name, '우선순위': prio, '목표두수': target_cnt,
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

        for spec in specs:
            company = spec['업체명']
            target = spec['목표두수']
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

        unassigned_mask = pigs['배정거래처'] == '미배정'
        pigs.loc[unassigned_mask, '배정거래처'] = '잇다'

        # 세션에 최종 저장 (메뉴 이동해도 안 날아감)
        st.session_state['allocated_pigs'] = pigs
        st.session_state['specs_dict'] = specs_dict

    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")

# ==============================================================================
# [메뉴 1] 거래처 자동 배정 시스템
# ==============================================================================
if st.session_state.main_menu == "배정":
    st.title("🐖 주식회사 잇다 / 거래처 자동 배정 시스템")

    tab1, tab2, tab3, tab4 = st.tabs([
        "⚙️ 거래처 스펙 관리", 
        "🚀 자동 배정 실행", 
        "🏢 거래처별 배정 상세",
        "🚚 잇다 배정"
    ])

    # ----------------- 탭 1: 거래처 스펙 관리 -----------------
    with tab1:
        st.subheader("⚙️ 거래처 스펙 관리")

        edited_df = st.data_editor(
            st.session_state.spec_df,
            num_rows="dynamic",
            use_container_width=True,
            height=600,
            key="spec_editor",
            column_config=get_centered_column_config(st.session_state.spec_df)
        )

        st.session_state.spec_df = edited_df

    # ----------------- 탭 2: 자동 배정 실행 -----------------
    with tab2:
        if 'allocated_pigs' in st.session_state:
            pigs = st.session_state['allocated_pigs']

            total_pigs = len(pigs)
            assigned_pigs = len(pigs[pigs['배정거래처'] != '잇다'])
            jn_pigs = len(pigs[pigs['배정거래처'] == '잇다'])

            c1, c2, c3 = st.columns(3)
            c1.metric("총 도축 수량", f"{total_pigs} 두")
            c2.metric("일반 거래처 배정 수량", f"{assigned_pigs} 두")
            c3.metric("잇다 잔여 할당 수량", f"{jn_pigs} 두")

            st.markdown("---")
            
            col_main, _ = st.columns([4, 1])
            with col_main:
                st.subheader("📋 전체 개체별 세부 배정 내역")
                
                today_tab_name = datetime.now().strftime("%Y-%m-%d")
                
                summary = pigs.groupby(['배정거래처', '성별']).size().unstack(fill_value=0)
                if '거세' not in summary.columns: summary['거세'] = 0
                if '암' not in summary.columns: summary['암'] = 0
                summary['합계'] = summary['거세'] + summary['암']
                summary = summary[['합계', '거세', '암']]

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    pigs.to_excel(writer, sheet_name='전체배정내역')
                    summary.to_excel(writer, sheet_name='요약')
                processed_data = output.getvalue()
                
                st.download_button(
                    label="📥 전체 배정 결과 엑셀 다운로드",
                    data=processed_data,
                    file_name=f"돼지배정결과_{today_tab_name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                display_df = pigs[['도체번호', '성별', '중량', '등지방', '등급', '배정거래처', '이력번호', '출하농가']].copy()
                st.dataframe(
                    display_df, 
                    height=1500, 
                    use_container_width=True,
                    column_config=get_centered_column_config(display_df)
                )
        else:
            st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 업로드해 주세요.")

    # ----------------- 탭 3: 거래처별 배정 상세 -----------------
    with tab3:
        st.subheader("🏢 거래처별 개별 배정 내역 및 명단")
        
        if 'allocated_pigs' in st.session_state and 'specs_dict' in st.session_state:
            pigs_all = st.session_state['allocated_pigs']
            specs_dict = st.session_state['specs_dict']
            
            company_list = sorted([c for c in pigs_all['배정거래처'].unique() if c != '잇다'])
            
            if company_list:
                if 'selected_company' not in st.session_state or st.session_state.selected_company not in company_list:
                    st.session_state.selected_company = company_list[0]

                st.write("👉 **조회할 거래처를 클릭하세요 (가나다순 정렬):**")
                
                cols = st.columns(min(len(company_list), 6))
                for idx, comp in enumerate(company_list):
                    col_idx = idx % 6
                    is_selected = (comp == st.session_state.selected_company)
                    label = f"📌 {comp}" if is_selected else comp
                    btn_type = "primary" if is_selected else "secondary"
                    
                    if cols[col_idx].button(label, key=f"btn_comp_{comp}", type=btn_type, use_container_width=True):
                        st.session_state.selected_company = comp
                        st.rerun()

                st.markdown("---")
                
                col_comp_main, _ = st.columns([4, 1])
                with col_comp_main:
                    selected_company = st.session_state.selected_company
                    st.markdown(f"### **[{selected_company}] 배정 명단**")

                    spec = specs_dict.get(selected_company, None)
                    if spec:
                        ex_farm_info = f" | 배제농가: {', '.join(spec['배제농가'])}" if spec['배제농가'] else ""
                        st.markdown(
                            f"""
                            <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 10px 15px; font-size: 14px; color: #495057; margin-bottom: 15px;">
                                <strong>목표두수:</strong> {spec['목표두수']}두 | <strong>중량:</strong> {spec['weight_str']} kg | <strong>등지방:</strong> {spec['fat_str']} mm | <strong>등급:</strong> {spec['grade_str']} | <strong>암 비율:</strong> {spec['f_ratio_str']}{ex_farm_info}
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )

                    comp_df = pigs_all[pigs_all['배정거래처'] == selected_company].copy()
                    comp_df.reset_index(drop=True, inplace=True)
                    comp_df.index = comp_df.index + 1

                    comp_df['도체번호'] = comp_df['도체번호'].astype(int)
                    comp_df['중량'] = comp_df['중량'].round(1)
                    comp_df['등지방'] = comp_df['등지방'].round(1)

                    remarks = []
                    for idx, row in comp_df.iterrows():
                        if not spec:
                            remarks.append("-")
                            continue
                        
                        diffs = []
                        if row['중량'] < spec['w_min']:
                            diffs.append(f"중량미달({row['중량']}kg < {spec['w_min']}kg)")
                        elif row['중량'] > spec['w_max']:
                            diffs.append(f"중량초과({row['중량']}kg > {spec['w_max']}kg)")
                        
                        if row['등지방'] < spec['f_min']:
                            diffs.append(f"등지방미달({row['등지방']}mm < {spec['f_min']}mm)")
                        elif row['등지방'] > spec['f_max']:
                            diffs.append(f"등지방초과({row['등지방']}mm > {spec['f_max']}mm)")
                        
                        if spec['grades'] and str(row['등급']).strip() not in spec['grades']:
                            diffs.append(f"등급불일치({row['등급']})")
                        
                        if spec['배제농가'] and any(farm in str(row['출하농가']) for farm in spec['배제농가']):
                            diffs.append(f"배제농가포함({row['출하농가']})")

                        remarks.append(", ".join(diffs) if diffs else "스펙일치")

                    comp_df['비고'] = remarks
                    
                    c_cnt = len(comp_df[comp_df['성별'] == '거세'])
                    f_cnt = len(comp_df[comp_df['성별'] == '암'])
                    avg_w = comp_df['중량'].mean() if not comp_df.empty else 0
                    avg_f = comp_df['등지방'].mean() if not comp_df.empty else 0
                    
                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("총 배정 수량", f"{len(comp_df)} 두")
                    m2.metric("거세 수량", f"{c_cnt} 두")
                    m3.metric("암 수량", f"{f_cnt} 두")
                    m4.metric("평균 중량", f"{avg_w:.1f} kg")
                    m5.metric("평균 등지방", f"{avg_f:.1f} mm")
                    
                    st.markdown(" ")
                    
                    output_comp = io.BytesIO()
                    with pd.ExcelWriter(output_comp, engine='openpyxl') as writer:
                        comp_df.to_excel(writer, sheet_name=selected_company)
                    comp_data = output_comp.getvalue()
                    
                    st.download_button(
                        label=f"📥 [{selected_company}] 배정 명단 엑셀 다운로드",
                        data=comp_data,
                        file_name=f"{selected_company}_배정명단.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    comp_display = comp_df[['도체번호', '성별', '중량', '등지방', '등급', '비고', '이력번호', '출하농가']].copy()
                    st.dataframe(
                        comp_display, 
                        height=1500, 
                        use_container_width=True,
                        column_config=get_centered_column_config(comp_display)
                    )
            else:
                st.info("배정된 일반 거래처 내역이 없습니다.")
        else:
            st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 업로드해 주세요.")

    # ----------------- 탭 4: 잇다 배정 -----------------
    with tab4:
        st.subheader("🚚 잇다 배정")
        
        if 'allocated_pigs' in st.session_state:
            pigs_all = st.session_state['allocated_pigs']
            jn_df = pigs_all[pigs_all['배정거래처'] == '잇다'].copy()
            
            if not jn_df.empty:
                jn_df.reset_index(drop=True, inplace=True)
                jn_df.index = jn_df.index + 1
                
                total_jn_count = len(jn_df)
                total_jn_weight = jn_df['중량'].sum()

                st.markdown(
                    f"""
                    <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 12px 18px; font-size: 15px; color: #333333; margin-bottom: 15px;">
                        <strong>전남지사 배정수량 :</strong> {total_jn_count}두 / <strong>총중량 :</strong> {total_jn_weight:,.1f} kg
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                jn_export = pd.DataFrame({
                    'No.': jn_df.index,
                    '작업장명': '나주농협',
                    '판정일': datetime.now().day,
                    '도체번호': jn_df['도체번호'],
                    '판정방법': '온',
                    '도체형태': '탕박',
                    '성별': jn_df['성별'],
                    '도체중(kg)': jn_df['중량'],
                    '등지방두께': jn_df['등지방'],
                    '최종등급': jn_df['등급'],
                    '출하농가': jn_df['출하농가'],
                    '이력번호': jn_df['이력번호'],
                    '거래처': '잇다'
                })

                output_jn = io.BytesIO()
                with pd.ExcelWriter(output_jn, engine='openpyxl') as writer:
                    jn_export.to_excel(writer, sheet_name='잇다', index=False)
                jn_data = output_jn.getvalue()

                today_str = datetime.now().strftime("%m%d")
                st.download_button(
                    label=f"📥 잇다 전달용 엑셀 다운로드 ({today_str} 잇다.xlsx)",
                    data=jn_data,
                    file_name=f"{today_str} 잇다.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                st.markdown("---")
                col_jn_main, _ = st.columns([4, 1])
                with col_jn_main:
                    st.dataframe(
                        jn_export, 
                        height=1200, 
                        use_container_width=True,
                        column_config=get_centered_column_config(jn_export)
                    )

            else:
                st.warning("잇다 채널로 할당된 물량이 없습니다.")
        else:
            st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 업로드해 주세요.")

# ==============================================================================
# [메뉴 2] 농가 분석 (추가 메뉴)
# ==============================================================================
elif st.session_state.main_menu == "농가분석":
    st.title("📊 농가별 출하 및 스펙 분석")
    
    if 'allocated_pigs' in st.session_state:
        pigs_all = st.session_state['allocated_pigs']
        st.success(f"✅ 현재 총 **{len(pigs_all)}두**의 출하 농가 데이터가 유지되고 있습니다.")
        
        # 사료사 / 농가별 출하 통계 요약 표
        farm_summary = pigs_all.groupby('출하농가').agg(
            출하두수=('도체번호', 'count'),
            평균중량=('중량', 'mean'),
            평균등지방=('등지방', 'mean')
        ).reset_index()

        farm_summary['평균중량'] = farm_summary['평균중량'].round(1)
        farm_summary['평균등지방'] = farm_summary['평균등지방'].round(1)

        st.subheader("📋 출하 농가(사료사)별 통계 요약")
        st.dataframe(
            farm_summary, 
            use_container_width=True, 
            height=600,
            column_config=get_centered_column_config(farm_summary)
        )
    else:
        st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 먼저 업로드하시면 농가 분석이 시작됩니다.")
