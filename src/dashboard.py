"""

Dashboard Interaktif untuk Analisis Hasil Retrieval

====================================================

Cara menjalankan:

    streamlit run src/dashboard.py



Fitur:

- Light/Dark mode toggle untuk laporan skripsi

- Export visualisasi untuk dimasukkan ke laporan



Pastikan berada di root directory project.

"""



import streamlit as st

import pandas as pd

import plotly.express as px

import plotly.graph_objects as go

from plotly.subplots import make_subplots

import os



# ============================================================================

# THEME CONFIGURATION

# ============================================================================

def configure_theme():

    """Configure theme settings for the dashboard"""

    # Get current theme from session state or default to light

    if 'theme' not in st.session_state:

        st.session_state.theme = 'light'

    

    return st.session_state.theme



def get_theme_colors(theme):

    """Get color scheme based on theme"""

    if theme == 'light':

        return {

            'bg_color': '#FFFFFF',

            'text_color': '#333333',

            'grid_color': '#E5E5E5',

            'plot_bg': '#FAFAFA',

            'primary': '#2E86AB',

            'secondary': '#A23B72',

            'success': '#28A745',

            'warning': '#FFC107',

            'danger': '#DC3545',

            'font': 'Arial, sans-serif'

        }

    else:

        return {

            'bg_color': '#0E1117',

            'text_color': '#FAFAFA',

            'grid_color': '#333333',

            'plot_bg': '#1E1E1E',

            'primary': '#4dabf7',

            'secondary': '#ff6b6b',

            'success': '#51cf66',

            'warning': '#ffd43b',

            'danger': '#ff6b6b',

            'font': 'Arial, sans-serif'

        }



# ============================================================================

# KONFIGURASI PAGE

# ============================================================================

st.set_page_config(

    page_title="CLIR Analysis Dashboard",

    page_icon="📊",

    layout="wide",

    initial_sidebar_state="expanded"

)



# ============================================================================

# FUNGSI LOAD DATA

# ============================================================================

@st.cache_data

def load_data():

    """Load dan proses semua data"""

    # Load queries

    queries_file = 'data/queries/queries_indo.csv'

    df_queries = pd.read_csv(queries_file)

    

    # Load Arabic queries (NMT vs LLM)

    arab_file = 'data/queries/queries_arab.csv'

    df_arab = pd.read_csv(arab_file) if os.path.exists(arab_file) else None

    

    # Load qrels (query-doc relevance judgments)

    qrels_file = 'data/queries/qrels.csv'

    df_qrels = pd.read_csv(qrels_file) if os.path.exists(qrels_file) else None

    

    # Load corpus

    corpus_file = 'data/raw/fathul_muin.csv'

    df_corpus = pd.read_csv(corpus_file) if os.path.exists(corpus_file) else None

    

    # Load detail results

    PATH = 'data/results/'

    file_detail = [

        PATH + 'skenario1_detail_per_kueri_nmt_vs_llm.csv',

        PATH + 'skenario2_distilbert_detail_per_kueri.csv',

        PATH + 'skenario2_mmbert-small_detail_per_kueri.csv',

        PATH + 'skenario2_mmbert-base_detail_per_kueri.csv',

        PATH + 'skenario3_detail_per_kueri_nmt_vs_llm.csv'

    ]

    

    # Load overall results (MRR & Success@k)

    file_overall = [

        PATH + 'skenario1_overall_nmt_vs_llm.csv',

        PATH + 'skenario2_distilbert_evaluasi_overall.csv',

        PATH + 'skenario2_mmbert-small_evaluasi_overall.csv',

        PATH + 'skenario2_mmbert-base_evaluasi_overall.csv',

        PATH + 'skenario3_overall_nmt_vs_llm.csv'

    ]

    

    def gabung_csv(list_file, is_overall=False):

        df_list = []

        for file in list_file:

            if os.path.exists(file):

                df = pd.read_csv(file)

                if 'skenario1' in file:

                    df.insert(0, 'Skenario', '1. BM25 (Sparse)')

                elif 'skenario2' in file:

                    df.insert(0, 'Skenario', '2. Cross-Lingual (Dense)')

                elif 'skenario3' in file:

                    df.insert(0, 'Skenario', '3. AraDPR (Monolingual)')

                df_list.append(df)

        return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()

    

    df_detail = gabung_csv(file_detail)

    df_overall = gabung_csv(file_overall, is_overall=True)

    

    # Convert Hit@10 to numeric

    df_detail['Hit@10_numeric'] = df_detail['Hit@10'].map({'✅ Hit': 1, '❌ Miss': 0})

    

    # Pivot untuk analisis

    detail_pivot = df_detail.pivot_table(

        index='qid',

        columns='name',

        values='Hit@10_numeric',

        aggfunc='first'

    ).reset_index()

    

    # Merge dengan queries

    result = df_queries[['qid', 'query', 'query_type']].merge(

        detail_pivot, on='qid', how='left'

    )

    

    # Get model names

    model_names = [c for c in result.columns if c not in ['qid', 'query', 'query_type']]

    

    # Hit count per query

    result['hit_count'] = result[model_names].sum(axis=1)

    

    return result, model_names, df_queries, df_detail, df_overall, df_arab, df_qrels, df_corpus



# ============================================================================

# FUNGSI ANALISIS

# ============================================================================

def find_unique_to_model(target_model, result_df, model_cols):

    """Query yang HANYA ditemukan oleh target_model"""

    if target_model not in model_cols:

        return None

    other_models = [m for m in model_cols if m != target_model]

    condition = (result_df[target_model] == 1)

    for m in other_models:

        condition = condition & (result_df[m] == 0)

    return result_df[condition]



def find_queries_all_models_hit(result_df, model_cols):

    """Query yang ditemukan oleh SEMUA model"""

    condition = (result_df[model_cols[0]] == 1)

    for m in model_cols[1:]:

        condition = condition & (result_df[m] == 1)

    return result_df[condition]



def find_queries_all_models_miss(result_df, model_cols):

    """Query yang TIDAK ditemukan oleh SEMUA model"""

    condition = (result_df[model_cols[0]] == 0)

    for m in model_cols[1:]:

        condition = condition & (result_df[m] == 0)

    return result_df[condition]



def compare_two_models(model_a, model_b, result_df, model_cols, mode='a_not_b'):

    """

    Compare two models with different modes:

    - 'a_not_b': Query yang ditemukan Model A tapi TIDAK oleh Model B

    - 'b_not_a': Query yang gagal di Model A tapi berhasil di Model B

    - 'both': Query yang sama-sama berhasil di kedua model

    - 'neither': Query yang sama-sama gagal di kedua model

    """

    if mode == 'a_not_b':

        # A berhasil, B gagal

        condition = (result_df[model_a] == 1) & (result_df[model_b] == 0)

    elif mode == 'b_not_a':

        # A gagal, B berhasil

        condition = (result_df[model_a] == 0) & (result_df[model_b] == 1)

    elif mode == 'both':

        # Keduanya berhasil

        condition = (result_df[model_a] == 1) & (result_df[model_b] == 1)

    elif mode == 'neither':

        # Keduanya gagal

        condition = (result_df[model_a] == 0) & (result_df[model_b] == 0)

    else:

        condition = (result_df[model_a] == 1) & (result_df[model_b] == 0)

    return result_df[condition]



