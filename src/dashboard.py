from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from collections import Counter
import re
import streamlit as st
import duckdb
import pandas as pd
import altair as alt

# 1. ตั้งค่าหน้าเพจ
st.set_page_config(page_title="Steam Big Data Dashboard", layout="wide", page_icon="🎮")
st.title("📊 Steam Reviews Big Data Dashboard")
st.markdown("วิเคราะห์เจาะลึกข้อมูลรีวิวเกมแบบ Real-time ด้วย DuckDB (Memory Optimized)")

# Dictionary แปลงรหัส AppID เป็นชื่อเกม
GAME_NAMES = {
    # --- รายชื่อเดิม (Multipurpose Classics) ---
    "730": "Counter-Strike 2", "570": "Dota 2", "550": "Left 4 Dead 2",
    "440": "Team Fortress 2", "578080": "PUBG: BATTLEGROUNDS",
    "271590": "Grand Theft Auto V", "105600": "Terraria",
    "4000": "Garry's Mod", "252490": "Rust", "218620": "PAYDAY 2",
    "304930": "Unturned", "230410": "Warframe", "291550": "Brawlhalla",
    "381210": "Dead by Daylight", "236390": "War Thunder",
    "252950": "Rocket League", "292030": "The Witcher 3: Wild Hunt",
    "359550": "Tom Clancy's Rainbow Six Siege", "1086940": "Baldur's Gate 3",
    "1145360": "Hades", "1174180": "Red Dead Redemption 2",
    "433850": "Z1 Battle Royale", "444090": "Paladins", "346110": "ARK: Survival Evolved",
    "72850": "The Elder Scrolls V: Skyrim", "377160": "Fallout 4", "990080": "Hogwarts Legacy",
    "2357570": "Overwatch 2", "1938090": "Call of Duty", "1326470": "Sons Of The Forest",
    "1172470": "Apex Legends", "1716740": "Starfield", "1245620": "ELDEN RING",
    "1599340": "Lost Ark", "1794680": "Vampire Survivors", "1063730": "New World",
    "739630": "Phasmophobia", "1091500": "Cyberpunk 2077", "1097150": "Fall Guys",
    "945360": "Among Us", "1085660": "Destiny 2", "698780": "Doki Doki Literature Club!",
    "275850": "No Man's Sky","435140": "Dishonored 2","402840": "Resident Evil 0","377350": "CRSED: F.O.A.D. (Cuisine Royale)",
    "1175730": "Tomb Raider IV: The Last Revelation","215120": "LEGO The Lord of the Rings",
    "458750": "Total War: WARHAMMER","290730": "Death Road to Canada","1011510": "The Legend of Heroes: Trails from Zero",
    "466170": "Resident Evil 5","661960": "Gumballs & Dungeons","718350": "Total War: WARHAMMER II",
    "723330": "The Sims™ 4","40000": "Vampire: The Masquerade - Bloodlines","377710": "Dungeon of the Endless",
    "910370": "Darksiders III","38000": "Gothic 1","313830": "Crea","663090": "A Way Out","662470": "AeternoBlade II","320000": "Dying Light",
    "612050": "GWENT: The Witcher Card Game","260020": "Crawl","874400": "RimWorld","961990": "The Sims™ 4 (Edition Upgrade)",
    "251610": "Barbie™ Dreamhouse Party™","310970": "Barony","326990": "Barony (Legacy)","347060": "Barony (Retail)",
    "502570": "The Surge", "930320": "The Surge (DLC)", "526800": "The Surge (Complete Edition)",
    "840160": "The Surge 2 (Wait/Related)", "42710": "Call of Duty: Black Ops", "241790": "Dishonored",
    "621300": "AeternoBlade", "37340": "Gothic 3", "748480": "AeternoBlade II: Director's Ring",
    "666790": "A Way Out (Trial)", "468070": "Barony (Soundtrack/DLC)", "547900": "A Way Out (Related ID)",
    "524660": "A Way Out (Origin Connection)", "294710": "The Sims™ 4 (Standard)", "39210": "FINAL FANTASY XIV Online",
    "257650": "The Sims™ 4 (DLC)", "338590": "The Sims™ 4 (Digital Deluxe)", "340990": "The Sims™ 4 (Legacy Edition)",
    "294690": "The Sims™ 4 (Base)", "406030": "The Sims™ 4 (Expansion)", "248170": "The Sims™ 4 (Pack)",
    "399610": "The Sims™ 4 (Free Trial)", "236850": "The Sims™ 4 (Origin)", "8500": "EVE Online",
    "244830": "Space Engineers", "205270": "3DMark 11", "874700": "The Putinland: Divide & Conquer",
    "625630": "Journey of Johann", "12540": "Mahjongg Investigations: Under Suspicion", "807920": "Onii-Chan",
    "1427540": "Attack from Planet Smiley", "1912760": "The Hentai Memory", "406220": "Gnomes Vs. Fairies",
    "202351": "Steam Community Beta Access", "824300": "Dragon Awaken", "32110": "Luxor Mahjong",
    "325110": "Save the Furries", "1051500": "Digital Diamond Baseball V8", "277250": "MAGIX Samplitude Music Studio 2014",
    "216610": "Football Manager 2013", "592340": "Mall Empire", "344340": "Front Office Football Seven",
    "1385920": "Impossible Pixels", "1753490": "Dachengzhu Strategic Edition (大城主战略版)", "60340": "LUXOR: 5th Passage"
}

