import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import altair as alt

# ==========================================
# 0. 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="강릉샌드 생산일지", page_icon="🍪")
st.title("🍪 쿠키 생산일지")

# ==========================================
# 1. 구글 시트 연결
# ==========================================
try:
    gcp_json_str = st.secrets["GCP_JSON"]
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(gcp_json_str), scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('강릉샌드 생산일지')
except Exception as e:
    st.error(f"구글 시트 연결 에러 원인: {e}")
    st.stop()

# ==========================================
# 2. 직원 입력 화면
# ==========================================
st.subheader("📝 횟수 입력하기")

name = st.selectbox("직원 이름", ["정환", "소정", "가영"])
time_type = st.radio("입력 시간", ["오전 (점심 전)", "오후 (퇴근 전)"])
count = st.number_input("기계 횟수", min_value=0, step=1)

if time_type == "오후 (퇴근 전)":
    boxes = st.number_input("총 쿠키 통 수", min_value=0, step=1)
else:
    boxes = 0

if st.button("제출하기"):
    tz = pytz.timezone('Asia/Seoul')
    today_date = datetime.now(tz).strftime("%Y-%m-%d")

    try:
        user_sheet = spreadsheet.worksheet(name)
        user_sheet.append_row([today_date, name, time_type, count, boxes])
        st.success(f"✅ {name}님, 개인 탭에 {today_date} 기록 완료! (현재 횟수: {count})")
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"🚨 구글 시트 맨 아래에 '{name}' 탭이 없어. 탭 이름을 다시 확인해 줘.")

st.write("---")

# ==========================================
# 3. 월간 생산량 (이번 달 기준)
# ==========================================
tz = pytz.timezone('Asia/Seoul')
today = datetime.now(tz)
current_month_str = today.strftime("%Y-%m")

st.subheader(f"🏆 월간 생산량 ({today.month}월 기준)")

all_data = []
for emp in ["정환", "소정", "가영"]:
    try:
        records = spreadsheet.worksheet(emp).get_all_records()
        all_data.extend(records)
    except:
        pass

df = pd.DataFrame(all_data)

if not df.empty:
    month_df = df[df['날짜'].astype(str).str.startswith(current_month_str)].copy()
    
    if not month_df.empty:
        # 날짜에서 '숫자(일)'만 정수로 추출
        month_df['일(Day)'] = pd.to_datetime(month_df['날짜']).dt.day
        
        # 오후 기록(하루 최대 횟수)을 그날의 최종 실적으로 계산
        daily_max = month_df.groupby(['일(Day)', '이름'])['횟수'].max().reset_index()
        
        # 이번 달 총합 계산
        monthly_total = daily_max.groupby('이름')['횟수'].sum().reset_index()
        monthly_total = monthly_total.sort_values(by="횟수", ascending=False).reset_index(drop=True)
        monthly_total.index = monthly_total.index + 1
        
        st.markdown(f"**👑 {today.month}월 총 누적 횟수**")
        st.dataframe(monthly_total, use_container_width=True)
        
        st.markdown(f"**📈 {today.month}월 일별 횟수 변화**")
        
        # 기본 차트 대신 Altair 라이브러리를 써서 29.00000 소수점 제거 & 세로 눕기 방지!
        chart = alt.Chart(daily_max).mark_line(point=True).encode(
            x=alt.X('일(Day):O', axis=alt.Axis(labelAngle=0, title='날짜 (일)')),
            y=alt.Y('횟수:Q', title='기계 횟수'),
            color=alt.Color('이름:N', title='직원')
        ).properties(height=400)
        
        st.altair_chart(chart, use_container_width=True)
        
    else:
        st.info(f"{today.month}월에 입력된 데이터가 없어!")
else:
    st.info("아직 입력된 데이터가 없어!")
