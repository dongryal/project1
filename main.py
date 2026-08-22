
import streamlit as st
import json
import os
import difflib
from datetime import datetime
import pandas as pd
import streamlit.components.v1 as components

# ----------------------------------------------------------------------------
# 기본 설정
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="개인정보처리방침 개정 관리 시스템",
    page_icon="🔐",
    layout="wide",
)

DATA_DIR = "data"
DATA_PATH = os.path.join(DATA_DIR, "policy_history.json")
INITIAL_POLICY_PATH = os.path.join(DATA_DIR, "initial_policy.txt")

SOURCE_URL = "https://privacy.11st.co.kr/"

FALLBACK_POLICY = (
    "(초기 전문이 아직 등록되지 않았습니다.)\n\n"
    f"1) '{INITIAL_POLICY_PATH}' 파일에 11번가 개인정보처리방침 전문을 붙여넣은 뒤 앱을 다시 실행하거나,\n"
    "2) '2. 개인정보처리방침 수정' 메뉴에서 직접 본문을 입력해 저장해 주세요.\n\n"
    f"공식 원문 출처: {SOURCE_URL}"
)


# ----------------------------------------------------------------------------
# 데이터 입출력 함수
# ----------------------------------------------------------------------------
def load_initial_content() -> str:
    """data/initial_policy.txt 파일이 있으면 그 내용을, 없으면 안내 문구를 반환한다."""
    if os.path.exists(INITIAL_POLICY_PATH):
        with open(INITIAL_POLICY_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            return content
    return FALLBACK_POLICY


def load_history():
    """저장된 이력 파일을 불러오거나, 없으면 최초 버전을 생성한다."""
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_DIR, exist_ok=True)
        initial_history = [
            {
                "version": "1.0",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "editor": "관리자",
                "reason": "최초 등록",
                "content": load_initial_content(),
            }
        ]
        save_history(initial_history)
        return initial_history

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def next_minor_version(current_version: str) -> str:
    """1.0 -> 1.1, 1.9 -> 1.10 처럼 부분 개정 버전을 계산한다."""
    try:
        major, minor = current_version.split(".")
        return f"{major}.{int(minor) + 1}"
    except ValueError:
        return current_version + ".1"


def next_major_version(current_version: str) -> str:
    """1.3 -> 2.0 처럼 전면 개정 버전을 계산한다."""
    try:
        major, _ = current_version.split(".")
        return f"{int(major) + 1}.0"
    except ValueError:
        return current_version + ".0"


# ----------------------------------------------------------------------------
# 세션 상태 초기화
# ----------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = load_history()

history = st.session_state.history
latest = history[-1]

# ----------------------------------------------------------------------------
# 사이드바
# ----------------------------------------------------------------------------
st.sidebar.title("🔐 메뉴")
menu = st.sidebar.radio(
    "이동할 메뉴를 선택하세요",
    [
        "1. 개인정보처리방침 전문",
        "2. 개인정보처리방침 수정",
        "3. 개인정보처리방침 이력관리",
    ],
)

st.sidebar.markdown("---")
st.sidebar.metric("현재 버전", f"v{latest['version']}")
st.sidebar.caption(f"최종 수정일: {latest['date']}")
st.sidebar.caption(f"최종 수정자: {latest['editor']}")
st.sidebar.markdown("---")
st.sidebar.caption("공식 원문 출처")
st.sidebar.markdown(f"[privacy.11st.co.kr]({SOURCE_URL})")