def hit_rate_summary(result_df, model_cols):

    """Summary hit rate untuk setiap model"""

    summary = []

    for m in model_cols:

        hits = result_df[m].sum()

        total = len(result_df)

        rate = (hits / total) * 100

        summary.append({

            'Model': m, 

            'Hits': int(hits), 

            'Total': total, 

            'Hit Rate (%)': round(rate, 2)

        })

    return pd.DataFrame(summary).sort_values('Hit Rate (%)', ascending=False)



def hit_rate_by_query_type(result_df, model_cols):

    """Hit rate per model per query type"""

    summary = []

    for qtype in sorted(result_df['query_type'].unique()):

        subset = result_df[result_df['query_type'] == qtype]

        for m in model_cols:

            hits = subset[m].sum()

            total = len(subset)

            rate = (hits / total) * 100

            summary.append({

                'Query Type': f"Tipe {int(qtype)}",

                'Model': m,

                'Hit Rate (%)': round(rate, 2)

            })

    return pd.DataFrame(summary)



# ============================================================================

# HELPER FUNCTIONS

# ============================================================================

import pyperclip



def copy_to_clipboard(text, success_msg="Copied to clipboard!"):

    """Copy text to clipboard using pyperclip"""

    try:

        pyperclip.copy(text)

        return True

    except Exception as e:

        st.error(f"Failed to copy: {e}")

        return False



def copy_button_simple(text, button_text="📋 Copy", success_msg="Copied!", key=None):

    """Create a simple copy button that actually works with Arabic text"""

    if key is None:

        import hashlib

        key = f"copy_{hashlib.md5(str(text).encode()).hexdigest()[:8]}"

    

    if st.button(button_text, key=key):

        if copy_to_clipboard(text):

            st.success(success_msg)

            return True

    return False



def display_copyable_text(text, label=None, height=200, key_prefix="text"):

    """Display text in a text area with a working copy button"""

    import hashlib

    

    if label:

        st.markdown(f"**{label}**")

    

    # Create unique key

    unique_key = f"{key_prefix}_{hashlib.md5(str(text).encode()).hexdigest()[:8]}"

    

    # Display in text area for easy selection

    st.text_area(

        label=f"_{unique_key}_label",

        value=text,

        height=height,

        label_visibility="collapsed",

        key=unique_key

    )

    

    # Copy button

    col1, col2 = st.columns([1, 10])

    with col1:

        copy_button_simple(text, "📋", f"Copied {len(text)} chars!", key=f"{unique_key}_btn")



# ============================================================================

# PLOT THEME FUNCTIONS

# ============================================================================

def apply_plot_theme(fig, theme_colors, title=None):

    """Apply theme to plotly figure"""

    fig.update_layout(

        plot_bgcolor=theme_colors['plot_bg'],

        paper_bgcolor=theme_colors['bg_color'],

        font=dict(color=theme_colors['text_color'], family=theme_colors['font']),

        title=dict(text=title, font=dict(color=theme_colors['text_color'], size=16)) if title else None,

        xaxis=dict(

            gridcolor=theme_colors['grid_color'],

            zerolinecolor=theme_colors['grid_color'],

            tickfont=dict(color=theme_colors['text_color'])

        ),

        yaxis=dict(

            gridcolor=theme_colors['grid_color'],

            zerolinecolor=theme_colors['grid_color'],

            tickfont=dict(color=theme_colors['text_color'])

        ),

        legend=dict(font=dict(color=theme_colors['text_color']))

    )

    return fig



# ============================================================================

# MAIN APP

# ============================================================================