# 2. Sidebar Filters (💡 เพิ่มตัวเลือก "ทุกปี")
st.sidebar.header("🔍 Filters")
years_list = ["ทุกปี", 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015]
selected_year = st.sidebar.selectbox("📅 เลือกปีที่ต้องการวิเคราะห์:", years_list)

# 3. เตรียมฟังก์ชันดึงข้อมูลจาก Parquet
@st.cache_data(show_spinner=False)
def get_dashboard_data(year):
    con = duckdb.connect(database=':memory:')
    con.execute("PRAGMA memory_limit='10GB'")
    base_path = "data/parquet/**/*.parquet"
    
    # 💡 จัดการเงื่อนไข WHERE clause แบบไดนามิก
    if year == "ทุกปี":
        where_clause = ""
        year_str = "ทุกปี"
    else:
        where_clause = f"WHERE EXTRACT(YEAR FROM CAST(timestamp_created AS TIMESTAMP)) = {year}"
        year_str = f"ปี {year}"
        
    data = {}
    try:
        # 💡 Query ใหม่สำหรับทำ Scorecard
        data['summary'] = con.execute(f"""
            SELECT 
                COUNT(*) as total_reviews,
                SUM(CASE WHEN voted_up = True THEN 1 ELSE 0 END) as positive_reviews,
                COUNT(DISTINCT appid) as total_games,
                AVG(CAST(author_playtime_forever AS DOUBLE)) / 60.0 as avg_playtime
            FROM read_parquet('{base_path}')
            {where_clause}
        """).df()

        data['top10'] = con.execute(f"""
            SELECT appid, COUNT(*) as total_reviews,
                   SUM(CASE WHEN voted_up = True THEN 1 ELSE 0 END) as positive,
                   SUM(CASE WHEN voted_up = False THEN 1 ELSE 0 END) as negative
            FROM read_parquet('{base_path}') 
            {where_clause}
            GROUP BY 1 ORDER BY 2 DESC LIMIT 10
        """).df()

        data['playtime'] = con.execute(f"""
            SELECT 
                CASE WHEN voted_up = True THEN 'แนะนำ (Positive)' ELSE 'ไม่แนะนำ (Negative)' END as Sentiment,
                AVG(CAST(author_playtime_forever AS DOUBLE)) / 60.0 as avg_playtime_hours
            FROM read_parquet('{base_path}')
            {where_clause}
            GROUP BY 1
        """).df()

        data['languages'] = con.execute(f"""
            SELECT language, COUNT(*) as count
            FROM read_parquet('{base_path}')
            {where_clause}
            GROUP BY 1 ORDER BY 2 DESC LIMIT 10
        """).df()

        data['trend'] = con.execute(f"""
            SELECT EXTRACT(MONTH FROM CAST(timestamp_created AS TIMESTAMP)) as month,
                   SUM(CASE WHEN voted_up = True THEN 1 ELSE 0 END) as positive,
                   SUM(CASE WHEN voted_up = False THEN 1 ELSE 0 END) as negative
            FROM read_parquet('{base_path}')
            {where_clause}
            GROUP BY 1 ORDER BY 1
        """).df()

        data['purchase'] = con.execute(f"""
            SELECT 
                CASE WHEN steam_purchase = True THEN 'ซื้อผ่าน Steam' ELSE 'ช่องทางอื่น/คีย์' END as source,
                COUNT(*) as count
            FROM read_parquet('{base_path}')
            {where_clause}
            GROUP BY 1
        """).df()

        data['early_access'] = con.execute(f"""
            SELECT 
                CASE WHEN written_during_early_access = True THEN 'ช่วง Early Access' ELSE 'หลังวางจำหน่ายจริง' END as status,
                COUNT(*) as count
            FROM read_parquet('{base_path}')
            {where_clause}
            GROUP BY 1
        """).df()

        data['lang_sentiment'] = con.execute(f"""
            SELECT language, 
                   AVG(CASE WHEN voted_up = True THEN 1.0 ELSE 0.0 END) * 100 as pos_rate,
                   COUNT(*) as review_count
            FROM read_parquet('{base_path}')
            {where_clause}
            GROUP BY 1 
            HAVING review_count > 500
            ORDER BY pos_rate DESC
            LIMIT 10
        """).df()

        data['engagement'] = con.execute(f"""
            SELECT appid, 
                   AVG(CAST(author_playtime_forever AS DOUBLE)) / 60.0 as avg_hours
            FROM read_parquet('{base_path}')
            {where_clause}
            GROUP BY 1 ORDER BY avg_hours DESC LIMIT 10
        """).df()

        # Query 9: สุ่ม Text รีวิวมาทำ Word Cloud (ใช้ USING SAMPLE ป้องกันแรมเต็ม)
        # กรองเฉพาะรีวิวภาษาอังกฤษก่อน เพื่อให้คำตัดง่ายและสวยงาม
        data['wordcloud'] = con.execute(f"""
            SELECT review
            FROM read_parquet('{base_path}')
            {where_clause}
            { "AND" if where_clause else "WHERE" } language = 'english' AND review IS NOT NULL
            USING SAMPLE 5000 ROWS
        """).df()
        
    except Exception as e:
        st.error(f"🚨 พบข้อผิดพลาด: {e}")
    return data

