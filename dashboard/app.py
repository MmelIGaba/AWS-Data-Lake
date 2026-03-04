import streamlit as st
import pandas as pd
import boto3
import plotly.express as px
import plotly.graph_objects as go
import time

st.set_page_config(
    page_title="COVID-19 Data Lake Dashboard",
    layout="wide"
)

st.title("COVID-19 Data Lake Dashboard")
st.markdown("Powered by Amazon Athena and AWS Glue Data Lake")
st.divider()

@st.cache_data(ttl=300, show_spinner=False)
def run_athena_query(query, database="datalake_db", workgroup="covid19-workgroup"):
    client = boto3.client("athena", region_name="us-east-1")
    execution_id = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": database},
        WorkGroup=workgroup
    )["QueryExecutionId"]

    while True:
        status = client.get_query_execution(
            QueryExecutionId=execution_id
        )["QueryExecution"]["Status"]["State"]
        if status in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            break
        time.sleep(1)

    if status != "SUCCEEDED":
        st.error(f"Athena query failed: {status}")
        return pd.DataFrame()

    results = client.get_query_results(QueryExecutionId=execution_id)
    rows = results["ResultSet"]["Rows"]
    headers = [col.get("VarCharValue", "") for col in rows[0]["Data"]]
    data = [[col.get("VarCharValue", None) for col in row["Data"]] for row in rows[1:]]
    return pd.DataFrame(data, columns=headers)

# -------------------------
# Sidebar Filters
# -------------------------
st.sidebar.header("Filters")

selected_year = st.sidebar.selectbox(
    "Year",
    ["All", "2020", "2021", "2022"]
)

continent_options = ["All", "Africa", "Asia", "Europe", "North America", "Oceania", "South America"]
selected_continent = st.sidebar.selectbox(
    "Continent",
    continent_options
)

top_n = st.sidebar.slider(
    "Top N Countries",
    min_value=5,
    max_value=50,
    value=20,
    step=5
)

metric = st.sidebar.selectbox(
    "Primary Metric",
    ["total_cases", "total_deaths", "people_fully_vaccinated"]
)

# -------------------------
# Build filter clauses
# -------------------------
year_filter = f"AND year = '{selected_year}'" if selected_year != "All" else ""
continent_filter = f"AND continent = '{selected_continent}'" if selected_continent != "All" else ""

# -------------------------
# Global KPIs
# -------------------------
st.subheader("Global Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with st.spinner("Loading global metrics..."):
    kpi_query = """
        SELECT
            MAX(total_cases) AS total_cases,
            MAX(total_deaths) AS total_deaths,
            MAX(people_fully_vaccinated) AS fully_vaccinated,
            ROUND(MAX(total_deaths) / NULLIF(MAX(total_cases),0)*100,2) AS death_rate
        FROM datalake_db.processed
        WHERE location = 'World'
    """
    kpi_df = run_athena_query(kpi_query)
    if not kpi_df.empty:
        col1.metric("Total Cases", f"{float(kpi_df['total_cases'][0]):,.0f}")
        col2.metric("Total Deaths", f"{float(kpi_df['total_deaths'][0]):,.0f}")
        col3.metric("Fully Vaccinated", f"{float(kpi_df['fully_vaccinated'][0]):,.0f}")
        col4.metric("Global Death Rate", f"{float(kpi_df['death_rate'][0]):.2f}%")

st.divider()

# -------------------------
# Monthly Global New Cases Trend (FIXED: aggregate properly)
# -------------------------
st.subheader("Monthly Global New Cases Trend")
with st.spinner("Loading trend data..."):
    trend_query = f"""
        SELECT year, month, SUM(new_cases) AS monthly_new_cases
        FROM datalake_db.processed
        WHERE location = 'World'
        {year_filter}
        GROUP BY year, month
        ORDER BY year, month
    """
    trend_df = run_athena_query(trend_query)
    if not trend_df.empty:
        trend_df["period"] = trend_df["year"] + "-" + trend_df["month"].str.zfill(2)
        trend_df["monthly_new_cases"] = pd.to_numeric(trend_df["monthly_new_cases"], errors="coerce")
        fig1 = px.area(
            trend_df,
            x="period",
            y="monthly_new_cases",
            title="Monthly New Cases (Global)",
            labels={"period": "Period", "monthly_new_cases": "New Cases"}
        )
        st.plotly_chart(fig1, use_container_width=True)

st.divider()

# -------------------------
# Top N Countries by Selected Metric & Vaccination Side-by-Side
# -------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader(f"Top {top_n} Countries by {metric.replace('_', ' ').title()}")
    with st.spinner("Loading country data..."):
        country_query = f"""
            SELECT location, MAX({metric}) AS metric_value
            FROM datalake_db.processed
            WHERE continent IS NOT NULL
            {continent_filter}
            GROUP BY location
            ORDER BY metric_value DESC
            LIMIT {top_n}
        """
        country_df = run_athena_query(country_query)
        if not country_df.empty:
            country_df["metric_value"] = pd.to_numeric(country_df["metric_value"], errors="coerce")
            fig2 = px.bar(
                country_df,
                x="metric_value",
                y="location",
                orientation="h",
                title=f"{metric.replace('_', ' ').title()} by Country",
                labels={"metric_value": metric.replace('_', ' ').title(), "location": "Country"}
            )
            fig2.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig2, use_container_width=True)

