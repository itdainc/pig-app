import io
import pandas as pd
import streamlit as st
from datetime import datetime

# ----------------- 외부 모듈 및 안전 로드 -----------------
try:
    from auth import check_password
except ImportError:
    def check_password(): return True

try:
    from farm_data import get_farm_with_feed
except ImportError:
    def get_farm_with_feed(farm_name):
        return str(farm_name).strip() if pd.notna(farm_name) else ''

try:
    from company_conditions import (
        get_company_conditions_df,
        get_company_conditions_excel_bytes,
        run_100pct_strict_allocation,
    )
except ImportError:
    def get_company_conditions_df(): return pd.DataFrame()
    def get_company_conditions_excel_bytes(): return b''
    def run_100pct_strict_allocation(df, custom_conditions_df=None): 
        df['배정거래처'] = '미분류'
        return df, pd.DataFrame(), pd.DataFrame()

# ----------------- 개체별 지육율 및 생체중 추정 함수 -----------------
def calc_pig_dressing_rate(weight, sex):
    if weight < 78:
        base_rate = 75.2
    elif weight < 82:
        base_rate = 75.8
    elif weight < 86:
        base_rate = 76.4
    elif weight < 90:
        base_rate = 77.0
    elif weight < 95:
        base_rate = 77.5
    else:
        base_rate = 78.0
        
    if str(sex).strip() == '거세':
        base_rate += 0.2
    return base_rate

# ----------------- 엑셀 위치 지정 로더 (7행부터 데이터 시작) -----------------
def load_excel_by_coords(file):
    file.seek(0)
    df = pd.read_excel(file, skiprows=6, header=None)

    # 4번 열: 실제 도체번호 (5201, 5202...)
    if df.shape[1] > 4:
        df['pig_no'] = pd.to_numeric(df.iloc[:, 4], errors='coerce').fillna(df.iloc[:, 1]).astype(int)
    else:
        df['pig_no'] = pd.to_numeric(df.iloc[:, 1], errors='coerce').fillna(0).astype(int)

    df['w_num'] = pd.to_numeric(df.iloc[:, 8], errors='coerce')  # 도체중
    df['f_num'] = pd.to_numeric(df.iloc[:, 9], errors='coerce')  # 등지방
    df['sex_str'] = df.iloc[:, 7].astype(str).str.strip()       # 성별
    df['grade_str'] = df.iloc[:, 22].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)

    # 35번 열 (출하자명 / 농가)
    farm_col_idx = 35 if df.shape[1] > 35 else (21 if df.shape[1] > 21 else 0)
    raw_farm = df.iloc[:, farm_col_idx].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    raw_farm = raw_farm.replace(['nan', 'None', '0', ''], '-')
    df['farm_name'] = raw_farm.apply(get_farm_with_feed)

    # 개체별 지육율 및 생체중 파생변수 생성
    df['pig_dressing_rate'] = df.apply(lambda r: calc_pig_dressing_rate(r['w_num'], r['sex_str']), axis=1)
    df['pig_live_weight'] = df['w_num'] / (df['pig_dressing_rate'] / 100.0)

    def check_no_defect(row_slice):
        for val in row_slice:
            if pd.notna(val):
                s = str(val).strip()
                if s and s.lower() not in ['nan', 'none']:
                    return False
        return True

    df['no_defect'] = df.iloc[:, 11:21].apply(check_no_defect, axis=1)
    df['배정거래처'] = '미분류'
    
    return df

