import streamlit as st

# 🔒 비밀번호 설정
APP_PASSWORD = "1234"

def check_password():
    """엔터 키 지원 로그인 검증 함수"""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 로그인 / 주식회사 잇다")
        st.info("💡 접속 권한이 필요합니다. 비밀번호를 입력 후 엔터(Enter)를 누르세요.")
        
        # st.form으로 감싸서 엔터키 작동 보장
        with st.form("login_form", clear_on_submit=False):
            user_input = st.text_input("비밀번호 입력", type="password", key="password_input")
            submit_button = st.form_submit_button("접속하기", type="primary", use_container_width=True)
            
            if submit_button:
                if user_input == APP_PASSWORD:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ 비밀번호가 올바르지 않습니다.")
        return False
    return True