with col_right:
    st.subheader("Vaccination Progress by Continent")
    with st.spinner("Loading vaccination data..."):
        vacc_query = f"""
            SELECT continent, MAX(people_fully_vaccinated_per_hundred) AS fully_vaccinated_pct
            FROM datalake_db.processed
            WHERE continent IS NOT NULL
            {year_filter}
            GROUP BY continent
            ORDER BY fully_vaccinated_pct DESC
        """
        vacc_df = run_athena_query(vacc_query)
        if not vacc_df.empty:
            vacc_df["fully_vaccinated_pct"] = pd.to_numeric(vacc_df["fully_vaccinated_pct"], errors="coerce")
            fig3 = px.bar(
                vacc_df,
                x="continent",
                y="fully_vaccinated_pct",
                title="Fully Vaccinated % by Continent",
                labels={"fully_vaccinated_pct": "Fully Vaccinated (%)", "continent": "Continent"},
                color="fully_vaccinated_pct",
                color_continuous_scale="blues"
            )
            st.plotly_chart(fig3, use_container_width=True)

st.divider()

# -------------------------
# Death Rate by Country
# -------------------------
st.subheader(f"Top {top_n} Countries by Death Rate")
with st.spinner("Loading death rate data..."):
    death_query = f"""
        SELECT location,
               ROUND(MAX(total_deaths)/NULLIF(MAX(total_cases),0)*100,2) AS death_rate_pct
        FROM datalake_db.processed
        WHERE continent IS NOT NULL
        {continent_filter}
        GROUP BY location
        ORDER BY death_rate_pct DESC
        LIMIT {top_n}
    """
    death_df = run_athena_query(death_query)
    if not death_df.empty:
        death_df["death_rate_pct"] = pd.to_numeric(death_df["death_rate_pct"], errors="coerce")
        fig4 = px.bar(
            death_df,
            x="location",
            y="death_rate_pct",
            title=f"Death Rate % by Country (Top {top_n})",
            labels={"death_rate_pct": "Death Rate (%)", "location": "Country"},
            color="death_rate_pct",
            color_continuous_scale="reds"
        )
        st.plotly_chart(fig4, use_container_width=True)

st.divider()

