import streamlit as st
import pandas as pd
import io
from datetime import datetime

# ----------------- 엑셀 위치 지정 로더 (7행부터 데이터 시작, I열=8, J열=9, W열=22) -----------------
def load_excel_by_coords(file):
    file.seek(0)
    # 상단 6개 행을 건너뛰고 7번째 행(인덱스 6)부터 데이터만 판독
    df = pd.read_excel(file, skiprows=6, header=None)
    
    # I열(8): 중량, J열(9): 등지방, W열(22): 최종등급 수치 및 문자 변환
    df['w_num'] = pd.to_numeric(df.iloc[:, 8], errors='coerce')
    df['f_num'] = pd.to_numeric(df.iloc[:, 9], errors='coerce')
    # W열(22) 등급 텍스트 정제 (1.0 형태로 판독되는 경우 대비)
    df['grade_str'] = df.iloc[:, 22].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    
    w_col_name = "I열(중량)"
    f_col_name = "J열(등지방)"
    
    return df, w_col_name, f_col_name

# ----------------- 외부 연동 모듈 불러오기 -----------------
try:
    from auth import check_password
except ImportError:
    def check_password(): return True

try:
    from auto_allocator import DEFAULT_TARGET_COUNTS, allocate_pigs_data
except ImportError:
    DEFAULT_TARGET_COUNTS = []
    def allocate_pigs_data(file, specs): return pd.DataFrame(), {}

