import streamlit as st
import json
import os
import html
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
    f"1) '{INITIAL_POLICY_PATH}' 파일에 개인정보처리방침 전문을 붙여넣은 뒤 앱을 다시 실행하거나,\n"
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


def build_html_export(entry: dict) -> str:
    """버전 정보를 사람이 읽기 좋은 단일 HTML 문서로 변환한다."""
    escaped_content = html.escape(entry["content"])
    # 문단 구분을 위해 빈 줄 기준으로 <p> 처리, 줄바꿈은 <br>
    paragraphs = escaped_content.split("\n\n")
    body_html = "".join(
        f"<p>{p.replace(chr(10), '<br>')}</p>" for p in paragraphs if p.strip()
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8" />
<title>개인정보처리방침 v{html.escape(entry['version'])}</title>
<style>
  body {{
    font-family: -apple-system, "Malgun Gothic", "Apple SD Gothic Neo", sans-serif;
    max-width: 860px;
    margin: 40px auto;
    padding: 0 24px;
    line-height: 1.7;
    color: #1a1a1a;
  }}
  h1 {{ font-size: 24px; margin-bottom: 4px; }}
  .meta {{ color: #666; font-size: 14px; margin-bottom: 32px; }}
  .meta span {{ margin-right: 16px; }}
  p {{ margin: 0 0 14px 0; white-space: pre-wrap; }}
  hr {{ border: none; border-top: 1px solid #e0e0e0; margin: 24px 0; }}
</style>
</head>
<body>
  <h1>개인정보처리방침 (v{html.escape(entry['version'])})</h1>
  <div class="meta">
    <span>발행일: {html.escape(entry['date'])}</span>
    <span>작성자: {html.escape(entry['editor'])}</span>
    <span>개정 사유: {html.escape(entry['reason'])}</span>
  </div>
  <hr>
  {body_html}
</body>
</html>
"""


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
        "1. 개인정보처리방침 전문 보기",
        "2. 개인정보 처리방침 수정",
        "3. 개인정보 처리방침 이력관리",
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
# 1. 개인정보처리방침 전문 보기
# ----------------------------------------------------------------------------
if menu.startswith("1"):
    st.title("📄 개인정보처리방침 전문 보기")

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
# 2. 개인정보 처리방침 수정
# ----------------------------------------------------------------------------
elif menu.startswith("2"):
    st.title("✏️ 개인정보 처리방침 수정")
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
            st.session_state["just_saved_version"] = new_version
            st.success(f"v{new_version} 버전으로 저장되었습니다. 아래에서 HTML로 다운로드할 수 있습니다.")
            st.rerun()

    # 방금 저장한 버전이 있으면 HTML 다운로드 버튼을 보여준다 (폼 바깥, rerun 이후에도 유지)
    just_saved = st.session_state.get("just_saved_version")
    if just_saved:
        saved_entry = next((h for h in history if h["version"] == just_saved), None)
        if saved_entry:
            st.markdown("---")
            st.subheader(f"📥 방금 저장한 v{just_saved} 버전 다운로드")
            html_doc = build_html_export(saved_entry)
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                st.download_button(
                    "⬇️ HTML 파일로 다운로드",
                    data=html_doc,
                    file_name=f"privacy_policy_v{just_saved}.html",
                    mime="text/html",
                    use_container_width=True,
                )
            with dl_col2:
                st.download_button(
                    "⬇️ 텍스트 파일로 다운로드",
                    data=saved_entry["content"],
                    file_name=f"privacy_policy_v{just_saved}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

    st.markdown("---")
    st.subheader("📥 임의 버전 HTML 다운로드")
    st.caption("최신 버전뿐 아니라 이력에 있는 어떤 버전이든 HTML로 내려받을 수 있습니다.")
    export_labels = [f"v{h['version']} ({h['date']})" for h in history]
    export_idx = st.selectbox(
        "다운로드할 버전 선택",
        options=list(range(len(history))),
        format_func=lambda i: export_labels[i],
        index=len(history) - 1,
        key="export_select",
    )
    export_entry = history[export_idx]
    st.download_button(
        f"⬇️ v{export_entry['version']} HTML 다운로드",
        data=build_html_export(export_entry),
        file_name=f"privacy_policy_v{export_entry['version']}.html",
        mime="text/html",
    )

# ----------------------------------------------------------------------------
# 3. 개인정보 처리방침 이력관리
# ----------------------------------------------------------------------------
else:
    st.title("🗂️ 개인정보 처리방침 이력관리")

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