# -------------------------
# Monthly Deaths vs Vaccinations (FIXED)
# -------------------------
st.subheader("Monthly Deaths vs Vaccinations (Global)")
with st.spinner("Loading deaths vs vaccinations data..."):
    dv_query = f"""
        SELECT year, month,
               MAX(new_deaths) AS monthly_deaths,
               MAX(new_vaccinations) AS monthly_vaccinations
        FROM datalake_db.processed
        WHERE location = 'World'
        {year_filter}
        GROUP BY year, month
        ORDER BY year, month
    """
    dv_df = run_athena_query(dv_query)
    if not dv_df.empty:
        dv_df["period"] = dv_df["year"] + "-" + dv_df["month"].str.zfill(2)
        dv_df = dv_df.sort_values("period").drop_duplicates(subset=["period"])
        dv_df["monthly_deaths"] = pd.to_numeric(dv_df["monthly_deaths"], errors="coerce")
        dv_df["monthly_vaccinations"] = pd.to_numeric(dv_df["monthly_vaccinations"], errors="coerce")

        fig5 = go.Figure()
        fig5.add_trace(go.Bar(
            x=dv_df["period"],
            y=dv_df["monthly_deaths"],
            name="Monthly Deaths",
            marker_color="red",
            opacity=0.7
        ))
        fig5.add_trace(go.Scatter(
            x=dv_df["period"],
            y=dv_df["monthly_vaccinations"],
            name="Monthly Vaccinations",
            line=dict(color="blue", width=2),
            yaxis="y2"
        ))
        fig5.update_layout(
            yaxis=dict(title="Monthly Deaths"),
            yaxis2=dict(title="Monthly Vaccinations", overlaying="y", side="right"),
            legend=dict(x=0, y=1),
            barmode="overlay"
        )
        st.plotly_chart(fig5, use_container_width=True)

st.divider()

# -------------------------
# Country Deep Dive (FIXED)
# -------------------------
st.subheader("Country Deep Dive")
with st.spinner("Loading country list..."):
    country_list_query = """
        SELECT DISTINCT location
        FROM datalake_db.processed
        WHERE continent IS NOT NULL
        ORDER BY location
    """
    country_list_df = run_athena_query(country_list_query)
    if not country_list_df.empty:
        selected_country = st.selectbox(
            "Select Country",
            country_list_df["location"].tolist()
        )

        deep_dive_query = f"""
            SELECT year, month,
                   MAX(total_cases) AS total_cases,
                   MAX(total_deaths) AS total_deaths,
                   MAX(people_fully_vaccinated_per_hundred) AS vaccinated_pct
            FROM datalake_db.processed
            WHERE location = '{selected_country}'
            GROUP BY year, month
            ORDER BY year, month
        """
        dd_df = run_athena_query(deep_dive_query)
        if not dd_df.empty:
            dd_df["period"] = dd_df["year"] + "-" + dd_df["month"].str.zfill(2)
            dd_df = dd_df.sort_values("period").drop_duplicates(subset=["period"])
            dd_df["total_cases"] = pd.to_numeric(dd_df["total_cases"], errors="coerce")
            dd_df["total_deaths"] = pd.to_numeric(dd_df["total_deaths"], errors="coerce")
            dd_df["vaccinated_pct"] = pd.to_numeric(dd_df["vaccinated_pct"], errors="coerce")

            dd_col1, dd_col2 = st.columns(2)
            with dd_col1:
                fig6 = go.Figure()
                fig6.add_trace(go.Scatter(
                    x=dd_df["period"],
                    y=dd_df["total_cases"],
                    name="Total Cases",
                    line=dict(color="orange")
                ))
                fig6.add_trace(go.Scatter(
                    x=dd_df["period"],
                    y=dd_df["total_deaths"],
                    name="Total Deaths",
                    line=dict(color="red"),
                    yaxis="y2"
                ))
                fig6.update_layout(
                    title=f"Cases and Deaths: {selected_country}",
                    yaxis=dict(title="Total Cases"),
                    yaxis2=dict(title="Total Deaths", overlaying="y", side="right"),
                    legend=dict(x=0, y=1)
                )
                st.plotly_chart(fig6, use_container_width=True)

            with dd_col2:
                fig7 = px.area(
                    dd_df,
                    x="period",
                    y="vaccinated_pct",
                    title=f"Vaccination Rate: {selected_country}",
                    labels={"vaccinated_pct": "Fully Vaccinated (%)", "period": "Period"}
                )
                st.plotly_chart(fig7, use_container_width=True)

st.caption("Data source: Our World in Data COVID-19 Dataset | Architecture: AWS S3, Glue, Athena")