# แสดงข้อความ Loading ให้เข้ากับเงื่อนไข
loading_msg = f"⏳ กำลังประมวลผล Big Data ของปี {selected_year}..." if selected_year != "ทุกปี" else "⏳ กำลังประมวลผล Big Data ทั้งหมด (ทุกปี)... อาจใช้เวลาสักครู่..."

with st.spinner(loading_msg):
    dash_data = get_dashboard_data(selected_year)

# ดึง DataFrames
df_summary = dash_data.get('summary', pd.DataFrame())
df_top10 = dash_data.get('top10', pd.DataFrame())
df_playtime = dash_data.get('playtime', pd.DataFrame())
df_lang = dash_data.get('languages', pd.DataFrame())
df_trend = dash_data.get('trend', pd.DataFrame())
df_purchase = dash_data.get('purchase', pd.DataFrame())
df_early = dash_data.get('early_access', pd.DataFrame())

# ==========================================
# 🌟 ส่วนที่ 0: SCORECARDS (แสดงด้านบนสุด)
# ==========================================
if not df_summary.empty and df_summary['total_reviews'].fillna(0).iloc[0] > 0:
    st.subheader(f"📌 ภาพรวมข้อมูลรีวิว: {selected_year}")
    
    # 💡 ใช้ .fillna(0) เพื่อป้องกัน Error NaN กรณีที่ปีนั้นไม่มีข้อมูลหรือค่าเป็น NULL
    total_reviews = int(df_summary['total_reviews'].fillna(0).iloc[0])
    total_positive = int(df_summary['positive_reviews'].fillna(0).iloc[0])
    total_games = int(df_summary['total_games'].fillna(0).iloc[0])
    avg_playtime = float(df_summary['avg_playtime'].fillna(0).iloc[0])
    
    # ป้องกันการหารด้วย 0
    percent_positive = (total_positive / total_reviews * 100) if total_reviews > 0 else 0
    
    # วาง Layout คอลัมน์ 4 ช่อง
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📝 จำนวนรีวิวทั้งหมด", f"{total_reviews:,.0f} รายการ")
    col2.metric("👍 อัตราความพึงพอใจ", f"{percent_positive:.1f}%")
    col3.metric("🎮 จำนวนเกมที่ถูกรีวิว", f"{total_games:,.0f} เกม")
    col4.metric("⏳ เวลาเล่นเฉลี่ย", f"{avg_playtime:,.1f} ชม.")
    
    st.divider() # เส้นคั่นก่อนเริ่มกราฟ

