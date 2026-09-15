import streamlit as st
import pandas as pd
import io
import numpy as np
from datetime import datetime

st.set_page_config(page_title="도축 스펙 거래처 자동 배정", layout="wide", page_icon="🐖")

st.title("🐖 돼지 도축 스펙 거래처 자동 배정 시스템")

# ----------------- 구글 시트 연동 -----------------
try:
    from streamlit_gsheets import GSheetsConnection
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    conn = None

# 기본 스펙 불러오기
try:
    if conn:
        spec_df = conn.read(worksheet="스펙", ttl="1m")
    else:
        raise Exception("연동 미설정")
except Exception:
    default_specs = [
        {"업체명": "대용식품", "중량(kg)": "85~90", "등지방(mm)": "18~21", "등급": "1,1+", "거세": 6, "암": 4},
        {"업체명": "민강", "중량(kg)": "85~97", "등지방(mm)": "21~25", "등급": "1,1+", "거세": 5, "암": 5},
        {"업체명": "예소야", "중량(kg)": "85~97", "등지방(mm)": "22~25", "등급": "1,1+", "거세": 6, "암": 4},
        {"업체명": "승민", "중량(kg)": "84~88", "등지방(mm)": "20", "등급": "1,1+", "거세": 0, "암": 10},
        {"업체명": "자운", "중량(kg)": "85~95", "등지방(mm)": "22~25", "등급": "1,1+", "거세": 0, "암": 10},
        {"업체명": "제이이", "중량(kg)": "88~97", "등지방(mm)": "25~27", "등급": "1,1+", "거세": 5, "암": 5},
        {"업체명": "돼랑이", "중량(kg)": "85~90", "등지방(mm)": "25~26", "등급": "1,1+", "거세": 5, "암": 5},
        {"업체명": "명성", "중량(kg)": "87~97", "등지방(mm)": "20~22", "등급": "1,1+", "거세": 8, "암": 2},
        {"업체명": "염주골", "중량(kg)": "98~109", "등지방(mm)": "20~27", "등급": "2", "거세": 5, "암": 5},
        {"업체명": "흥부축산", "중량(kg)": "75~86", "등지방(mm)": "18~22", "등급": "1,1+,2", "거세": 6, "암": 4},
        {"업체명": "미소", "중량(kg)": "80~97", "등지방(mm)": "17~25", "등급": "1,1+", "거세": 6, "암": 4},
        {"업체명": "프라임미트", "중량(kg)": "80~103", "등지방(mm)": "20~34", "등급": "1,1+,2", "거세": 7, "암": 3},
    ]
    spec_df = pd.DataFrame(default_specs)

if 'spec_df' not in st.session_state:
    st.session_state.spec_df = spec_df

# ----------------- 탭 구성 (요청 반영) -----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚀 자동 배정 실행", 
    "🏢 거래처별 배정 상세",
    "⚙️ 거래처 스펙 관리", 
    "📅 배정 이력 조회 (구글 시트)",
    "🚚 전남지사 배정 (잇다)"
])

