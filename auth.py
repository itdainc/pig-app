# auth.py
import streamlit as st

# 🔒 사이드바 접속 비밀번호 설정 (원하시는 비밀번호로 변경하세요)
APP_PASSWORD = "00885"

def check_password():
    """로그인 검증 함수"""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 로그인 / 주식회사 잇다")
        st.info("💡 접속 권한이 필요합니다. 비밀번호를 입력해 주세요.")
        
        user_input = st.text_input("비밀번호 입력", type="password", key="password_input")
        if st.button("접속하기", type="primary", use_container_width=True):
            if user_input == APP_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ 비밀번호가 올바르지 않습니다.")
        return False
    return True