# ==========================================
# กราฟและส่วนอื่นๆ ของ Dashboard
# ==========================================
if not df_top10.empty:
    # --- ส่วนที่ 1: TABS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏆 Top 10 Games", "⏱️ Playtime vs Sentiment", "🌍 Global Languages", "📈 Monthly Trends",  "☁️ Word Cloud"])

    with tab1:
        df_top10['Game Name'] = df_top10['appid'].astype(str).map(GAME_NAMES).fillna("AppID: " + df_top10['appid'].astype(str))
        chart_data = df_top10.melt(id_vars='Game Name', value_vars=['positive', 'negative'], var_name='Sentiment', value_name='Count')
        chart = alt.Chart(chart_data).mark_bar().encode(
            y=alt.Y('Sentiment:N', title=None, sort=['positive', 'negative']), 
            x=alt.X('Count:Q', title='จำนวนรีวิว'),
            color=alt.Color('Sentiment:N', scale=alt.Scale(domain=['positive', 'negative'], range=['#4CAF50', '#F44336'])),
            row=alt.Row('Game Name:N', title='รายชื่อเกม', sort=df_top10['Game Name'].tolist(), header=alt.Header(labelAngle=0, labelAlign='left'))
        ).properties(width=700, height=50).configure_axis(labelFontSize=13, titleFontSize=15).configure_header(labelFontSize=14, titleFontSize=15)
        st.altair_chart(chart, use_container_width=True)

    with tab2:
        st.subheader("⏱️ ยิ่งเล่นนาน ยิ่งรัก หรือ ยิ่งเกลียด?")
        playtime_chart = alt.Chart(df_playtime).mark_bar(size=80).encode(
            x=alt.X('Sentiment:N', title='ความพึงพอใจ', sort=['แนะนำ (Positive)', 'ไม่แนะนำ (Negative)'], axis=alt.Axis(labelAngle=0, labelFontSize=16)),
            y=alt.Y('avg_playtime_hours:Q', title='เวลาเล่นเฉลี่ย (ชั่วโมง)', axis=alt.Axis(labelFontSize=16)),
            color=alt.Color('Sentiment:N', scale=alt.Scale(domain=['แนะนำ (Positive)', 'ไม่แนะนำ (Negative)'], range=['#4CAF50', '#F44336']), legend=None)
        ).properties(height=450).configure_axis(labelFontSize=16, titleFontSize=18)
        st.altair_chart(playtime_chart, use_container_width=True)

    with tab3:
        st.subheader("🌍 ภาษาของเกมเมอร์ทั่วโลก")
        lang_chart = alt.Chart(df_lang).mark_bar().encode(
            x=alt.X('count:Q', title='จำนวนรีวิว'),
            y=alt.Y('language:N', title='ภาษา', sort='-x'),
            color=alt.Color('count:Q', scale=alt.Scale(scheme='blues'))
        ).properties(height=450).configure_axis(labelFontSize=14, titleFontSize=16)
        st.altair_chart(lang_chart, use_container_width=True)

    with tab4:
        st.subheader("📈 ฤดูกาลแห่งการรีวิวเกม")
        trend_data = df_trend.melt(id_vars='month', value_vars=['positive', 'negative'], var_name='Sentiment', value_name='Count')
        trend_chart = alt.Chart(trend_data).mark_line(point=True, strokeWidth=4).encode(
            x=alt.X('month:O', title='เดือน (1-12)', axis=alt.Axis(labelAngle=0, labelFontSize=16), scale=alt.Scale(domain=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])),
            y=alt.Y('Count:Q', title='จำนวนรีวิว', axis=alt.Axis(labelFontSize=16)),
            color=alt.Color('Sentiment:N', scale=alt.Scale(domain=['positive', 'negative'], range=['#4CAF50', '#F44336']))
        ).properties(height=450).configure_axis(labelFontSize=16, titleFontSize=18)
        st.altair_chart(trend_chart, use_container_width=True)

    with tab5:
        st.subheader("☁️ เสียงสะท้อนจากเกมเมอร์ (Top Keywords & Word Cloud)")
        st.markdown("วิเคราะห์คำศัพท์ที่ถูกพูดถึงบ่อยที่สุดในรีวิว (สุ่มตัวอย่าง 5,000 รีวิวภาษาอังกฤษ)")
        
        df_wc = dash_data.get('wordcloud', pd.DataFrame())
        
        if not df_wc.empty:
            # 1. นำข้อความทั้งหมดมารวมกันเป็นก้อนเดียว
            raw_text = " ".join(review for review in df_wc['review'].dropna()).lower()
            
            # 2. ทำความสะอาดข้อความ (Clean Text)
            # ตัดเครื่องหมายวรรคตอนและเหลือเฉพาะตัวอักษร a-z
            clean_text = re.sub(r'[^a-z\s]', '', raw_text)
            
            # 3. เตรียม Stopwords แบบเข้มข้นขึ้น (เพิ่มคำทั่วไปที่มักเจอในรีวิวเกมแต่ไม่มีความหมายลึกซึ้ง)
            custom_stopwords = set(STOPWORDS)
            custom_stopwords.update(['game', 'games', 'play', 'playing', 'played', 'time', 'one', 'will', 'even', 'really', 'much', 'still', 'now', 'make'])
            
            # กรองคำที่เป็น Stopwords หรือคำที่สั้นเกินไปออก
            words = [word for word in clean_text.split() if word not in custom_stopwords and len(word) > 2]
            
            # ---------------------------------------------------------
            # ส่วนที่ A: สร้างตารางและกราฟ Top 10 Keywords
            # ---------------------------------------------------------
            # นับความถี่ของคำ
            word_counts = Counter(words)
            df_top_words = pd.DataFrame(word_counts.most_common(10), columns=['Word', 'Count'])
            
            # แบ่ง Layout ซ้าย-ขวา
            col_wc1, col_wc2 = st.columns([1, 1])
            
            with col_wc1:
                st.markdown("##### 📊 10 อันดับคำศัพท์ยอดฮิต")
                
                # พล็อตกราฟแท่งด้วย Altair
                top_words_chart = alt.Chart(df_top_words).mark_bar(color='#2ca02c', size=25).encode(
                    x=alt.X('Count:Q', title='จำนวนครั้งที่พบ', axis=alt.Axis(labelFontSize=14, titleFontSize=15)),
                    y=alt.Y('Word:N', title='คำศัพท์', sort='-x', axis=alt.Axis(labelFontSize=14, titleFontSize=15)),
                    tooltip=['Word', 'Count']
                ).properties(height=400)
                
                st.altair_chart(top_words_chart, use_container_width=True)

            # ---------------------------------------------------------
            # ส่วนที่ B: สร้าง Word Cloud แบบปรับแต่งแล้ว
            # ---------------------------------------------------------
            with col_wc2:
                st.markdown("##### ☁️ ภาพรวม Word Cloud")
                
                # ใช้คำที่ถูกคลีนแล้วมาทำ Word Cloud
                filtered_text = " ".join(words)
                
                wordcloud = WordCloud(
                    width=800, height=500,
                    background_color='#0E1117', 
                    colormap='Set3', # เปลี่ยนชุดสีให้ดูซอฟต์ลง
                    max_words=100,   # ลดจำนวนคำลงเหลือ 100 ให้อ่านง่ายขึ้น
                    contour_width=0
                ).generate(filtered_text)
                
                fig, ax = plt.subplots(figsize=(10, 6), facecolor='#0E1117')
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis("off")
                fig.tight_layout(pad=0)
                
                st.pyplot(fig)
        else:
            st.info("ไม่พบข้อมูล Text สำหรับสร้าง Word Cloud ในเงื่อนไขนี้") 

    # --- ส่วนที่ 2: FOOTER พร้อมเปอร์เซ็นต์บนกราฟโดนัท ---
    st.divider()
    st.subheader("🍩 ข้อมูลสรุปพฤติกรรมการรีวิว (พร้อมสัดส่วนเปอร์เซ็นต์)")
    
    col_footer1, col_footer2 = st.columns(2)
    
    with col_footer1:
        st.markdown("##### 🛒 ที่มาของตัวเกม")
        if not df_purchase.empty:
            df_purchase['pct'] = (df_purchase['count'] / df_purchase['count'].sum() * 100).round(1)
            df_purchase['label'] = df_purchase['pct'].astype(str) + '%'
            
            base = alt.Chart(df_purchase).encode(
                theta=alt.Theta(field="count", type="quantitative"),
                color=alt.Color(field="source", type="nominal", 
                                scale=alt.Scale(range=['#1f77b4', '#aec7e8']),
                                legend=alt.Legend(title="แหล่งที่มา", labelFontSize=14, titleFontSize=15))
            )
            donut = base.mark_arc(innerRadius=70, outerRadius=120)
            text = base.mark_text(radius=155, size=18, fontWeight="bold").encode(text="label:N")
            
            st.altair_chart(donut + text, use_container_width=True)

    with col_footer2:
        st.markdown("##### 🏗️ สถานะการพัฒนาขณะรีวิว")
        if not df_early.empty:
            df_early['pct'] = (df_early['count'] / df_early['count'].sum() * 100).round(1)
            df_early['label'] = df_early['pct'].astype(str) + '%'
            
            base_early = alt.Chart(df_early).encode(
                theta=alt.Theta(field="count", type="quantitative"),
                color=alt.Color(field="status", type="nominal", 
                                scale=alt.Scale(range=['#ff7f0e', '#ffbb78']),
                                legend=alt.Legend(title="สถานะเกม", labelFontSize=14, titleFontSize=15))
            )
            donut_early = base_early.mark_arc(innerRadius=70, outerRadius=120)
            text_early = base_early.mark_text(radius=155, size=18, fontWeight="bold").encode(text="label:N")
            
            st.altair_chart(donut_early + text_early, use_container_width=True)

    st.divider()
    st.subheader("🧐 การวิเคราะห์เชิงลึกเพิ่มเติม (Deep Analysis)")
    col_deep1, col_deep2 = st.columns(2)

    with col_deep1:
        st.markdown("##### 🌍 10 อันดับภาษาที่ให้คะแนนแง่บวกสูงสุด")
        df_lang_sent = dash_data.get('lang_sentiment', pd.DataFrame())
        if not df_lang_sent.empty:
            lang_sent_chart = alt.Chart(df_lang_sent).mark_bar(size=30).encode(
                x=alt.X('pos_rate:Q', 
                        title='เปอร์เซ็นต์แง่บวก (%)', 
                        scale=alt.Scale(domain=[0, 100]),
                        axis=alt.Axis(labelFontSize=14, titleFontSize=16)),
                y=alt.Y('language:N', 
                        title='ภาษา', 
                        sort='-x',
                        axis=alt.Axis(labelFontSize=14, titleFontSize=16)),
                color=alt.Color('language:N', 
                                title='ภาษา', 
                                legend=alt.Legend(labelFontSize=14, titleFontSize=15)),
                tooltip=[alt.Tooltip('pos_rate', format='.1f', title='แง่บวก %'), 'review_count']
            ).properties(height=450)
            
            st.altair_chart(lang_sent_chart, use_container_width=True)

    with col_deep2:
        st.markdown("##### 🎮 เกมที่ครองเวลาผู้เล่นนานที่สุด (Average Engagement)")
        df_engage = dash_data.get('engagement', pd.DataFrame())
        if not df_engage.empty:
            df_engage['Game Name'] = df_engage['appid'].astype(str).map(GAME_NAMES).fillna("AppID: " + df_engage['appid'].astype(str))
            
            engage_chart = alt.Chart(df_engage).mark_bar(color='#9467bd', size=30).encode(
                x=alt.X('avg_hours:Q', 
                        title='เวลาเล่นเฉลี่ย (ชั่วโมง)',
                        axis=alt.Axis(labelFontSize=14, titleFontSize=16)),
                y=alt.Y('Game Name:N', 
                        title=None, 
                        sort='-x',
                        axis=alt.Axis(labelFontSize=13)),
                tooltip=[alt.Tooltip('avg_hours', format='.1f', title='ชั่วโมงเฉลี่ย')]
            ).properties(height=450)
            
            st.altair_chart(engage_chart, use_container_width=True)

else:
    st.warning("⚠️ ไม่มีข้อมูลสำหรับเงื่อนไขที่เลือก")