# ----------------- 탭 1: 자동 배정 -----------------
with tab1:
    st.sidebar.header("📁 파일 업로드")
    uploaded_grade = st.sidebar.file_uploader("1. 등급판정 결과 파일 (.xls/.xlsx)", type=["xls", "xlsx"])

    if uploaded_grade:
        try:
            df_g = pd.read_excel(uploaded_grade, header=3)
            
            pigs = pd.DataFrame({
                '도체번호': df_g.iloc[:, 4],
                '성별': df_g.iloc[:, 7],
                '중량': pd.to_numeric(df_g.iloc[:, 8], errors='coerce'),
                '등지방': pd.to_numeric(df_g.iloc[:, 9], errors='coerce'),
                '등급': df_g.iloc[:, 22],
                '출하농가': '',
                '이력번호': ''
            }).dropna(subset=['중량']).copy()

            pigs.reset_index(drop=True, inplace=True)
            pigs.index = pigs.index + 1

            specs = []
            for idx, row in st.session_state.spec_df.iterrows():
                name = str(row['업체명'])
                weight_str = str(row['중량(kg)'])
                fat_str = str(row['등지방(mm)'])
                grade_str = str(row['등급'])

                w_min, w_max = (map(float, weight_str.split('~')) if '~' in weight_str 
                                else (float(weight_str), float(weight_str)) if weight_str!='nan' else (0, 999))
                f_min, f_max = (map(float, fat_str.split('~')) if '~' in fat_str 
                                else (float(fat_str), float(fat_str)) if fat_str!='nan' else (0, 999))
                grades = [g.strip() for g in grade_str.split(',')] if grade_str != 'nan' else []

                c_cnt = float(row['거세']) if pd.notna(row['거세']) else 0.0
                f_cnt = float(row['암']) if pd.notna(row['암']) else 0.0
                total_ratio = c_cnt + f_cnt
                
                c_ratio = (c_cnt / total_ratio) if total_ratio > 0 else 0.5
                f_ratio = (f_cnt / total_ratio) if total_ratio > 0 else 0.5

                specs.append({
                    '업체명': name, 'w_min': w_min, 'w_max': w_max,
                    'f_min': f_min, 'f_max': f_max, 'grades': grades,
                    '거세비율': c_ratio, '암비율': f_ratio
                })

            pigs['배정거래처'] = '미배정'

            # ----------------- 비율 기반 배정 로직 -----------------
            # 1단계: 스펙 100% 매칭 소진
            for spec in specs:
                company = spec['업체명']
                
                cond_base = (
                    (pigs['배정거래처'] == '미배정') &
                    (pigs['중량'] >= spec['w_min']) & (pigs['중량'] <= spec['w_max']) &
                    (pigs['등지방'] >= spec['f_min']) & (pigs['등지방'] <= spec['f_max'])
                )
                if spec['grades']:
                    cond_base &= (pigs['등급'].isin(spec['grades']))

                matched_all = pigs[cond_base]
                if not matched_all.empty:
                    matched_c = matched_all[matched_all['성별'] == '거세']
                    matched_f = matched_all[matched_all['성별'] == '암']

                    if spec['거세비율'] == 0:
                        pigs.loc[matched_f.index, '배정거래처'] = company
                    elif spec['암비율'] == 0:
                        pigs.loc[matched_c.index, '배정거래처'] = company
                    else:
                        pigs.loc[matched_c.index, '배정거래처'] = company
                        pigs.loc[matched_f.index, '배정거래처'] = company

            # 2단계: 스펙 유사도 유연 소진 (약 105두 잔여시 중단)
            for spec in specs:
                unassigned_cnt = len(pigs[pigs['배정거래처'] == '미배정'])
                if unassigned_cnt <= 105:
                    break

                candidates = pigs[pigs['배정거래처'] == '미배정'].copy()
                if not candidates.empty:
                    w_diff = np.maximum(0, np.maximum(spec['w_min'] - candidates['중량'], candidates['중량'] - spec['w_max']))
                    f_diff = np.maximum(0, np.maximum(spec['f_min'] - candidates['등지방'], candidates['등지방'] - spec['f_max']))
                    candidates['score'] = w_diff * 1.5 + f_diff

                    matched_relaxed = candidates.sort_values('score').head(15)
                    pigs.loc[matched_relaxed.index, '배정거래처'] = spec['업체명']

            # 남아있는 잔여 물량을 전남지사(잇다)로 최종 할당
            unassigned_mask = pigs['배정거래처'] == '미배정'
            pigs.loc[unassigned_mask, '배정거래처'] = '전남지사(잇다)'

            st.session_state['allocated_pigs'] = pigs

            # ----------------- 좌측 배정요약 표 -----------------
            summary = pigs.groupby(['배정거래처', '성별']).size().unstack(fill_value=0)
            if '거세' not in summary.columns: summary['거세'] = 0
            if '암' not in summary.columns: summary['암'] = 0
            
            summary = summary[['거세', '암']]
            summary['합계'] = summary['거세'] + summary['암']
            summary.columns.name = None

            st.sidebar.markdown("---")
            st.sidebar.subheader("📊 거래처별 배정 요약")
            st.sidebar.dataframe(summary, use_container_width=True, height=500)

            # ----------------- 상단 지표 -----------------
            total_pigs = len(pigs)
            assigned_pigs = len(pigs[pigs['배정거래처'] != '전남지사(잇다)'])
            jn_pigs = len(pigs[pigs['배정거래처'] == '전남지사(잇다)'])

            c1, c2, c3 = st.columns(3)
            c1.metric("총 도축 수량", f"{total_pigs} 두")
            c2.metric("일반 거래처 배정 수량", f"{assigned_pigs} 두")
            c3.metric("전남지사 배정 수량", f"{jn_pigs} 두")

            st.markdown("---")
            
            col_main, _ = st.columns([3, 1])
            with col_main:
                st.subheader("📋 전체 개체별 세부 배정 내역")
                
                today_tab_name = datetime.now().strftime("%Y-%m-%d")
                
                col_btn_save, col_btn_dl = st.columns([1, 1])
                with col_btn_save:
                    if st.button(f"☁️ 구글 시트로 당일({today_tab_name}) 탭 생성 및 저장", type="primary"):
                        try:
                            if conn is None:
                                raise Exception("구글 시트 연동 설정 필요")
                            conn.update(worksheet=today_tab_name, data=pigs)
                            st.success(f"✅ 구글 시트에 [{today_tab_name}] 탭이 생성되고 저장되었습니다!")
                        except Exception as e:
                            st.error(f"구글 시트 저장 실패: Secrets 설정을 진행해 주세요. ({e})")

                with col_btn_dl:
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

                st.dataframe(pigs[['도체번호', '성별', '중량', '등지방', '등급', '배정거래처', '이력번호', '출하농가']], height=750, use_container_width=True)

        except Exception as e:
            st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
    else:
        st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]만 올려주시면 바로 배정됩니다.")