def main():

    # Theme Configuration

    theme = configure_theme()

    colors = get_theme_colors(theme)

    

    # Sidebar

    st.sidebar.header("🎨 Pengaturan Tampilan")

    

    # Theme Toggle

    theme_option = st.sidebar.radio(

        "Pilih Tema:",

        ["☀️ Light Mode", "🌙 Dark Mode"],

        index=0 if theme == 'light' else 1

    )

    

    # Update theme in session state

    new_theme = 'light' if theme_option == "☀️ Light Mode" else 'dark'

    if new_theme != st.session_state.theme:

        st.session_state.theme = new_theme

        st.rerun()

    

    colors = get_theme_colors(st.session_state.theme)

    

    # Export Options

    st.sidebar.markdown("---")

    st.sidebar.header("📥 Export untuk Laporan")

    

    export_format = st.sidebar.selectbox(

        "Format Export:",

        ["PNG (High Res)", "SVG (Vector)", "PDF"]

    )

    

    st.sidebar.info("💡 Tip: Gunakan Light Mode untuk laporan skripsi agar terlihat lebih profesional.")

    

    # Title

    st.title("📊 Dashboard Analisis CLIR")

    st.caption("Cross-Lingual Information Retrieval - Analysis Dashboard")

    st.markdown("---")

    

    # Load data

    with st.spinner("Memuat data..."):

        result, model_names, df_queries, df_detail, df_overall, df_arab, df_qrels, df_corpus = load_data()

    

    # Navigation

    st.sidebar.header("🔧 Navigasi")

    page = st.sidebar.radio(

        "Pilih Analisis:",

        ["📈 Overview", "🏆 Perbandingan Model", "🔍 Analisis Query", "📊 Metrik Lengkap (MRR & Success@k)", "🌍 Query Bahasa Arab", "📈 Visualisasi Lanjutan"]

    )

    

    # =======================================================================

    # PAGE 1: OVERVIEW

    # =======================================================================

    if page == "📈 Overview":

        st.header("📈 Overview Performa Model")

        

        # Metrics

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric("Total Query", len(result))

        with col2:

            st.metric("Total Model", len(model_names))

        with col3:

            all_hit_count = len(find_queries_all_models_hit(result, model_names))

            st.metric("Query Ditemukan Semua Model", all_hit_count)

        with col4:

            all_miss_count = len(find_queries_all_models_miss(result, model_names))

            st.metric("Query Gagal Semua Model", all_miss_count)

        

        st.markdown("---")

        

        # Hit Rate Summary Table

        st.subheader("🏆 Ranking Model (Hit Rate)")

        summary_df = hit_rate_summary(result, model_names)

        summary_df['Rank'] = range(1, len(summary_df) + 1)

        summary_df = summary_df[['Rank', 'Model', 'Hits', 'Hit Rate (%)']]

        

        # Color coding for light mode

        def highlight_top3(val):

            if isinstance(val, (int, float)):

                if val >= 50:

                    return 'background-color: #90EE90; color: black'

                elif val >= 30:

                    return 'background-color: #FFD700; color: black'

            return ''

        

        styled_summary = summary_df.style.applymap(highlight_top3, subset=['Hit Rate (%)'])

        st.dataframe(styled_summary, use_container_width=True)

        

        # Bar Chart

        st.subheader("📊 Visualisasi Hit Rate")

        fig = px.bar(

            summary_df, 

            x='Hit Rate (%)', 

            y='Model', 

            orientation='h',

            color='Hit Rate (%)',

            color_continuous_scale='Viridis',

            text='Hit Rate (%)'

        )

        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')

        fig = apply_plot_theme(fig, colors, "Performa Model berdasarkan Hit Rate @10")

        fig.update_layout(yaxis={'categoryorder': 'total ascending'})

        st.plotly_chart(fig, use_container_width=True)

        

        # Export button

        if st.button("💾 Simpan Grafik untuk Laporan"):

            fig.write_image("hit_rate_overview.png", width=1200, height=800, scale=2)

            st.success("✅ Grafik disimpan sebagai 'hit_rate_overview.png'")

    

    # =======================================================================

    # PAGE 2: PERBANDINGAN MODEL

    # =======================================================================

    elif page == "🏆 Perbandingan Model":

        st.header("🏆 Perbandingan Antar Model")

        

        col1, col2 = st.columns(2)

        

        with col1:

            st.subheader("📌 Model A")

            model_a = st.selectbox("Pilih Model A:", model_names, key="model_a")

        

        with col2:

            st.subheader("📌 Model B")

            model_b = st.selectbox("Pilih Model B:", model_names, index=1, key="model_b")

        

        if model_a == model_b:

            st.warning("⚠️ Model A dan Model B harus berbeda!")

        else:

            st.markdown("---")

            

            # Create tabs for different comparison types

            tab1, tab2, tab3, tab4 = st.tabs([

                "✅ A Berhasil, B Gagal", 

                "❌ A Gagal, B Berhasil", 

                "✅✅ Keduanya Berhasil",

                "❌❌ Keduanya Gagal"

            ])

            

            # TAB 1: A berhasil, B gagal

            with tab1:

                comparison_df = compare_two_models(model_a, model_b, result, model_names, mode='a_not_b')

                

                st.subheader(f"🔍 Query yang ditemukan '{model_a}' tapi TIDAK oleh '{model_b}'")

                col_m1, col_m2, col_m3 = st.columns(3)

                with col_m1:

                    st.metric("Jumlah Query", len(comparison_df))

                with col_m2:

                    st.metric(f"Hit Rate {model_a[:20]}...", f"{result[model_a].sum()} hits")

                with col_m3:

                    a_success = result[model_a].sum()

                    b_success = result[model_b].sum()

                    advantage = len(comparison_df)

                    st.metric("Keunggulan A", f"{advantage} query")

                

                if len(comparison_df) > 0:

                    display_cols = ['qid', 'query_type', 'query', model_a, model_b]

                    st.dataframe(comparison_df[display_cols], use_container_width=True)

                    

                    # Breakdown by query type

                    st.subheader("📊 Breakdown per Tipe Query")

                    type_breakdown = comparison_df['query_type'].value_counts().sort_index()

                    

                    fig = px.pie(

                        values=type_breakdown.values, 

                        names=[f"Tipe {int(x)}" for x in type_breakdown.index],

                        title=f"Distribusi Tipe Query - Keunggulan {model_a[:30]}",

                        color_discrete_sequence=px.colors.qualitative.Set3

                    )

                    fig = apply_plot_theme(fig, colors)

                    st.plotly_chart(fig, use_container_width=True)

                    

                    if st.button("💾 Simpan Grafik (A > B)", key="save_a_not_b"):

                        fig.write_image("model_comparison_a_wins.png", width=800, height=600, scale=2)

                        st.success("✅ Grafik disimpan!")

                else:

                    st.info("Tidak ada query yang memenuhi kriteria ini.")

            

            # TAB 2: A gagal, B berhasil

            with tab2:

                comparison_df = compare_two_models(model_a, model_b, result, model_names, mode='b_not_a')

                

                st.subheader(f"🔍 Query yang gagal di '{model_a}' tapi BERHASIL di '{model_b}'")

                col_m1, col_m2, col_m3 = st.columns(3)

                with col_m1:

                    st.metric("Jumlah Query", len(comparison_df))

                with col_m2:

                    st.metric(f"Hit Rate {model_b[:20]}...", f"{result[model_b].sum()} hits")

                with col_m3:

                    advantage = len(comparison_df)

                    st.metric("Keunggulan B", f"{advantage} query")

                

                if len(comparison_df) > 0:

                    display_cols = ['qid', 'query_type', 'query', model_a, model_b]

                    st.dataframe(comparison_df[display_cols], use_container_width=True)

                    

                    # Breakdown by query type

                    st.subheader("📊 Breakdown per Tipe Query")

                    type_breakdown = comparison_df['query_type'].value_counts().sort_index()

                    

                    fig = px.pie(

                        values=type_breakdown.values, 

                        names=[f"Tipe {int(x)}" for x in type_breakdown.index],

                        title=f"Distribusi Tipe Query - Keunggulan {model_b[:30]}",

                        color_discrete_sequence=px.colors.qualitative.Set2

                    )

                    fig = apply_plot_theme(fig, colors)

                    st.plotly_chart(fig, use_container_width=True)

                    

                    if st.button("💾 Simpan Grafik (B > A)", key="save_b_not_a"):

                        fig.write_image("model_comparison_b_wins.png", width=800, height=600, scale=2)

                        st.success("✅ Grafik disimpan!")

                else:

                    st.info("Tidak ada query yang memenuhi kriteria ini.")

            

            # TAB 3: Keduanya berhasil

            with tab3:

                comparison_df = compare_two_models(model_a, model_b, result, model_names, mode='both')

                

                st.subheader(f"✅✅ Query yang BERHASIL ditemukan oleh KEDUA model")

                st.markdown(f"*Query yang berhasil ditemukan oleh **'{model_a}'** DAN **'{model_b}'***")

                

                col_m1, col_m2, col_m3 = st.columns(3)

                with col_m1:

                    st.metric("Jumlah Query (Both Hit)", len(comparison_df))

                with col_m2:

                    overlap_pct = (len(comparison_df) / len(result)) * 100

                    st.metric("Overlap Rate", f"{overlap_pct:.1f}%")

                with col_m3:

                    a_only = len(compare_two_models(model_a, model_b, result, model_names, mode='a_not_b'))

                    b_only = len(compare_two_models(model_a, model_b, result, model_names, mode='b_not_a'))

                    st.metric("Unique to A / B", f"{a_only} / {b_only}")

                

                if len(comparison_df) > 0:

                    display_cols = ['qid', 'query_type', 'query', model_a, model_b]

                    st.dataframe(comparison_df[display_cols], use_container_width=True)

                    

                    # Show query types that both models succeed

                    st.subheader("📊 Tipe Query yang Dikuasai Kedua Model")

                    type_breakdown = comparison_df['query_type'].value_counts().sort_index()

                    

                    fig = px.bar(

                        x=[f"Tipe {int(x)}" for x in type_breakdown.index],

                        y=type_breakdown.values,

                        labels={'x': 'Tipe Query', 'y': 'Jumlah Query'},

                        title=f"Query yang Berhasil di Kedua Model - Breakdown per Tipe",

                        color=type_breakdown.values,

                        color_continuous_scale='Greens'

                    )

                    fig = apply_plot_theme(fig, colors)

                    st.plotly_chart(fig, use_container_width=True)

                    

                    if st.button("💾 Simpan Grafik (Both Success)", key="save_both"):

                        fig.write_image("model_comparison_both_success.png", width=800, height=600, scale=2)

                        st.success("✅ Grafik disimpan!")

                else:

                    st.info("Tidak ada query yang berhasil ditemukan oleh kedua model.")

            

            # TAB 4: Keduanya gagal

            with tab4:

                comparison_df = compare_two_models(model_a, model_b, result, model_names, mode='neither')

                

                st.subheader(f"❌❌ Query yang GAGAL ditemukan oleh KEDUA model")

                st.markdown(f"*Query yang **gagal** ditemukan oleh **'{model_a}'** DAN **'{model_b}'***")

                st.caption("⚠️ Query-query ini adalah 'hard queries' yang sulit untuk kedua model")

                

                col_m1, col_m2, col_m3 = st.columns(3)

                with col_m1:

                    st.metric("Jumlah Query (Both Miss)", len(comparison_df))

                with col_m2:

                    miss_rate = (len(comparison_df) / len(result)) * 100

                    st.metric("Both Miss Rate", f"{miss_rate:.1f}%")

                with col_m3:

                    total_hard = len(result) - len(compare_two_models(model_a, model_b, result, model_names, mode='both'))

                    st.metric("Total Hard Queries", f"{total_hard}")

                

                if len(comparison_df) > 0:

                    display_cols = ['qid', 'query_type', 'query', model_a, model_b]

                    st.dataframe(comparison_df[display_cols], use_container_width=True)

                    

                    # Analysis of hard queries

                    st.subheader("📊 Analisis Query Sulit (Hard Queries)")

                    type_breakdown = comparison_df['query_type'].value_counts().sort_index()

                    

                    col_t1, col_t2 = st.columns(2)

                    with col_t1:

                        st.markdown("**Breakdown per Tipe:**")

                        for qtype, count in type_breakdown.items():

                            st.markdown(f"- Tipe {int(qtype)}: {count} query")

                    

                    with col_t2:

                        fig = px.pie(

                            values=type_breakdown.values, 

                            names=[f"Tipe {int(x)}" for x in type_breakdown.index],

                            title="Distribusi Hard Queries per Tipe",

                            color_discrete_sequence=px.colors.sequential.Reds

                        )

                        fig = apply_plot_theme(fig, colors)

                        st.plotly_chart(fig, use_container_width=True)

                    

                    if st.button("💾 Simpan Grafik (Both Fail)", key="save_neither"):

                        fig.write_image("model_comparison_both_fail.png", width=800, height=600, scale=2)

                        st.success("✅ Grafik disimpan!")

                    

                    # Show suggestions for improvement

                    st.info(f"💡 **Insight:** Terdapat {len(comparison_df)} query yang gagal ditemukan oleh kedua model. Query-query ini mungkin memerlukan pendekatan retrieval yang berbeda atau query expansion yang lebih baik.")

                else:

                    st.success("✅ Tidak ada query yang gagal ditemukan oleh kedua model. Semua query berhasil ditemukan oleh minimal satu model!")

        

        st.markdown("---")

        

        # Unique to Model Section

        st.subheader("🌟 Query yang HANYA Ditemukan oleh Satu Model")

        selected_model = st.selectbox("Pilih Model:", model_names, key="unique_model")

        

        unique_df = find_unique_to_model(selected_model, result, model_names)

        st.metric(f"Query yang HANYA ditemukan oleh '{selected_model}'", len(unique_df))

        

        if len(unique_df) > 0:

            st.dataframe(unique_df[['qid', 'query_type', 'query', selected_model]], use_container_width=True)

    

    # =======================================================================

    # PAGE 3: ANALISIS QUERY

    # =======================================================================

    elif page == "🔍 Analisis Query":

        st.header("🔍 Analisis Query")

        

        tab1, tab2, tab3 = st.tabs(["Query Sulit & Mudah", "By Query Type", "Semua/Gagal Semua"])

        

        # Tab 1: Query Sulit & Mudah

        with tab1:

            st.subheader("📊 Distribusi Kesulitan Query")

            

            # Histogram hit count

            hit_dist = result['hit_count'].value_counts().sort_index()

            fig = px.bar(

                x=hit_dist.index, 

                y=hit_dist.values,

                labels={'x': 'Jumlah Model yang Berhasil', 'y': 'Jumlah Query'},

                title="Distribusi: Berapa Model yang Berhasil Menemukan Setiap Query",

                color=hit_dist.values,

                color_continuous_scale='Blues'

            )

            fig = apply_plot_theme(fig, colors)

            st.plotly_chart(fig, use_container_width=True)

            

            col1, col2 = st.columns(2)

            

            with col1:

                st.markdown("#### ❌ Query Sulit (≤2 Model)")

                hard_queries = result[result['hit_count'] <= 2]

                st.metric("Jumlah", len(hard_queries))

                if len(hard_queries) > 0:

                    st.dataframe(

                        hard_queries[['qid', 'query_type', 'query', 'hit_count']], 

                        use_container_width=True,

                        height=300

                    )

            

            with col2:

                st.markdown("#### ✅ Query Mudah (≥10 Model)")

                easy_queries = result[result['hit_count'] >= 10]

                st.metric("Jumlah", len(easy_queries))

                if len(easy_queries) > 0:

                    st.dataframe(

                        easy_queries[['qid', 'query_type', 'query', 'hit_count']], 

                        use_container_width=True,

                        height=300

                    )

        

        # Tab 2: By Query Type

        with tab2:

            st.subheader("📊 Performa per Tipe Query")

            

            type_summary = hit_rate_by_query_type(result, model_names)

            

            # Heatmap

            pivot_type = type_summary.pivot(index='Model', columns='Query Type', values='Hit Rate (%)')

            

            # Choose colorscale based on theme

            colorscale = 'RdYlGn' if st.session_state.theme == 'light' else 'RdYlGn'

            

            fig = px.imshow(

                pivot_type,

                text_auto='.1f',

                aspect='auto',

                color_continuous_scale=colorscale,

                title="Heatmap: Hit Rate (%) per Model per Tipe Query"

            )

            fig = apply_plot_theme(fig, colors)

            st.plotly_chart(fig, use_container_width=True)

            

            # Export button

            if st.button("💾 Simpan Heatmap"):

                fig.write_image("heatmap_query_type.png", width=1000, height=800, scale=2)

                st.success("✅ Heatmap disimpan sebagai 'heatmap_query_type.png'")

            

            # Tabel detail

            st.dataframe(type_summary, use_container_width=True)

        

        # Tab 3: Semua/Gagal Semua

        with tab3:

            col1, col2 = st.columns(2)

            

            with col1:

                st.markdown("#### ✅ Ditemukan SEMUA Model")

                all_hit = find_queries_all_models_hit(result, model_names)

                st.metric("Jumlah", len(all_hit))

                if len(all_hit) > 0:

                    st.dataframe(

                        all_hit[['qid', 'query_type', 'query']], 

                        use_container_width=True,

                        height=400

                    )

            

            with col2:

                st.markdown("#### ❌ Gagal SEMUA Model")

                all_miss = find_queries_all_models_miss(result, model_names)

                st.metric("Jumlah", len(all_miss))

                if len(all_miss) > 0:

                    st.dataframe(

                        all_miss[['qid', 'query_type', 'query']], 

                        use_container_width=True,

                        height=400

                    )

    

    # =======================================================================

    # PAGE 4: METRIK LENGKAP (MRR & SUCCESS@K)

    # =======================================================================

    elif page == "📊 Metrik Lengkap (MRR & Success@k)":

        st.header("📊 Metrik Lengkap: MRR & Success@k")

        st.markdown("*Mean Reciprocal Rank (MRR) dan Success Rate pada berbagai cutoff (10, 20, 50, 100)*")

        

        # Prepare overall data

        overall_display = df_overall[['Skenario', 'name', 'recip_rank', 'success_10 (%)', 'success_20 (%)', 'success_50 (%)', 'success_100 (%)']].copy()

        overall_display.columns = ['Skenario', 'Model', 'MRR', 'Success@10', 'Success@20', 'Success@50', 'Success@100']

        

        # Sort by MRR

        overall_display = overall_display.sort_values('MRR', ascending=False).reset_index(drop=True)

        overall_display['Rank'] = range(1, len(overall_display) + 1)

        

        # Reorder columns

        overall_display = overall_display[['Rank', 'Skenario', 'Model', 'MRR', 'Success@10', 'Success@20', 'Success@50', 'Success@100']]

        

        col1, col2 = st.columns([2, 1])

        

        with col1:

            st.subheader("🏆 Ranking Model berdasarkan MRR")

            

            # Highlight top 3

            def highlight_mrr(val):

                if isinstance(val, float):

                    if val >= 0.30:

                        return 'background-color: #90EE90; color: black'

                    elif val >= 0.15:

                        return 'background-color: #FFD700; color: black'

                return ''

            

            styled_overall = overall_display.style.applymap(highlight_mrr, subset=['MRR'])

            st.dataframe(styled_overall, use_container_width=True, height=500)

        

        with col2:

            st.subheader("📈 Statistik MRR")

            st.metric("MRR Tertinggi", f"{overall_display['MRR'].max():.4f}")

            st.metric("MRR Terendah", f"{overall_display['MRR'].min():.4f}")

            st.metric("Rata-rata MRR", f"{overall_display['MRR'].mean():.4f}")

            

            st.markdown("---")

            st.markdown("**📝 Catatan:**")

            st.markdown("- MRR = Mean Reciprocal Rank")

            st.markdown("- Semakin tinggi MRR, semakin baik")

            st.markdown("- MRR > 0.3 dianggap baik")

        

        st.markdown("---")

        

        # Success@k Curve

        st.subheader("📉 Success@k Curve")

        st.markdown("*Kurva yang menunjukkan peningkatan success rate seiring dengan bertambahnya jumlah dokumen yang di-retrieve (k)*")

        

        # Prepare data for curve

        curve_data = []

        for _, row in df_overall.iterrows():

            curve_data.append({

                'Model': row['name'],

                'Skenario': row['Skenario'],

                'k': 10,

                'Success Rate': row['success_10 (%)']

            })

            curve_data.append({

                'Model': row['name'],

                'Skenario': row['Skenario'],

                'k': 20,

                'Success Rate': row['success_20 (%)']

            })

            curve_data.append({

                'Model': row['name'],

                'Skenario': row['Skenario'],

                'k': 50,

                'Success Rate': row['success_50 (%)']

            })

            curve_data.append({

                'Model': row['name'],

                'Skenario': row['Skenario'],

                'k': 100,

                'Success Rate': row['success_100 (%)']

            })

        

        curve_df = pd.DataFrame(curve_data)

        

        # Filter option

        show_all_curves = st.checkbox("Tampilkan semua model", value=False)

        

        if show_all_curves:

            fig = px.line(

                curve_df, 

                x='k', 

                y='Success Rate', 

                color='Model',

                markers=True,

                title="Success@k Curve untuk Semua Model",

                labels={'k': 'Cutoff (k)', 'Success Rate': 'Success Rate (%)'}

            )

        else:

            # Show top 5 models by MRR

            top_models = overall_display.head(5)['Model'].tolist()

            curve_top = curve_df[curve_df['Model'].isin(top_models)]

            

            fig = px.line(

                curve_top, 

                x='k', 

                y='Success Rate', 

                color='Model',

                markers=True,

                title="Success@k Curve - Top 5 Model (berdasarkan MRR)",

                labels={'k': 'Cutoff (k)', 'Success Rate': 'Success Rate (%)'}

            )

        

        fig.update_traces(line_width=3, marker_size=10)

        fig.update_layout(

            xaxis=dict(tickmode='array', tickvals=[10, 20, 50, 100]),

            yaxis=dict(range=[0, 100])

        )

        fig = apply_plot_theme(fig, colors)

        st.plotly_chart(fig, use_container_width=True)

        

        if st.button("💾 Simpan Success Curve", key="save_curve"):

            fig.write_image("success_curve.png", width=1200, height=700, scale=2)

            st.success("✅ Success curve disimpan!")

        

        st.markdown("---")

        

        # Comparison by Scenario

        st.subheader("📊 Perbandingan per Skenario")

        

        scenario_tabs = st.tabs(["Skenario 1 (BM25)", "Skenario 2 (Dense)", "Skenario 3 (AraDPR)"])

        

        for idx, (tab, skenario) in enumerate(zip(scenario_tabs, 

                                                   ['1. BM25 (Sparse)', '2. Cross-Lingual (Dense)', '3. AraDPR (Monolingual)'])):

            with tab:

                scenario_data = overall_display[overall_display['Skenario'] == skenario].copy()

                scenario_data = scenario_data.drop('Skenario', axis=1)

                

                col_s1, col_s2 = st.columns([3, 2])

                

                with col_s1:

                    st.dataframe(scenario_data, use_container_width=True)

                

                with col_s2:

                    # Mini curve for this scenario

                    scenario_curve = curve_df[curve_df['Skenario'] == skenario]

                    

                    fig_mini = px.line(

                        scenario_curve,

                        x='k',

                        y='Success Rate',

                        color='Model',

                        markers=True,

                        title=f"Success Curve - {skenario}"

                    )

                    fig_mini.update_layout(xaxis=dict(tickmode='array', tickvals=[10, 20, 50, 100]))

                    fig_mini = apply_plot_theme(fig_mini, colors)

                    st.plotly_chart(fig_mini, use_container_width=True)

        

        st.markdown("---")

        

        # MRR vs Success@10 Scatter

        st.subheader("🔍 MRR vs Success@10 Analysis")

        st.markdown("*Scatter plot untuk melihat hubungan antara MRR dan Success@10*")

        

        fig_scatter = px.scatter(

            overall_display,

            x='MRR',

            y='Success@10',

            color='Skenario',

            text='Model',

            size='Success@100',

            hover_data=['Success@20', 'Success@50'],

            title="MRR vs Success@10 (ukuran bubble = Success@100)"

        )

        fig_scatter.update_traces(textposition='top center', textfont_size=8)

        fig_scatter = apply_plot_theme(fig_scatter, colors)

        st.plotly_chart(fig_scatter, use_container_width=True)

        

        st.info("💡 **Interpretasi:** Model yang berada di pojok kanan atas adalah model terbaik (MRR tinggi dan Success@10 tinggi). Ukuran bubble menunjukkan Success@100 - semakin besar berarti semakin banyak query yang berhasil ditemukan dalam top-100.")

    

    # =======================================================================

    # PAGE 5: QUERY BAHASA ARAB

    # =======================================================================

    elif page == "🌍 Query Bahasa Arab":
        st.header("🌍 Query dalam Bahasa Arab")
        st.markdown("*Perbandingan terjemahan query ke bahasa Arab menggunakan Google NMT vs Gemini LLM*")
        
        if df_arab is None:
            st.error("❌ File queries_arab.csv tidak ditemukan!")
        else:
            # Merge dengan data hasil retrieval
            arab_with_results = df_arab.merge(
                result[['qid', 'query_type']], 
                on='qid', 
                how='left'
            )
            
            # Filter options
            st.subheader("🔍 Filter Query")
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                filter_type = st.multiselect(
                    "Tipe Query:",
                    options=[1, 2, 3],
                    default=[1, 2, 3],
                    format_func=lambda x: f"Tipe {x}"
                )
            
            with col_f2:
                search_text = st.text_input("Cari query (Indonesia):", "")
            
            with col_f3:
                show_diff_only = st.checkbox("Hanya tampilkan query dengan perbedaan signifikan", value=False)
            
            # Apply filters
            filtered_df = arab_with_results[arab_with_results['query_type'].isin(filter_type)]
            
            if search_text:
                filtered_df = filtered_df[filtered_df['query'].str.contains(search_text, case=False, na=False)]
            
            # Display stats
            st.markdown("---")
            st.subheader("📊 Statistik")
            
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("Total Query", len(filtered_df))
            with col_s2:
                avg_len_nmt = filtered_df['query_nmt'].str.len().mean()
                avg_len_llm = filtered_df['query_llm'].str.len().mean()
                st.metric("Rata-rata Panjang (NMT / LLM)", f"{avg_len_nmt:.0f} / {avg_len_llm:.0f}")
            with col_s3:
                len_diff = abs(filtered_df['query_nmt'].str.len() - filtered_df['query_llm'].str.len()).mean()
                st.metric("Rata-rata Perbedaan Panjang", f"{len_diff:.0f} karakter")
            
            # Display table
            st.markdown("---")
            st.subheader("📋 Daftar Query")
            
            # Prepare display columns
            display_df = filtered_df[['qid', 'query_type', 'query', 'query_nmt', 'query_llm']].copy()
            display_df.columns = ['ID', 'Tipe', 'Query (Indonesia)', 'Arab (Google NMT)', 'Arab (Gemini LLM)']
            
            # Add length comparison
            display_df['Panjang NMT'] = display_df['Arab (Google NMT)'].str.len()
            display_df['Panjang LLM'] = display_df['Arab (Gemini LLM)'].str.len()
            display_df['Selisih'] = display_df['Panjang NMT'] - display_df['Panjang LLM']
            
            st.dataframe(display_df, use_container_width=True, height=500)
            
            # Sample comparison
            st.markdown("---")
            st.subheader("🔬 Perbandingan Detail (Sample)")
            
            sample_qid = st.selectbox(
                "Pilih Query untuk dilihat detailnya:",
                options=filtered_df['qid'].tolist(),
                format_func=lambda x: f"Q{x}: {filtered_df[filtered_df['qid']==x]['query'].iloc[0][:50]}..."
            )
            
            if sample_qid:
                sample = filtered_df[filtered_df['qid'] == sample_qid].iloc[0]
                
                col_d1, col_d2, col_d3 = st.columns(3)
                
                with col_d1:
                    st.markdown("**🇮🇩 Indonesia**")
                    st.info(sample['query'])
                    st.caption(f"Tipe: {sample['query_type']}")
                    if st.button("📋 Copy Indonesia", key=f"copy_indo_{sample_qid}"):
                        if copy_to_clipboard(sample['query']):
                            st.success(f"Copied! ({len(sample['query'])} chars)")
                
                with col_d2:
                    st.markdown("**🔤 Arab (Google NMT)**")
                    st.success(sample['query_nmt'])
                    st.caption(f"Panjang: {len(sample['query_nmt'])} char")
                    if st.button("📋 Copy NMT", key=f"copy_nmt_{sample_qid}"):
                        if copy_to_clipboard(sample['query_nmt']):
                            st.success(f"Copied! ({len(sample['query_nmt'])} chars)")
                
                with col_d3:
                    st.markdown("**🤖 Arab (Gemini LLM)**")
                    st.warning(sample['query_llm'])
                    st.caption(f"Panjang: {len(sample['query_llm'])} char")
                    if st.button("📋 Copy LLM", key=f"copy_llm_{sample_qid}"):
                        if copy_to_clipboard(sample['query_llm']):
                            st.success(f"Copied! ({len(sample['query_llm'])} chars)")
                
                # Analysis Section
                st.markdown("---")
                st.subheader("📚 Dokumen Korpus yang Relevan")
                st.markdown(f"*Dokumen Fathul Muin untuk query Q{sample_qid}*")
                
                if df_qrels is not None and df_corpus is not None:
                    relevant_docs = df_qrels[df_qrels['qid'] == sample_qid]
                    
                    if len(relevant_docs) > 0:
                        docno = relevant_docs.iloc[0]['docno']
                        corpus_doc = df_corpus[df_corpus['docno'] == docno]
                        
                        if len(corpus_doc) > 0:
                            doc_text = corpus_doc.iloc[0]['text']
                            
                            col_doc1, col_doc2 = st.columns([3, 1])
                            with col_doc1:
                                st.markdown(f"**📄 ID: `{docno}`**")
                            with col_doc2:
                                st.markdown("**✅ Relevan**")
                            
                            st.markdown("---")
                            st.markdown("**📝 Isi Dokumen:**")
                            
                            max_chars = 3000
                            if len(doc_text) > max_chars:
                                display_text = doc_text[:max_chars] + "... [Dokumen dipotong]"
                                st.caption(f"Panjang: {len(doc_text)} char, menampilkan {max_chars} char")
                            else:
                                display_text = doc_text
                            
                            st.text_area(
                                label="corpus_text",
                                value=display_text,
                                height=400,
                                label_visibility="collapsed",
                                key=f"corpus_{sample_qid}_{docno}"
                            )
                            
                            # Copy buttons
                            col_copy1, col_copy2, col_copy3 = st.columns(3)
                            with col_copy1:
                                if st.button(f"📋 Copy ID", key=f"copy_docno_{sample_qid}"):
                                    if copy_to_clipboard(docno):
                                        st.success("ID copied!")
                            with col_copy2:
                                if st.button(f"📋 Copy Dokumen", key=f"copy_doc_{sample_qid}"):
                                    if copy_to_clipboard(doc_text):
                                        st.success(f"Dokumen copied! ({len(doc_text)} chars)")
                            with col_copy3:
                                combined = f"Query: {sample['query']}\n\nDokumen ({docno}):\n{doc_text[:1000]}..."
                                if st.button(f"📋 Copy Query+Doc", key=f"copy_both_{sample_qid}"):
                                    if copy_to_clipboard(combined):
                                        st.success("Query+Doc copied!")
                            
                            # Stats
                            st.markdown("---")
                            col_stat1, col_stat2, col_stat3 = st.columns(3)
                            with col_stat1:
                                st.metric("Panjang", f"{len(doc_text)} char")
                            with col_stat2:
                                word_count = len(doc_text.split())
                                st.metric("Kata", f"~{word_count}")
                            with col_stat3:
                                line_count = len(doc_text.split('\n'))
                                st.metric("Baris", f"~{line_count}")
                        else:
                            st.error(f"❌ Dokumen {docno} tidak ditemukan")
                    else:
                        st.warning("⚠️ Tidak ada informasi relevansi")
                else:
                    st.error("❌ Data qrels atau korpus tidak tersedia")
                
                # PERFORMA QUERY SECTION
                st.markdown("---")
                st.subheader("📊 Analisis Perbedaan")
                
                len_nmt = len(sample['query_nmt'])
                len_llm = len(sample['query_llm'])
                
                col_a1, col_a2 = st.columns(2)
                
                with col_a1:
                    st.markdown("**Perbandingan Panjang:**")
                    fig_len = go.Figure()
                    fig_len.add_trace(go.Bar(
                        name='Google NMT',
                        x=['Panjang Karakter'],
                        y=[len_nmt],
                        marker_color='#4CAF50'
                    ))
                    fig_len.add_trace(go.Bar(
                        name='Gemini LLM',
                        x=['Panjang Karakter'],
                        y=[len_llm],
                        marker_color='#FF9800'
                    ))
                    fig_len.update_layout(
                        title="Perbandingan Panjang Terjemahan",
                        barmode='group'
                    )
                    fig_len = apply_plot_theme(fig_len, colors)
                    st.plotly_chart(fig_len, use_container_width=True)
                
                with col_a2:
                    st.markdown("**Insight:**")
                    if len_llm < len_nmt:
                        st.success(f"✅ Gemini LLM lebih ringkas ({len_llm} vs {len_nmt} char)")
                    elif len_llm > len_nmt:
                        st.info(f"ℹ️ Gemini LLM lebih panjang ({len_llm} vs {len_nmt} char)")
                    else:
                        st.caption("📊 Panjang sama")
                    
                    st.markdown("---")
                    st.markdown("**Query Type:**")
                    if sample['query_type'] == 1:
                        st.markdown("📝 **Tipe 1**: Kata Kunci")
                    elif sample['query_type'] == 2:
                        st.markdown("❓ **Tipe 2**: Tanya Awam")
                    else:
                        st.markdown("📖 **Tipe 3**: Studi Kasus")
                
                # CORPUS SECTION
                st.markdown("---")
                st.subheader("🎯 Performa Query untuk Semua Model")
                st.markdown(f"*Ranking dan keberhasilan query Q{sample_qid}*")
                
                query_detail = df_detail[df_detail['qid'] == sample_qid].copy()
                
                if len(query_detail) > 0:
                    query_perf = query_detail[['name', 'Skenario', 'rank_ditemukan', 'Hit@10', 'Hit@20', 'Hit@50', 'Hit@100']].copy()
                    query_perf.columns = ['Model', 'Skenario', 'Rank', 'Hit@10', 'Hit@20', 'Hit@50', 'Hit@100']
                    
                    query_perf['Rank'] = pd.to_numeric(query_perf['Rank'], errors='coerce').fillna(0).astype(int)
                    query_perf['Rank Display'] = query_perf['Rank'].apply(lambda x: str(x) if x > 0 else '-')
                    query_perf = query_perf.sort_values('Rank', ascending=False)
                    
                    def status_indicator(hit_status):
                        return '✅' if hit_status == '✅ Hit' else '❌'
                    
                    query_perf['S@10'] = query_perf['Hit@10'].apply(status_indicator)
                    query_perf['S@20'] = query_perf['Hit@20'].apply(status_indicator)
                    query_perf['S@50'] = query_perf['Hit@50'].apply(status_indicator)
                    query_perf['S@100'] = query_perf['Hit@100'].apply(status_indicator)
                    
                    success_at_10 = (query_perf['Hit@10'] == '✅ Hit').sum()
                    total_models = len(query_perf)
                    
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("Model Berhasil (S@10)", f"{success_at_10}/{total_models}")
                    with col_stat2:
                        best_rank = query_perf[query_perf['Rank'] > 0]['Rank'].min() if (query_perf['Rank'] > 0).any() else '-'
                        st.metric("Rank Terbaik", f"#{best_rank}" if best_rank != '-' else '-')
                    with col_stat3:
                        success_rate = (success_at_10 / total_models) * 100
                        st.metric("Success Rate", f"{success_rate:.1f}%")
                    
                    display_perf = query_perf[['Model', 'Skenario', 'Rank Display', 'S@10', 'S@20', 'S@50', 'S@100']].copy()
                    display_perf.columns = ['Model', 'Skenario', 'Rank', '@10', '@20', '@50', '@100']
                    
                    def highlight_best_rank(val):
                        try:
                            val_int = int(val)
                            if val_int == best_rank and val != '-':
                                return 'background-color: #FFD700; color: black; font-weight: bold'
                        except (ValueError, TypeError):
                            pass
                        return ''
                    
                    styled_perf = display_perf.style.applymap(highlight_best_rank, subset=['Rank'])
                    st.dataframe(styled_perf, use_container_width=True, height=400)
                    
                    # Rank comparison chart
                    st.markdown("---")
                    st.subheader("📊 Perbandingan Ranking")
                    
                    found_queries = query_perf[query_perf['Rank'] > 0].copy()
                    
                    if len(found_queries) > 0:
                        found_queries = found_queries.sort_values('Rank', ascending=True)
                        
                        fig_rank = px.bar(
                            found_queries,
                            x='Rank',
                            y='Model',
                            orientation='h',
                            color='Rank',
                            color_continuous_scale='RdYlGn_r',
                            title=f"Ranking Query Q{sample_qid} (Semakin kecil = Semakin baik)",
                            text='Rank'
                        )
                        fig_rank.update_traces(textposition='outside')
                        fig_rank.update_layout(xaxis_title="Rank", yaxis_title="")
                        fig_rank = apply_plot_theme(fig_rank, colors)
                        st.plotly_chart(fig_rank, use_container_width=True)
                        
                        # Success rate by scenario
                        st.markdown("---")
                        st.subheader("📈 Success Rate per Skenario")
                        
                        scenario_success = query_perf.groupby('Skenario').agg({
                            'Hit@10': lambda x: (x == '✅ Hit').sum() / len(x) * 100
                        }).reset_index()
                        scenario_success.columns = ['Skenario', 'Success Rate (%)']
                        
                        fig_scenario = px.bar(
                            scenario_success,
                            x='Skenario',
                            y='Success Rate (%)',
                            color='Success Rate (%)',
                            color_continuous_scale='Greens',
                            title="Success Rate @10 per Skenario",
                            text='Success Rate (%)'
                        )
                        fig_scenario.update_traces(texttemplate='%{text:.1f}%')
                        fig_scenario = apply_plot_theme(fig_scenario, colors)
                        st.plotly_chart(fig_scenario, use_container_width=True)
                    else:
                        st.warning("⚠️ Query tidak ditemukan oleh semua model")
                else:
                    st.error("❌ Data detail tidak ditemukan")
            
            # Export option
            st.markdown("---")
            if st.button("💾 Export Query Arab ke CSV"):
                export_file = "query_arab_export.csv"
                display_df.to_csv(export_file, index=False)
                st.success(f"✅ Data diexport ke {export_file}")
    
    elif page == "📈 Visualisasi Lanjutan":

        st.header("📊 Visualisasi Lanjutan")

        

        # Fine-tuned vs Baseline Comparison

        st.subheader("📈 Fine-Tuned vs Baseline Comparison")

        

        comparisons = [

            ('Baseline (DistilBERT Base)', 'DistilBERT Base Fine-Tuned (JH-POLO)'),

            ('Baseline (mmBERT-base)', 'mmBERT-base Fine-Tuned (JH-POLO)'),

            ('Baseline (mmBERT-small)', 'mmBERT-small Fine-Tuned (JH-POLO)')

        ]

        

        ft_data = []

        for base, ft in comparisons:

            if base in model_names and ft in model_names:

                base_hits = result[base].sum()

                ft_hits = result[ft].sum()

                improved = len(result[(result[base] == 0) & (result[ft] == 1)])

                ft_data.append({

                    'Model Pair': base.replace('Baseline (', '').replace(')', ''),

                    'Baseline': base_hits,

                    'Fine-Tuned': ft_hits,

                    'Improved': improved

                })

        

        if ft_data:

            ft_df = pd.DataFrame(ft_data)

            

            # Grouped bar chart

            fig = go.Figure()

            fig.add_trace(go.Bar(

                name='Baseline',

                x=ft_df['Model Pair'],

                y=ft_df['Baseline'],

                marker_color=colors['secondary']

            ))

            fig.add_trace(go.Bar(

                name='Fine-Tuned',

                x=ft_df['Model Pair'],

                y=ft_df['Fine-Tuned'],

                marker_color=colors['primary']

            ))

            

            fig.update_layout(

                barmode='group',

                title="Fine-Tuned vs Baseline Performance"

            )

            fig = apply_plot_theme(fig, colors)

            st.plotly_chart(fig, use_container_width=True)

            

            # Table

            st.dataframe(ft_df, use_container_width=True)

        

        st.markdown("---")

        

        # LLM vs NMT Comparison

        st.subheader("📈 LLM vs NMT Translation Comparison")

        

        llm_nmt_pairs = [

            ('BM25 (Google NMT)', 'BM25 (Gemini LLM)'),

            ('BM25+RM3 (Google NMT)', 'BM25+RM3 (Gemini LLM)'),

            ('AraDPR (Google NMT)', 'AraDPR (Gemini LLM)')

        ]

        

        llm_data = []

        for nmt, llm in llm_nmt_pairs:

            if nmt in model_names and llm in model_names:

                nmt_hits = result[nmt].sum()

                llm_hits = result[llm].sum()

                llm_win = len(result[(result[nmt] == 0) & (result[llm] == 1)])

                llm_data.append({

                    'Model': nmt.replace(' (Google NMT)', '').replace(' (Gemini LLM)', ''),

                    'Google NMT': nmt_hits,

                    'Gemini LLM': llm_hits,

                    'LLM Wins': llm_win

                })

        

        if llm_data:

            llm_df = pd.DataFrame(llm_data)

            

            # Grouped bar chart

            fig = go.Figure()

            fig.add_trace(go.Bar(

                name='Google NMT',

                x=llm_df['Model'],

                y=llm_df['Google NMT'],

                marker_color='#FF6B6B'

            ))

            fig.add_trace(go.Bar(

                name='Gemini LLM',

                x=llm_df['Model'],

                y=llm_df['Gemini LLM'],

                marker_color='#4ECDC4'

            ))

            

            fig.update_layout(

                barmode='group',

                title="Google NMT vs Gemini LLM Translation Performance"

            )

            fig = apply_plot_theme(fig, colors)

            st.plotly_chart(fig, use_container_width=True)

        

        st.markdown("---")

        

        # Model Correlation Heatmap

        st.subheader("📊 Korelasi antar Model")

        corr_matrix = result[model_names].corr()

        

        fig = px.imshow(

            corr_matrix,

            text_auto='.2f',

            aspect='auto',

            color_continuous_scale='RdBu',

            title="Correlation Matrix: Seberapa Sering Model Menemukan Query yang Sama",

            zmin=-1,

            zmax=1

        )

        fig = apply_plot_theme(fig, colors)

        st.plotly_chart(fig, use_container_width=True)

        

        # Export

        if st.button("💾 Simpan Correlation Matrix"):

            fig.write_image("correlation_matrix.png", width=1000, height=1000, scale=2)

            st.success("✅ Correlation matrix disimpan sebagai 'correlation_matrix.png'")



# ============================================================================

# RUN

# ============================================================================

if __name__ == "__main__":

    main()