# 로그인 검증
if check_password():

    st.set_page_config(page_title="주식회사 잇다 / 자동 배정 및 농가 분석 시스템", layout="wide", page_icon="🐖")

    if 'main_menu' not in st.session_state:
        st.session_state.main_menu = "배정"

    if 'target_df' not in st.session_state:
        st.session_state.target_df = pd.DataFrame(DEFAULT_TARGET_COUNTS)

    # 📌 메인 메뉴 (2개 고정)
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

    if st.sidebar.button("🔒 로그아웃", use_container_width=True):
        st.session_state["password_correct"] = False
        st.rerun()

    def get_centered_column_config(df):
        config = {}
        for col in df.columns:
            if col in ["우선순위", "목표두수"]:
                config[col] = st.column_config.Column(col, alignment="center", width="small")
            elif col == "비고":
                config[col] = st.column_config.Column(col, alignment="center", width="large")
            elif col in ["출하농가", "이력번호"]:
                config[col] = st.column_config.Column(col, alignment="center", width="medium")
            else:
                config[col] = st.column_config.Column(col, alignment="center")
        return config

    # ==============================================================================
    # [메뉴 1] 거래처 자동 배정 시스템
    # ==============================================================================
    if st.session_state.main_menu == "배정":
        st.title("🐖 주식회사 잇다 / 거래처 자동 배정 시스템")

        # 3개 탭 구성
        tab1, tab2, tab3 = st.tabs([
            "🚀 자동 배정 실행", 
            "🏢 거래처별 배정 상세", 
            "🚚 잇다 배정"
        ])

        # ----------------- 탭 1: 자동 배정 실행 -----------------
        with tab1:
            st.subheader("🚀 자동 배정 연산 및 분석")
            
            # -------------------------------------------------------------------------
            # 1. 등급판정 결과 분석 표 (I, J, W열 기준 분석)
            # -------------------------------------------------------------------------
            st.markdown("### 📊 1. 등급판정 결과 데이터 규격 분석")
            
            if uploaded_grade:
                try:
                    df_raw, w_col_name, f_col_name = load_excel_by_coords(uploaded_grade)
                    
                    # 결측치 제외 유효 데이터 추출
                    df_valid = df_raw.dropna(subset=['w_num', 'f_num'])
                    
                    # 조건 1: 마장동 스펙 (중량 85~97kg AND 등지방 18~27mm AND 등급 1 or 1+등급)
                    cond1 = (
                        (df_valid['w_num'] >= 85) & (df_valid['w_num'] <= 97) & 
                        (df_valid['f_num'] >= 18) & (df_valid['f_num'] <= 27) & 
                        (df_valid['grade_str'].isin(['1', '1+']))
                    )
                    df_cond1 = df_valid[cond1]
                    
                    # 조건 1 제외 물량
                    df_rem1 = df_valid[~cond1]
                    
                    # 조건 2: 두꺼운 지육 (조건 1 제외 중 중량 >= 97kg OR 등지방 >= 27mm)
                    cond2 = (df_rem1['w_num'] >= 97) | (df_rem1['f_num'] >= 27)
                    df_cond2 = df_rem1[cond2]
                    
                    # 조건 3: 얇은/소형 지육 (조건 1, 2 제외 잔여: 중량 < 85kg OR 등지방 < 18mm)
                    df_cond3 = df_rem1[~cond2]
                    
                    tot_cnt = len(df_valid)
                    c1_cnt = len(df_cond1)
                    c2_cnt = len(df_cond2)
                    c3_cnt = len(df_cond3)
                    
                    analysis_table = pd.DataFrame({
                        "구분": ["1. 마장동 스펙 규격", "2. 두꺼운 지육 (마장동 제외)", "3. 얇은/소형 지육 (잔여 물량)"],
                        "분류 상세 조건": [
                            r"중량 85 \~ 97kg, 등지방 18 \~ 27mm, 등급 1 / 1+",
                            r"중량 97kg 이상 이거나 등지방 27mm 이상",
                            r"중량 85kg 미만 이거나 등지방 18mm 미만"
                        ],
                        "배정가능 두수": [f"{c1_cnt:,} 두", f"{c2_cnt:,} 두", f"{c3_cnt:,} 두"],
                        "비율 (%)": [
                            f"{(c1_cnt/tot_cnt*100):.1f}%" if tot_cnt > 0 else "0%",
                            f"{(c2_cnt/tot_cnt*100):.1f}%" if tot_cnt > 0 else "0%",
                            f"{(c3_cnt/tot_cnt*100):.1f}%" if tot_cnt > 0 else "0%"
                        ]
                    })
                    
                    st.table(analysis_table)
                    st.info(f"💡 **총 입고두수:** {tot_cnt:,}두 (마장동(1/1+등급): {c1_cnt:,}두 / 두꺼운 지육: {c2_cnt:,}두 / 얇은·소형: {c3_cnt:,}두)")
                except Exception as e:
                    st.error(f"등급판정 파일 분석 중 오류 발생: {e}")
            else:
                st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 업로드하시면 규격별 수량 분석표가 표시됩니다.")

            st.markdown("---")

            # -------------------------------------------------------------------------
            # 2. 조건 일치 자동배정 예상 결과 표 & 실행
            # -------------------------------------------------------------------------
            st.markdown("### 🤖 2. 조건별 예상 배정 현황 및 연산 실행")
            
            # 자동 배정 실행 버튼
            if st.button("⚡ 거래처 자동 배정 실행하기", type="primary", use_container_width=True):
                if uploaded_grade:
                    try:
                        uploaded_grade.seek(0)
                        pigs, specs_dict = allocate_pigs_data(uploaded_grade, st.session_state.target_df)
                        st.session_state['allocated_pigs'] = pigs
                        st.session_state['specs_dict'] = specs_dict
                        st.success("✅ 자동 배정이 성공적으로 완료되었습니다!")
                    except Exception as e:
                        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
                else:
                    st.warning("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 먼저 업로드해 주세요.")

            # 연산 결과 요약 표 표시
            if 'allocated_pigs' in st.session_state:
                pigs = st.session_state['allocated_pigs']
                
                # 거래처별 예상 배정두수 요약표 생성
                target_df_curr = st.session_state.target_df.copy()
                allocated_counts = pigs.groupby('배정거래처').size().reset_index(name='예상 배정두수')
                
                summary_alloc = pd.merge(target_df_curr, allocated_counts, left_on='거래처명', right_on='배정거래처', how='left')
                summary_alloc['예상 배정두수'] = summary_alloc['예상 배정두수'].fillna(0).astype(int)
                summary_alloc['목표두수'] = pd.to_numeric(summary_alloc['목표두수'], errors='coerce').fillna(0).astype(int)
                
                # 달성률 계산
                summary_alloc['달성률'] = summary_alloc.apply(
                    lambda r: f"{(r['예상 배정두수']/r['목표두수']*100):.1f}%" if r['목표두수'] > 0 else "-", axis=1
                )
                
                display_summary = summary_alloc[['거래처명', '목표두수', '예상 배정두수', '달성률']]
                st.dataframe(display_summary, use_container_width=True, hide_index=True)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("총 도축 수량", f"{len(pigs)} 두")
                c2.metric("일반 거래처 배정 수량", f"{len(pigs[~pigs['배정거래처'].str.contains('잇다', na=False)])} 두")
                c3.metric("잇다 잔여 할당 수량", f"{len(pigs[pigs['배정거래처'].str.contains('잇다', na=False)])} 두")
                
                st.markdown(" ")
                col_main, _ = st.columns([4, 1])
                with col_main:
                    st.subheader("📋 전체 개체별 세부 배정 내역")
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    
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
                        file_name=f"{today_str}_배정결과.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                    display_df = pigs[['도체번호', '성별', '중량', '등지방', '등급', '배정거래처', '이력번호', '출하농가']].copy()
                    calc_height = (len(display_df) + 1) * 35 + 10
                    st.dataframe(display_df, height=calc_height, use_container_width=True, column_config=get_centered_column_config(display_df))

            st.markdown("---")

            # -------------------------------------------------------------------------
            # 3. 거래처별 목표두수 / 변동두수 수기 조정 (하단)
            # -------------------------------------------------------------------------
            st.markdown("### ✏️ 3. 거래처별 목표두수 / 변동두수 수기 조정")
            with st.expander("📌 거래처별 목표두수 수기 조정 표 (클릭하여 열기)", expanded=True):
                st.info("💡 목표 두수에 변동이 있으면 아래 표에서 수량을 직접 수정하거나 새로운 거래처를 추가하세요.")
                edited_target_df = st.data_editor(
                    st.session_state.target_df,
                    num_rows="dynamic",
                    use_container_width=True,
                    height=500,
                    key="target_editor",
                    column_config={
                        "거래처명": st.column_config.Column("거래처명", alignment="center"), 
                        "목표두수": st.column_config.Column("목표두수", alignment="center")
                    }
                )
                if st.button("💾 두수 변동사항 적용", type="secondary", use_container_width=True):
                    st.session_state.target_df = edited_target_df
                    st.success("✅ 목표두수가 업데이트되었습니다. 상단의 [⚡ 거래처 자동 배정 실행하기] 버튼을 누르세요!")

        # ----------------- 탭 2: 거래처별 배정 상세 -----------------
        with tab2:
            st.subheader("🏢 거래처별 개별 배정 내역 및 명단")
            if 'allocated_pigs' in st.session_state and 'specs_dict' in st.session_state:
                pigs_all = st.session_state['allocated_pigs']
                specs_dict = st.session_state['specs_dict']
                
                all_assigned = [c for c in pigs_all['배정거래처'].unique() if "잇다" not in c]
                main_company_map = {}
                for c in all_assigned:
                    base_name = c.split()[0]
                    if base_name not in main_company_map:
                        main_company_map[base_name] = []
                    main_company_map[base_name].append(c)

                company_list = sorted(list(main_company_map.keys()))
                
                if company_list:
                    if 'selected_company' not in st.session_state or st.session_state.selected_company not in company_list:
                        st.session_state.selected_company = company_list[0]

                    st.write("👉 **조회할 거래처를 클릭하세요 (가나다순 정렬):**")
                    cols = st.columns(min(len(company_list), 6))
                    for idx, comp in enumerate(company_list):
                        col_idx = idx % 6
                        is_selected = (comp == st.session_state.selected_company)
                        if cols[col_idx].button(f"📌 {comp}" if is_selected else comp, key=f"btn_comp_{comp}", type="primary" if is_selected else "secondary", use_container_width=True):
                            st.session_state.selected_company = comp
                            st.rerun()

                    st.markdown("---")
                    selected_main = st.session_state.selected_company
                    sub_companies = sorted(main_company_map[selected_main])

                    for sub_comp in sub_companies:
                        st.markdown(f"### **[{sub_comp}] 배정 명단**")

                        spec = specs_dict.get(sub_comp, None)
                        if spec:
                            ex_farm_info = f" | 배제농가: {', '.join(spec['배제농가'])}" if spec['배제농가'] else ""
                            st.markdown(f"""
                            <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 10px 15px; font-size: 14px; color: #495057; margin-bottom: 15px;">
                                <strong>목표두수:</strong> {spec['목표두수']}두 | <strong>중량:</strong> {spec['weight_str']} kg | <strong>등지방:</strong> {spec['fat_str']} mm | <strong>등급:</strong> {spec['grade_str']} | <strong>암 비율:</strong> {spec['f_ratio_str']}{ex_farm_info}
                            </div>
                            """, unsafe_allow_html=True)

                        comp_df = pigs_all[pigs_all['배정거래처'] == sub_comp].copy()
                        comp_df.reset_index(drop=True, inplace=True)
                        comp_df.index = comp_df.index + 1

                        remarks = []
                        for idx, row in comp_df.iterrows():
                            if not spec: remarks.append("-"); continue
                            diffs = []
                            if row['중량'] < spec['w_min']: diffs.append(f"중량미달({row['중량']}kg < {spec['w_min']}kg)")
                            elif row['중량'] > spec['w_max']: diffs.append(f"중량초과({row['중량']}kg > {spec['w_max']}kg)")
                            if row['등지방'] < spec['f_min']: diffs.append(f"등지방미달({row['등지방']}mm < {spec['f_min']}mm)")
                            elif row['등지방'] > spec['f_max']: diffs.append(f"등지방초과({row['등지방']}mm > {spec['f_max']}mm)")
                            if spec['grades'] and str(row['등급']).strip() not in spec['grades']: diffs.append(f"등급불일치({row['등급']})")
                            if spec['배제농가'] and any(farm in str(row['출하농가']) for farm in spec['배제농가']): diffs.append(f"배제농가포함({row['출하농가']})")
                            remarks.append(",\n".join(diffs) if diffs else "스펙일치")

                        comp_df['비고'] = remarks
                        c_cnt = len(comp_df[comp_df['성별'] == '거세'])
                        f_cnt = len(comp_df[comp_df['성별'] == '암'])
                        
                        m1, m2, m3, m4, m5 = st.columns(5)
                        m1.metric("총 배정 수량", f"{len(comp_df)} 두")
                        m2.metric("거세 수량", f"{c_cnt} 두")
                        m3.metric("암 수량", f"{f_cnt} 두")
                        m4.metric("평균 중량", f"{comp_df['중량'].mean():.1f} kg" if not comp_df.empty else "0 kg")
                        m5.metric("평균 등지방", f"{comp_df['등지방'].mean():.1f} mm" if not comp_df.empty else "0 mm")
                        
                        st.markdown(" ")
                        output_comp = io.BytesIO()
                        with pd.ExcelWriter(output_comp, engine='openpyxl') as writer: comp_df.to_excel(writer, sheet_name=sub_comp)
                        
                        st.download_button(label=f"📥 [{sub_comp}] 배정 명단 엑셀 다운로드", data=output_comp.getvalue(), file_name=f"{sub_comp}_배정명단.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                        
                        comp_display = comp_df[['도체번호', '성별', '중량', '등지방', '등급', '비고', '이력번호', '출하농가']].copy()
                        calc_height = (len(comp_display) + 1) * 35 + 10
                        st.dataframe(comp_display, height=calc_height, use_container_width=True, column_config=get_centered_column_config(comp_display))
                        st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 업로드해 주세요.")

        # ----------------- 탭 3: 잇다 배정 (잇다 1 / 잇다 2) -----------------
        with tab3:
            st.subheader("🚚 잇다 배정 내역")
            if 'allocated_pigs' in st.session_state:
                pigs_all = st.session_state['allocated_pigs']
                jn_pigs = pigs_all[pigs_all['배정거래처'].str.contains('잇다', na=False)].copy()
                
                if not jn_pigs.empty:
                    for ita_type in sorted(jn_pigs['배정거래처'].unique()):
                        jn_df = jn_pigs[jn_pigs['배정거래처'] == ita_type].copy()
                        jn_df.reset_index(drop=True, inplace=True)
                        jn_df.index = jn_df.index + 1
                        
                        st.markdown(f"### **[{ita_type}] 배정 내역**")
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 12px 18px; font-size: 15px; color: #333333; margin-bottom: 15px;">
                            <strong>수량 :</strong> {len(jn_df)}두 / <strong>총중량 :</strong> {jn_df['중량'].sum():,.1f} kg
                        </div>
                        """, unsafe_allow_html=True)

                        jn_export = pd.DataFrame({
                            'No.': jn_df.index, '작업장명': '나주농협', '판정일': datetime.now().day,
                            '도체번호': jn_df['도체번호'], '판정방법': '온', '도체형태': '탕박',
                            '성별': jn_df['성별'], '도체중(kg)': jn_df['중량'], '등지방두께': jn_df['등지방'],
                            '최종등급': jn_df['등급'], '출하농가': jn_df['출하농가'], '이력번호': jn_df['이력번호'], '거래처': ita_type
                        })

                        output_jn = io.BytesIO()
                        with pd.ExcelWriter(output_jn, engine='openpyxl') as writer: jn_export.to_excel(writer, sheet_name=ita_type, index=False)
                        today_str = datetime.now().strftime("%m%d")
                        
                        st.download_button(label=f"📥 [{ita_type}] 전달용 엑셀 다운로드 ({today_str} {ita_type}.xlsx)", data=output_jn.getvalue(), file_name=f"{today_str}_{ita_type}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                        calc_jn_height = (len(jn_export) + 1) * 35 + 10
                        st.dataframe(jn_export, height=calc_jn_height, use_container_width=True, column_config=get_centered_column_config(jn_export))
                        st.markdown("<br>", unsafe_allow_html=True)
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
                    return parts[1], parts[0]
                return s_val, '-'

            pigs_all[['농가_명', '사료사_명']] = pigs_all['출하농가'].apply(lambda x: pd.Series(extract_feed_and_farm(x)))
            farm_groups = pigs_all.groupby(['농가_명', '사료사_명'])
            
            rows = []
            for (farm_name, feed_name), group in farm_groups:
                head_cnt = len(group)
                total_weight = group['중량'].sum()
                live_weight = total_weight / (76.32 / 100.0)
                real_dressing_rate = (total_weight / live_weight * 100) if live_weight > 0 else 0.0

                spec_target = group[(group['중량'] >= 86) & (group['중량'] <= 96) & (group['등지방'] >= 19) & (group['등지방'] <= 23)]
                spec_target_cnt = len(spec_target)

                cnt_1plus = len(group[group['등급'] == '1+'])
                cnt_1 = len(group[group['등급'] == '1'])
                cnt_2 = len(group[group['등급'] == '2'])

                rows.append({
                    '농가': farm_name, '사료사': feed_name, '두수': f"{head_cnt:,}", '중량': f"{int(round(total_weight)):,}",
                    '생체': f"{int(round(live_weight)):,}", '생체평균': f"{(live_weight / head_cnt):.2f}" if head_cnt > 0 else "0.00",
                    '도체 kg': f"{(total_weight / head_cnt):.1f}" if head_cnt > 0 else "0.0", '등지방 mm': f"{group['등지방'].mean():.1f}",
                    '지육율': f"{real_dressing_rate:.2f}%", '86~96,19~23': f"{spec_target_cnt:,}", '스펙비율': f"{(spec_target_cnt / head_cnt * 100):.1f}%" if head_cnt > 0 else "0.0%",
                    '암': f"{len(group[group['성별'] == '암']):,}", '1+': f"{cnt_1plus:,}", '1+ 중량': f"{int(round(group[group['등급'] == '1+']['중량'].sum())):,}",
                    '1': f"{cnt_1:,}", '1 중량': f"{int(round(group[group['등급'] == '1']['중량'].sum())):,}",
                    '2': f"{cnt_2:,}", '2 중량': f"{int(round(group[group['등급'] == '2']['중량'].sum())):,}",
                    '1+,1 비율': f"{((cnt_1plus + cnt_1) / head_cnt * 100):.2f}%" if head_cnt > 0 else "0.00%"
                })

            analysis_df = pd.DataFrame(rows)

            total_head = len(pigs_all)
            total_w = pigs_all['중량'].sum()
            total_live = total_w / (76.32 / 100.0)

            sum_row = pd.DataFrame([{
                '농가': '합계', '사료사': '-', '두수': f"{total_head:,}", '중량': f"{int(round(total_w)):,}",
                '생체': f"{int(round(total_live)):,}", '생체평균': f"{(total_live / total_head):.2f}" if total_head > 0 else "0.00",
                '도체 kg': f"{(total_w / total_head):.1f}" if total_head > 0 else "0.0", '등지방 mm': f"{pigs_all['등지방'].mean():.1f}",
                '지육율': f"{(total_w / total_live * 100):.2f}%" if total_live > 0 else "0.00%",
                '86~96,19~23': f"{len(pigs_all[(pigs_all['중량'] >= 86) & (pigs_all['중량'] <= 96) & (pigs_all['등지방'] >= 19) & (pigs_all['등지방'] <= 23)]):,}",
                '스펙비율': f"{(len(pigs_all[(pigs_all['중량'] >= 86) & (pigs_all['중량'] <= 96) & (pigs_all['등지방'] >= 19) & (pigs_all['등지방'] <= 23)]) / total_head * 100):.1f}%" if total_head > 0 else "0.0%",
                '암': f"{len(pigs_all[pigs_all['성별'] == '암']):,}", '1+': f"{len(pigs_all[pigs_all['등급'] == '1+']):,}", '1+ 중량': f"{int(round(pigs_all[pigs_all['등급'] == '1+']['중량'].sum())):,}",
                '1': f"{len(pigs_all[pigs_all['등급'] == '1']):,}", '1 중량': f"{int(round(pigs_all[pigs_all['등급'] == '1']['중량'].sum())):,}",
                '2': f"{len(pigs_all[pigs_all['등급'] == '2']):,}", '2 중량': f"{int(round(pigs_all[pigs_all['등급'] == '2']['중량'].sum())):,}",
                '1+,1 비율': f"{((len(pigs_all[pigs_all['등급'] == '1+']) + len(pigs_all[pigs_all['등급'] == '1'])) / total_head * 100):.2f}%" if total_head > 0 else "0.00%"
            }])

            final_analysis_df = pd.concat([analysis_df, sum_row], ignore_index=True)
            st.subheader("📋 출하 농가별 세부 성적 및 등급 분석")
            
            output_anal = io.BytesIO()
            with pd.ExcelWriter(output_anal, engine='openpyxl') as writer: final_analysis_df.to_excel(writer, sheet_name='농가분석', index=False)
            
            st.download_button(label="📥 농가분석 결과 엑셀 다운로드", data=output_anal.getvalue(), file_name=f"농가분석_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            styled_df = final_analysis_df.style.apply(lambda row: ['font-weight: bold; background-color: #f1f3f5;'] * len(row) if row['농가'] == '합계' else [''] * len(row), axis=1)
            
            calc_height = (len(final_analysis_df) + 1) * 35 + 10
            st.dataframe(styled_df, height=calc_height, use_container_width=True, hide_index=True, column_config=get_centered_column_config(final_analysis_df))
        else:
            st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 업로드하시면 농가 분석 결과가 즉시 생성됩니다.")