# 로그인 검증
if check_password():

    st.set_page_config(page_title="주식회사 잇다 / 자동 배정 및 농가 분석 시스템", layout="wide", page_icon="🐖")

    if 'main_menu' not in st.session_state:
        st.session_state.main_menu = "배정"

    # ------------------------------------------------------------------------------
    # 💡 조건표 동기화 및 세부 항목 초기화 (KeyError 방지)
    # ------------------------------------------------------------------------------
    df_cond = get_company_conditions_df()
    current_cond_companies = list(df_cond['거래처']) if not df_cond.empty else []

    is_target_valid = (
        'target_df' in st.session_state 
        and isinstance(st.session_state.target_df, pd.DataFrame)
        and '거래처' in st.session_state.target_df.columns
        and list(st.session_state.target_df['거래처']) == current_cond_companies
    )

    if not is_target_valid:
        if not df_cond.empty:
            st.session_state.target_df = df_cond.copy()
        else:
            st.session_state.target_df = pd.DataFrame(columns=['거래처', '목표두수'])

    # 📌 사이드바 메뉴
    st.sidebar.title("📌 메인 메뉴")

    if st.sidebar.button("🏢 1. 거래처 자동 배정 시스템", type="primary" if st.session_state.main_menu == "배정" else "secondary", use_container_width=True):
        st.session_state.main_menu = "배정"
        st.rerun()

    if st.sidebar.button("📊 2. 농가 분석", type="primary" if st.session_state.main_menu == "농가분석" else "secondary", use_container_width=True):
        st.session_state.main_menu = "농가분석"
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.header("📁 파일 업로드")
    uploaded_grade = st.sidebar.file_uploader("1. 등급판정 결과 파일 (.xls/.xlsx)", type=["xls", "xlsx"])

    st.sidebar.markdown("---")

    # 💡 시스템 초기화 (메모리 리프레쉬) 버튼
    if st.sidebar.button("🔄 시스템 초기화", use_container_width=True):
        keys_to_clear = ['target_df', 'allocated_pigs']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.success("✅ 시스템 메모리가 완전히 초기화되었습니다.")
        st.rerun()

    if st.sidebar.button("🔒 로그아웃", use_container_width=True):
        st.session_state["password_correct"] = False
        st.rerun()

    # ==============================================================================
    # [메뉴 1] 거래처 자동 배정 시스템
    # ==============================================================================
    if st.session_state.main_menu == "배정":
        st.title("🐖 주식회사 잇다 / 거래처 자동 배정 시스템")

        tab1, tab2, tab3 = st.tabs(["🚀 자동 배정 실행", "🏢 거래처별 배정 상세", "🚚 잇다 배정 내역 (미분류)"])

        # ----------------- 탭 1: 자동 배정 실행 -----------------
        with tab1:
            st.subheader("🚀 자동 배정 연산 및 분석")
            
            # --- 1. 규격 분석 ---
            st.markdown("### 📊 1. 등급판정 결과 데이터 규격 분석")
            
            if uploaded_grade:
                try:
                    df_raw = load_excel_by_coords(uploaded_grade)
                    df_valid = df_raw.dropna(subset=['w_num', 'f_num'])
                    
                    cond1 = (
                        (df_valid['w_num'] >= 85) & (df_valid['w_num'] <= 97) & 
                        (df_valid['f_num'] >= 18) & (df_valid['f_num'] <= 27) & 
                        (df_valid['grade_str'].isin(['1', '1+'])) &
                        (df_valid['no_defect'])
                    )
                    df_cond1 = df_valid[cond1]
                    df_rem1 = df_valid[~cond1]
                    
                    cond2 = (df_rem1['w_num'] >= 97) | (df_rem1['f_num'] >= 27)
                    df_cond2 = df_rem1[cond2]
                    df_rem2 = df_rem1[~cond2]
                    
                    cond3 = (df_rem2['w_num'] < 85) | (df_rem2['f_num'] < 18)
                    df_cond3 = df_rem2[cond3]
                    df_cond4 = df_rem2[~cond3]
                    
                    tot_cnt = len(df_valid)
                    c1_cnt = len(df_cond1)
                    c2_cnt = len(df_cond2)
                    c3_cnt = len(df_cond3)
                    c4_cnt = len(df_cond4)
                    
                    analysis_table = pd.DataFrame({
                        "구분": ["1. 마장동 스펙 규격", "2. 두꺼운 지육 (마장동 제외)", "3. 얇은/소형 지육 (잔여 물량)", "4. 그외"],
                        "분류 상세 조건": [
                            r"중량 85 \~ 97kg, 등지방 18 \~ 27mm, 등급 1 / 1+, 하자없음",
                            r"중량 97kg 이상 이거나 등지방 27mm 이상",
                            r"중량 85kg 미만 이거나 등지방 18mm 미만",
                            r"1 \~ 3번 조건 미포함"
                        ],
                        "배정가능 두수": [f"{c1_cnt:,} 두", f"{c2_cnt:,} 두", f"{c3_cnt:,} 두", f"{c4_cnt:,} 두"],
                        "비율 (%)": [
                            f"{(c1_cnt/tot_cnt*100):.1f}%" if tot_cnt > 0 else "0%",
                            f"{(c2_cnt/tot_cnt*100):.1f}%" if tot_cnt > 0 else "0%",
                            f"{(c3_cnt/tot_cnt*100):.1f}%" if tot_cnt > 0 else "0%",
                            f"{(c4_cnt/tot_cnt*100):.1f}%" if tot_cnt > 0 else "0%"
                        ]
                    })
                    
                    st.table(analysis_table)
                    st.info(f"💡 **총 입고두수:** {tot_cnt:,}두 (마장동 스펙 지육: {c1_cnt:,}두 / 두꺼운 지육: {c2_cnt:,}두 / 얇은·소형: {c3_cnt:,}두 / 그외: {c4_cnt:,}두)")
                except Exception as e:
                    st.error(f"등급판정 파일 분석 중 오류 발생: {e}")
            else:
                st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 업로드하시면 규격별 수량 분석표가 표시됩니다.")

            st.markdown("---")

            # --- 2. 목표두수 및 세부 조건 수정 ---
            st.markdown("### ✏️ 2. 거래처별 세부 배정 조건 수정 및 변경")
            st.info("💡 거래처별 **목표두수, 중량, 등지방, 등급, 하자, 배제농가** 항목을 직접 수정하고 하단 버튼을 누르면 배정 연산에 즉시 반영됩니다.")
            
            # 동적 높이 계산 (공란 없이 행 수에 맞춤)
            calc_target_editor_height = (len(st.session_state.target_df) + 1) * 35 + 5
            
            edited_target_df = st.data_editor(
                st.session_state.target_df,
                height=calc_target_editor_height,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "배정순서": st.column_config.Column("배정순서", disabled=True),
                    "거래처": st.column_config.Column("거래처명", disabled=True),
                    "중요도": st.column_config.Column("중요도", disabled=True),
                    "암 비율": st.column_config.Column("암 비율", disabled=True),
                    "지급률": st.column_config.Column("지급률", disabled=True),
                    "목표두수": st.column_config.NumberColumn("목표두수", min_value=0, step=1),
                    "최소 중량": st.column_config.NumberColumn("최소 중량"),
                    "최대 중량": st.column_config.NumberColumn("최대 중량"),
                    "최소 등지방": st.column_config.NumberColumn("최소 등지방"),
                    "최대 등지방": st.column_config.NumberColumn("최대 등지방"),
                    "등급": st.column_config.TextColumn("등급"),
                    "하자": st.column_config.TextColumn("하자"),
                    "배제농가": st.column_config.TextColumn("배제농가 (쉼표 분리 가능)"),
                }
            )

            if st.button("💾 변경사항 적용 및 재연산", type="primary", use_container_width=True):
                st.session_state.target_df = edited_target_df
                st.success("✅ 거래처별 세부 배정 조건이 업데이트되었습니다. 아래 3번 항목에 즉시 적용되었습니다.")
                st.rerun()

            st.markdown("---")

            # --- 3. 1차 배정 ---
            st.markdown("### 🤖 3. 1차 배정 (스펙일치)")
            
            if uploaded_grade:
                try:
                    pigs, unallocated_df, summary_df = run_100pct_strict_allocation(df_valid, st.session_state.target_df)
                    st.session_state['allocated_pigs'] = pigs

                    c1, c2, c3 = st.columns(3)
                    c1.metric("총 도축 수량", f"{len(pigs)} 두")
                    c2.metric("1차 배정 완료 수량", f"{len(pigs[pigs['배정거래처'] != '미분류'])} 두")
                    c3.metric("미분류 (잔여 물량)", f"{len(unallocated_df)} 두")
                    
                    st.markdown("#### 📊 업체별 1차 배정 달성 요약")
                    if not summary_df.empty:
                        comp_summary = summary_df[summary_df['거래처명'] != '미분류 (잔여 물량)'].copy()
                        
                        comp_summary['목표두수'] = pd.to_numeric(comp_summary['목표두수'], errors='coerce').fillna(0).astype(int)
                        comp_summary['1차 배정두수'] = pd.to_numeric(comp_summary['1차 배정두수'], errors='coerce').fillna(0).astype(int)
                        comp_summary['부족두수'] = comp_summary['목표두수'] - comp_summary['1차 배정두수']
                        
                        display_summary = comp_summary[['거래처명', '목표두수', '1차 배정두수', '부족두수']]
                        
                        def highlight_shortage(row):
                            if row['부족두수'] > 0:
                                return ['background-color: rgba(255, 75, 75, 0.2); color: #ff4b4b; font-weight: bold;'] * len(row)
                            return [''] * len(row)

                        styled_summary = display_summary.style.apply(highlight_shortage, axis=1)
                        # 공란 없이 달성요약표 높이 정확히 계산
                        calc_summary_height = (len(display_summary) + 1) * 35 + 5
                        
                        st.dataframe(styled_summary, height=calc_summary_height, use_container_width=True, hide_index=True)

                    # ---------------- 아코디언 메뉴 ----------------
                    with st.expander("📋 1차 배정 내역보기(스팩 100% 일치)", expanded=False):
                        today_str = datetime.now().strftime("%Y-%m-%d")
                        summary = pigs.groupby(['배정거래처']).size().reset_index(name='수량')

                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            pigs.to_excel(writer, sheet_name='전체배정내역')
                            summary.to_excel(writer, sheet_name='요약')
                        processed_data = output.getvalue()
                        
                        # 도체번호(pig_no), 중량, 등지방, 등급 표출 및 인덱스 1부터 부여
                        display_df = pigs[['pig_no', 'w_num', 'f_num', 'grade_str', '배정거래처']].copy()
                        display_df.columns = ['도체번호', '중량', '등지방', '등급', '배정거래처']
                        display_df.index = range(1, len(display_df) + 1)  # 순번 1부터 시작!
                        
                        calc_height = min(800, (len(display_df) + 1) * 35 + 5)
                        st.dataframe(display_df, height=calc_height, use_container_width=True)

                        st.download_button(
                            label="📥 전체 배정 결과 엑셀 다운로드",
                            data=processed_data,
                            file_name=f"{today_str}_배정결과.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                    if not unallocated_df.empty:
                        with st.expander("⚠️ 1차 배정 미분류 (잔여 물량) 내역 보기", expanded=False):
                            today_str = datetime.now().strftime("%Y-%m-%d")
                            output_unalloc = io.BytesIO()
                            with pd.ExcelWriter(output_unalloc, engine='openpyxl') as writer:
                                unallocated_df.to_excel(writer, sheet_name='1차_미분류내역', index=False)
                            
                            display_unalloc_df = unallocated_df[['pig_no', 'w_num', 'f_num', 'grade_str', '배정거래처']].copy()
                            display_unalloc_df.columns = ['도체번호', '중량', '등지방', '등급', '배정거래처']
                            display_unalloc_df.index = range(1, len(display_unalloc_df) + 1)  # 순번 1부터 시작!
                            
                            calc_unalloc_height = min(800, (len(display_unalloc_df) + 1) * 35 + 5)
                            st.dataframe(display_unalloc_df, height=calc_unalloc_height, use_container_width=True)

                            st.download_button(
                                label="📥 1차 배정 미분류 엑셀 다운로드",
                                data=output_unalloc.getvalue(),
                                file_name=f"{today_str}_1차배정_미분류내역.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )

                    with st.expander("📋 업체별 세부 배정 조건표 조회 및 엑셀 다운로드", expanded=False):
                        cond_df = get_company_conditions_df()
                        if not cond_df.empty:
                            st.dataframe(cond_df, use_container_width=True, hide_index=True)
                            st.download_button(
                                label="📥 거래처별 배정 조건표 엑셀 다운로드",
                                data=get_company_conditions_excel_bytes(),
                                file_name="거래처별_배정조건표.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )

                except Exception as e:
                    st.error(f"1차 배정 처리 중 오류가 발생했습니다: {e}")
            else:
                st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 업로드하시면 1차 배정 결과가 자동 연산됩니다.")

        # ----------------- 탭 2: 거래처별 배정 상세 -----------------
        with tab2:
            st.subheader("🏢 거래처별 개별 배정 내역 및 명단")
            if 'allocated_pigs' in st.session_state and '배정거래처' in st.session_state['allocated_pigs'].columns:
                pigs_all = st.session_state['allocated_pigs']
                all_assigned = [c for c in pigs_all['배정거래처'].unique() if "미분류" not in c]
                
                if all_assigned:
                    selected_company = st.selectbox("👉 조회할 거래처를 선택하세요:", sorted(all_assigned))
                    st.markdown(f"### **[{selected_company}] 배정 명단**")
                    comp_df = pigs_all[pigs_all['배정거래처'] == selected_company].copy()
                    
                    display_comp_df = comp_df[['pig_no', 'w_num', 'f_num', 'grade_str', '배정거래처']].copy()
                    display_comp_df.columns = ['도체번호', '중량', '등지방', '등급', '배정거래처']
                    display_comp_df.index = range(1, len(display_comp_df) + 1)  # 순번 1부터 시작!
                    
                    calc_comp_height = min(800, (len(display_comp_df) + 1) * 35 + 5)
                    st.dataframe(display_comp_df, height=calc_comp_height, use_container_width=True)
            else:
                st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 업로드해 주세요.")

        # ----------------- 탭 3: 잇다 배정 (미분류) -----------------
        with tab3:
            st.subheader("🚚 잇다 배정 내역 (미분류)")
            if 'allocated_pigs' in st.session_state and '배정거래처' in st.session_state['allocated_pigs'].columns:
                pigs_all = st.session_state['allocated_pigs']
                unassigned_df_tab3 = pigs_all[pigs_all['배정거래처'] == '미분류'].copy()
                
                if not unassigned_df_tab3.empty:
                    display_tab3_df = unassigned_df_tab3[['pig_no', 'w_num', 'f_num', 'grade_str', '배정거래처']].copy()
                    display_tab3_df.columns = ['도체번호', '중량', '등지방', '등급', '배정거래처']
                    display_tab3_df.index = range(1, len(display_tab3_df) + 1)  # 순번 1부터 시작!
                    
                    calc_tab3_height = min(800, (len(display_tab3_df) + 1) * 35 + 5)
                    st.dataframe(display_tab3_df, height=calc_tab3_height, use_container_width=True)
            else:
                st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 업로드해 주세요.")

    # ==============================================================================
    # [메뉴 2] 농가 분석
    # ==============================================================================
    elif st.session_state.main_menu == "농가분석":
        st.title("📊 농가별 출하 및 스펙 분석")
        
        if 'allocated_pigs' in st.session_state:
            pigs_all = st.session_state['allocated_pigs'].copy()
            
            def extract_feed_and_farm(val):
                s_val = str(val).strip()
                if '/' in s_val:
                    parts = s_val.split('/')
                    return parts[1].strip(), parts[0].strip()
                return s_val, '-'

            # 농가명 정밀 파싱
            if 'farm_name' in pigs_all.columns:
                pigs_all[['농가_명', '사료사_명']] = pigs_all['farm_name'].apply(lambda x: pd.Series(extract_feed_and_farm(x)))
            else:
                pigs_all['농가_명'] = '-'
                pigs_all['사료사_명'] = '-'

            farm_groups = pigs_all.groupby(['농가_명', '사료사_명'])
            
            rows = []
            for (farm_name, feed_name), group in farm_groups:
                head_cnt = len(group)
                total_weight = group['w_num'].sum()
                
                # 개체별 연산 기반 생체중 합산
                if 'pig_live_weight' in group.columns:
                    live_weight = group['pig_live_weight'].sum()
                else:
                    live_weight = total_weight / (76.32 / 100.0)
                    
                real_dressing_rate = (total_weight / live_weight * 100) if live_weight > 0 else 0.0

                spec_target = group[(group['w_num'] >= 86) & (group['w_num'] <= 96) & (group['f_num'] >= 19) & (group['f_num'] <= 23)]
                spec_target_cnt = len(spec_target)

                cnt_1plus = len(group[group['grade_str'] == '1+'])
                cnt_1 = len(group[group['grade_str'] == '1'])
                cnt_2 = len(group[group['grade_str'] == '2'])

                rows.append({
                    '농가': farm_name, '사료사': feed_name, '두수': f"{head_cnt:,}", '중량': f"{int(round(total_weight)):,}",
                    '생체': f"{int(round(live_weight)):,}", '생체평균': f"{(live_weight / head_cnt):.2f}" if head_cnt > 0 else "0.00",
                    '도체 kg': f"{(total_weight / head_cnt):.1f}" if head_cnt > 0 else "0.0", '등지방 mm': f"{group['f_num'].mean():.1f}",
                    '지육율': f"{real_dressing_rate:.2f}%", '86~96,19~23': f"{spec_target_cnt:,}", '스펙비율': f"{(spec_target_cnt / head_cnt * 100):.1f}%" if head_cnt > 0 else "0.0%",
                    '1+': f"{cnt_1plus:,}", '1+ 중량': f"{int(round(group[group['grade_str'] == '1+']['w_num'].sum())):,}",
                    '1': f"{cnt_1:,}", '1 중량': f"{int(round(group[group['grade_str'] == '1']['w_num'].sum())):,}",
                    '2': f"{cnt_2:,}", '2 중량': f"{int(round(group[group['grade_str'] == '2']['w_num'].sum())):,}",
                    '1+,1 비율': f"{((cnt_1plus + cnt_1) / head_cnt * 100):.2f}%" if head_cnt > 0 else "0.00%"
                })

            analysis_df = pd.DataFrame(rows)
            total_head = len(pigs_all)
            total_w = pigs_all['w_num'].sum()
            
            if 'pig_live_weight' in pigs_all.columns:
                total_live = pigs_all['pig_live_weight'].sum()
            else:
                total_live = total_w / (76.32 / 100.0)

            sum_row = pd.DataFrame([{
                '농가': '합계', '사료사': '-', '두수': f"{total_head:,}", '중량': f"{int(round(total_w)):,}",
                '생체': f"{int(round(total_live)):,}", '생체평균': f"{(total_live / total_head):.2f}" if total_head > 0 else "0.00",
                '도체 kg': f"{(total_w / total_head):.1f}" if total_head > 0 else "0.0", '등지방 mm': f"{pigs_all['f_num'].mean():.1f}",
                '지육율': f"{(total_w / total_live * 100):.2f}%" if total_live > 0 else "0.00%",
                '86~96,19~23': f"{len(pigs_all[(pigs_all['w_num'] >= 86) & (pigs_all['w_num'] <= 96) & (pigs_all['f_num'] >= 19) & (pigs_all['f_num'] <= 23)]):,}",
                '스펙비율': f"{(len(pigs_all[(pigs_all['w_num'] >= 86) & (pigs_all['w_num'] <= 96) & (pigs_all['f_num'] >= 19) & (pigs_all['f_num'] <= 23)]) / total_head * 100):.1f}%" if total_head > 0 else "0.0%",
                '1+': f"{len(pigs_all[pigs_all['grade_str'] == '1+']):,}", '1+ 중량': f"{int(round(pigs_all[pigs_all['grade_str'] == '1+']['w_num'].sum())):,}",
                '1': f"{len(pigs_all[pigs_all['grade_str'] == '1']):,}", '1 중량': f"{int(round(pigs_all[pigs_all['grade_str'] == '1']['w_num'].sum())):,}",
                '2': f"{len(pigs_all[pigs_all['grade_str'] == '2']):,}", '2 중량': f"{int(round(pigs_all[pigs_all['grade_str'] == '2']['w_num'].sum())):,}",
                '1+,1 비율': f"{((len(pigs_all[pigs_all['grade_str'] == '1+']) + len(pigs_all[pigs_all['grade_str'] == '1'])) / total_head * 100):.2f}%" if total_head > 0 else "0.00%"
            }])

            final_analysis_df = pd.concat([analysis_df, sum_row], ignore_index=True)
            st.subheader("📋 출하 농가별 세부 성적 및 등급 분석")
            
            output_anal = io.BytesIO()
            with pd.ExcelWriter(output_anal, engine='openpyxl') as writer: final_analysis_df.to_excel(writer, sheet_name='농가분석', index=False)
            
            st.download_button(label="📥 농가분석 결과 엑셀 다운로드", data=output_anal.getvalue(), file_name=f"농가분석_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            styled_df = final_analysis_df.style.apply(lambda row: ['font-weight: bold; background-color: #f1f3f5;'] * len(row) if row['농가'] == '합계' else [''] * len(row), axis=1)
            
            calc_height = min(800, (len(final_analysis_df) + 1) * 35 + 5)
            st.dataframe(styled_df, height=calc_height, use_container_width=True, hide_index=True)
        else:
            st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 업로드하시면 농가 분석 결과가 즉시 생성됩니다.")