# ----------------------------------------------------------------------------
# 1. 개인정보처리방침 전문
# ----------------------------------------------------------------------------
if menu.startswith("1"):
    st.title("📄 개인정보처리방침 전문")

    with st.expander("📎 공식 원문 페이지 (11번가)", expanded=False):
        st.caption("전문 원본은 아래 공식 페이지에서 항상 최신 상태로 확인할 수 있습니다.")
        components.iframe(SOURCE_URL, height=500, scrolling=True)

    version_labels = [f"v{h['version']} ({h['date']})" for h in history]
    selected_idx = st.selectbox(
        "조회할 버전을 선택하세요",
        options=list(range(len(history))),
        format_func=lambda i: version_labels[i],
        index=len(history) - 1,
    )
    selected = history[selected_idx]

    info_col, download_col = st.columns([3, 1])
    with info_col:
        st.subheader(f"v{selected['version']}  ·  {selected['date']}")
        st.caption(f"작성자: {selected['editor']}   |   개정 사유: {selected['reason']}")
    with download_col:
        st.download_button(
            "⬇️ 텍스트 다운로드",
            data=selected["content"],
            file_name=f"privacy_policy_v{selected['version']}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    keyword = st.text_input("🔍 본문 내 검색", placeholder="검색어를 입력하세요 (예: 보유기간)")
    content = selected["content"]
    if keyword:
        hit_count = content.count(keyword)
        if hit_count > 0:
            st.success(f"'{keyword}' 검색 결과: {hit_count}건 일치")
        else:
            st.warning(f"'{keyword}'에 대한 검색 결과가 없습니다.")

    st.text_area("전문", content, height=550, disabled=True, label_visibility="collapsed")

# ----------------------------------------------------------------------------
# 2. 개인정보처리방침 수정
# ----------------------------------------------------------------------------
elif menu.startswith("2"):
    st.title("✏️ 개인정보처리방침 수정")
    st.caption(f"현재 최신 버전: v{latest['version']} ({latest['date']}, {latest['editor']})")

    with st.form("edit_form", clear_on_submit=False):
        new_content = st.text_area(
            "본문 수정",
            value=latest["content"],
            height=420,
        )

        col1, col2 = st.columns(2)
        with col1:
            editor = st.text_input("작성자", placeholder="담당자 이름을 입력하세요")
        with col2:
            change_type = st.selectbox(
                "개정 구분",
                ["부분 개정 (minor)", "전면 개정 (major)"],
            )

        reason = st.text_area(
            "개정 사유",
            height=100,
            placeholder="예: 개인정보 보관기간 조항 변경, 위탁업체 목록 추가 등",
        )

        submitted = st.form_submit_button("변경사항 저장", type="primary", use_container_width=True)

    if submitted:
        if not editor.strip():
            st.error("작성자를 입력해 주세요.")
        elif not reason.strip():
            st.error("개정 사유를 입력해 주세요.")
        elif new_content.strip() == latest["content"].strip():
            st.warning("기존 내용과 변경된 부분이 없습니다.")
        else:
            new_version = (
                next_major_version(latest["version"])
                if change_type.startswith("전면")
                else next_minor_version(latest["version"])
            )
            new_entry = {
                "version": new_version,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "editor": editor.strip(),
                "reason": reason.strip(),
                "content": new_content,
            }
            history.append(new_entry)
            save_history(history)
            st.success(f"v{new_version} 버전으로 저장되었습니다.")
            st.rerun()

    with st.expander("💡 최신 버전과 변경 전 내용 비교 미리보기", expanded=False):
        st.caption("저장 전, 최신 버전(v{})과의 차이를 미리 확인하려면 아래를 펼쳐보세요.".format(latest["version"]))
        st.info("실제 비교는 저장 후 '3. 개인정보처리방침 이력관리' 메뉴에서 두 버전을 선택해 확인할 수 있습니다.")

# ----------------------------------------------------------------------------
# 3. 개인정보처리방침 이력관리
# ----------------------------------------------------------------------------
else:
    st.title("🗂️ 개인정보처리방침 이력관리")

    df = pd.DataFrame(
        [
            {
                "버전": f"v{h['version']}",
                "일자": h["date"],
                "작성자": h["editor"],
                "개정 사유": h["reason"],
            }
            for h in history
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇️ 이력 CSV 다운로드",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="policy_history.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.subheader("🔍 버전 간 비교")

    labels = [f"v{h['version']} ({h['date']})" for h in history]
    col1, col2 = st.columns(2)
    with col1:
        v1_idx = st.selectbox(
            "비교 버전 A (이전)",
            options=list(range(len(history))),
            format_func=lambda i: labels[i],
            index=max(0, len(history) - 2),
            key="compare_a",
        )
    with col2:
        v2_idx = st.selectbox(
            "비교 버전 B (이후)",
            options=list(range(len(history))),
            format_func=lambda i: labels[i],
            index=len(history) - 1,
            key="compare_b",
        )

    if st.button("비교하기", type="primary"):
        text_a = history[v1_idx]["content"].splitlines()
        text_b = history[v2_idx]["content"].splitlines()

        differ = difflib.HtmlDiff(wrapcolumn=60)
        diff_html = differ.make_file(
            text_a,
            text_b,
            fromdesc=labels[v1_idx],
            todesc=labels[v2_idx],
            context=True,
            numlines=2,
        )
        components.html(diff_html, height=600, scrolling=True)

    st.markdown("---")
    st.subheader("♻️ 이전 버전으로 복원")

    if len(history) <= 1:
        st.info("복원할 이전 버전이 없습니다.")
    else:
        restore_idx = st.selectbox(
            "복원할 버전을 선택하세요",
            options=list(range(len(history) - 1)),
            format_func=lambda i: labels[i],
            key="restore_select",
        )
        if st.button("선택한 버전으로 복원", type="secondary"):
            target = history[restore_idx]
            new_version = next_minor_version(latest["version"])
            new_entry = {
                "version": new_version,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "editor": "복원",
                "reason": f"v{target['version']} 버전 내용으로 복원",
                "content": target["content"],
            }
            history.append(new_entry)
            save_history(history)
            st.success(f"v{target['version']} 내용을 기반으로 v{new_version} 버전이 생성되었습니다.")
            st.rerun()