# ----------------- 탭 2: 거래처별 배정 상세 (신규 추가) -----------------
with tab2:
    st.subheader("🏢 거래처별 개별 배정 내역 및 명단")
    
    if 'allocated_pigs' in st.session_state:
        pigs_all = st.session_state['allocated_pigs']
        company_list = [c for c in pigs_all['배정거래처'].unique() if c != '전남지사(잇다)']
        
        if company_list:
            selected_company = st.selectbox("📌 조회 및 출력할 거래처 선택:", company_list)
            
            comp_df = pigs_all[pigs_all['배정거래처'] == selected_company].copy()
            comp_df.reset_index(drop=True, inplace=True)
            comp_df.index = comp_df.index + 1
            
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
            
            st.markdown("---")
            
            # 개별 거래처 엑셀 다운로드
            output_comp = io.BytesIO()
            with pd.ExcelWriter(output_comp, engine='openpyxl') as writer:
                comp_df.to_excel(writer, sheet_name=selected_company)
            comp_data = output_comp.getvalue()
            
            st.download_button(
                label=f"📥 {selected_company} 전달용 엑셀 다운로드",
                data=comp_data,
                file_name=f"{selected_company}_배정명단.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
            
            st.dataframe(comp_df[['도체번호', '성별', '중량', '등지방', '등급', '이력번호', '출하농가']], height=650, use_container_width=True)
        else:
            st.info("배정된 일반 거래처 내역이 없습니다.")
    else:
        st.info("👈 [🚀 자동 배정 실행] 탭에서 등급판정 파일을 먼저 업로드해 주세요.")

# ----------------- 탭 3: 거래처 스펙 관리 -----------------
with tab3:
    st.subheader("⚙️ 등록된 거래처 스펙 수정 및 추가 (구글 시트 연동)")
    st.write("표 안의 셀을 클릭하여 숫자를 수정하거나 항목을 추가/삭제할 수 있습니다.")

    col_spec, _ = st.columns([3, 2])
    with col_spec:
        edited_df = st.data_editor(
            st.session_state.spec_df,
            num_rows="dynamic",
            use_container_width=True,
            height=600,
            key="spec_editor"
        )

        if st.button("💾 구글 시트에 스펙 변경사항 저장", type="primary"):
            try:
                if conn is None:
                    raise Exception("Secrets 필요")
                conn.update(worksheet="스펙", data=edited_df)
                st.session_state.spec_df = edited_df
                st.success("거래처 스펙 변경 사항이 구글 시트 ['스펙'] 탭에 성공적으로 동기화되었습니다!")
            except Exception:
                st.session_state.spec_df = edited_df
                st.success("스펙이 임시 반영되었습니다.")

# ----------------- 탭 4: 배정 이력 조회 -----------------
with tab4:
    st.subheader("📅 구글 시트 날짜별(탭별) 배정 이력 조회")
    try:
        if conn is None:
            raise Exception("Secrets 필요")
        
        search_date = st.date_input("조회하고 싶은 날짜 선택", datetime.now())
        target_tab = search_date.strftime("%Y-%m-%d")
        
        if st.button(f"🔍 [{target_tab}] 이력 불러오기"):
            try:
                hist_df = conn.read(worksheet=target_tab, ttl="0s")
                if hist_df.empty:
                    st.warning(f"[{target_tab}] 탭은 존재하지만 데이터가 없습니다.")
                else:
                    st.write(f"### 📌 {target_tab} 배정 이력")
                    summary_hist = hist_df.groupby(['배정거래처', '성별']).size().unstack(fill_value=0)
                    
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.write("**거래처별 요약**")
                        st.dataframe(summary_hist, use_container_width=True)
                    with c2:
                        st.write("**상세 개체 내역**")
                        st.dataframe(hist_df, height=600, use_container_width=True)
            except Exception:
                st.error(f"❌ [{target_tab}] 날짜로 저장된 구글 시트 탭이 없습니다.")

    except Exception:
        st.info("💡 구글 시트 연동 완료 시 날짜별 이력 조회가 가능합니다.")

# ----------------- 탭 5: 전남지사 배정 (잇다) -----------------
with tab5:
    st.subheader("🚚 전남지사(잇다) 전달용 표 및 엑셀 다운로드")
    
    if 'allocated_pigs' in st.session_state:
        pigs_all = st.session_state['allocated_pigs']
        jn_df = pigs_all[pigs_all['배정거래처'] == '전남지사(잇다)'].copy()
        
        if not jn_df.empty:
            jn_df.reset_index(drop=True, inplace=True)
            jn_df.index = jn_df.index + 1
            
            total_jn_count = len(jn_df)
            total_jn_weight = jn_df['중량'].sum()

            st.success(f"📌 **전남지사 전달 총 수량:** {total_jn_count}두 / **총 중량:** {total_jn_weight:,.1f} kg")

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
                '출하농가': '',
                '이력번호': '',
                '거래처': '잇다'
            })

            output_jn = io.BytesIO()
            with pd.ExcelWriter(output_jn, engine='openpyxl') as writer:
                jn_export.to_excel(writer, sheet_name='잇다', index=False)
            jn_data = output_jn.getvalue()

            today_str = datetime.now().strftime("%m%d")
            st.download_button(
                label=f"📥 전남지사 전달용 엑셀 다운로드 ({today_str} 잇다.xlsx)",
                data=jn_data,
                file_name=f"{today_str} 잇다.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )

            st.markdown("---")
            st.dataframe(jn_export, height=750, use_container_width=True)

        else:
            st.warning("전남지사로 할당된 물량이 없습니다.")
    else:
        st.info("👈 [🚀 자동 배정 실행] 탭에서 등급판정 파일을 먼저 업로드해 주세요.")
