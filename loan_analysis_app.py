import streamlit as st
import polars as pl
import pandas as pd
import plotly.express as px
#from datetime import datetime, timedelta
#import pytz
#import plotly.graph_objects as go

# Set page config
st.set_page_config(page_title="Brent Ugoh Streamlit App", page_icon="🧙‍♂", layout="wide")

# Sidebar
with st.sidebar:
    st.header("Author")
    st.write("Brent Ugoh :sunglasses:")

# Main content
st.title("Revenue Analysis and Loan Recommendation for Emerging Businesses.")

st.markdown(f"""
##### ***Evaluating Business Performance for Investment Decisions: A Comparative Analysis of Three-Month Revenue Trends.***
""")
st.text("")
st.text("")
st.text("")

st.subheader("Executive summary", divider=True)

executive_summary = [
    "• HotDiggity has the highest revenue across the 3 month time period at \$21,219.",
    "• LeBelle comes in at second highest in total revenue at \$17,089, which is \$4,130 below HotDiggity.",
    "• Interestingly, LeBelle showed consistent increase in revenue over the time period, with the presence of \nhigh-value transaction and a balanced transaction profile at the top, middle and bottom, which shows \npresence of a robust customer base."
]

for sentence in executive_summary:
    st.write(sentence)

st.write("")
st.write("")
# Load and process data
@st.cache_data
def load_data():
    sales_url = "https://byuistats.github.io/M335/data/sales.csv"
    sales_df = pl.read_csv(sales_url)
    
    clean_sales = (
        sales_df
        .with_columns(pl.col("Time").cast(pl.Datetime))
        .filter(pl.col("Name") != "Missing")
        .filter((pl.col("Time") > datetime(2016, 5, 16, 13, 27, 0)) &
                (pl.col("Time") < datetime(2016, 7, 19, 10, 32, 0)))
    )
    
    total_revenue = (
        clean_sales
        .group_by("Name")
        .agg(pl.sum("Amount").alias("TotalRevenue"))
        .sort("TotalRevenue", descending=True)
        .with_columns(pl.col("TotalRevenue").round(0).cast(pl.Int64))
    )

    # Assuming clean_sales is already a Polars DataFrame
    mst = pytz.timezone('MST')

    clean_sales = clean_sales.with_columns(
        pl.col("Time").dt.replace_time_zone("MST")
    )

    week_revenue = (
        clean_sales.with_columns(
        (pl.col("Time") - pl.duration(days=pl.col("Time").dt.weekday()))
        .dt.truncate("1d")
        .alias("Week")
        )
        .group_by(["Name", "Week"])
        .agg(
        pl.col("Amount").sum().alias("WeeklyRevenue")
        )
        .filter(pl.col("Week") < pl.lit(mst.localize(datetime(2016, 7, 17))))
    )

    max_weekly_revenue = (
        week_revenue.group_by("Name")
        .agg(
        pl.col("WeeklyRevenue").max().alias("MaxWeeklyRevenue")
        )
        .join(week_revenue, on=["Name"], how="inner")
        .filter(pl.col("WeeklyRevenue") == pl.col("MaxWeeklyRevenue"))
        .drop("MaxWeeklyRevenue")
    )
    
    return clean_sales, total_revenue, week_revenue, max_weekly_revenue

# Load data
clean_sales, total_revenue, week_revenue, max_weekly_revenue = load_data()


# Create Plotly bar chart
fig1 = px.bar(
    total_revenue,
    x="Name",
    y="TotalRevenue",
    text="TotalRevenue",
    title="Total Businesses Revenue",
    labels={"TotalRevenue": "Total Revenue ($)"}
)

fig1.update_traces(texttemplate='$%{text:,.0f}',
                    textposition='outside')

fig1.update_layout(
    xaxis_title="",
    yaxis_tickformat='$,',
    width=1000,
    height=600
)

# Display the bar chart in Streamlit
st.plotly_chart(fig1, use_container_width=True)



# Assuming week_revenue and max_weekly_revenue are DataFrames
# Convert to Pandas DataFrames if needed
week_revenue_pd = week_revenue.to_pandas()
week_revenue_pd_sorted = week_revenue_pd.sort_values('Week')

max_weekly_revenue_pd = max_weekly_revenue.to_pandas()

# Create the figure
fig2 = make_subplots()

# Add traces for each business
for name in week_revenue_pd_sorted['Name'].unique():
    df_business = week_revenue_pd_sorted[week_revenue_pd_sorted['Name'] == name]
    fig2.add_trace(
        go.Scatter(
            x=df_business['Week'],
            y=df_business['WeeklyRevenue'],
            mode='lines',
            name=name,
            hovertemplate='%{y:$,.0f}<extra></extra>'
        )
    )

# Add annotations for maximum revenue points
for _, row in max_weekly_revenue_pd.iterrows():
    fig2.add_annotation(
        x=row['Week'],
        y=row['WeeklyRevenue'],
        text=f"${row['WeeklyRevenue']:,.0f}",
        showarrow=False,
        yshift=10,
        font=dict(size=10)
    )

# Customize the layout
fig2.update_layout(
    title='Each business showed period of growth',
    xaxis_title=' ',
    yaxis_title='Revenue ($)',
    legend_title='Business Names',
    width=1000,
    height=600,
    xaxis=dict(
        tickmode='linear',
        dtick=14*24*60*60*1000,  # 14 days in milliseconds
        tickformat='%b %d'
    ),
    yaxis=dict(
        tickprefix='$',
        tickformat=',.'
    ),
    hovermode='x unified'
)

# Show the plot
st.plotly_chart(fig2, use_container_width=True)

st.text("")
st.text("")

st.text("Summary of highest revenue for each business across different time periods.")
# Function to convert Polars DataFrame to Markdown
def df_to_markdown(df: pl.DataFrame) -> str:
    headers = "| " + " | ".join(df.columns) + " |"
    separator = "|" + "|".join(["---" for _ in df.columns]) + "|"
    
    rows = []
    for row in df.rows():
        formatted_row = []
        for i, cell in enumerate(row):
            if df.columns[i] in ["Daily Revenue", "Weekly Revenue", "Monthly Revenue"]:
                formatted_cell = f"${cell:,.0f}"
            else:
                formatted_cell = str(cell)
            formatted_row.append(formatted_cell)
        rows.append("| " + " | ".join(formatted_row) + " |")
    
    return "\n".join([headers, separator] + rows)

# Create a DataFrame with the data
data2 = {
    "Business Names": ["Frozone", "HotDiggity", "LeBelle", "ShortStop", "SplashandDash", "Tacontento"],
    "Daily Revenue": [447, 990, 2102, 582, 882, 1550],
    "Weekly Revenue": [1364, 3086, 4590, 2235, 2056, 31934],
    "Monthly Revenue": [2898, 9343, 7986, 4429, 6444, 6319]
}
df2 = pl.DataFrame(data2)

# Convert the DataFrame to Markdown format
markdown_table = df_to_markdown(df2)

# Display the Markdown table in Streamlit
st.markdown(markdown_table)


st.markdown("""
LeBelle has shown consistent growth over the 3-month periods, having the highest daily and weekly revenue, coming in at \$2,102 and \$4,590. respectively, and a total revenue of \$17,089.

Although HotDiggity has the highest monthly revenue and the highest total revenue, it isn't consistent across other time periods. The difference in the monthly revenue isn't far off from LeBelle, with just a \$1,357 difference.
""")

st.text("")
st.text("")
# Create the boxplot
fig3 = px.box(clean_sales.to_pandas(), x='Name', y='Amount', color='Name',
              title='Distribution of Transaction Values',
              labels={'Amount': 'Transaction Amount', 'Name': ''},
              category_orders={'Name': sorted(clean_sales['Name'].unique())},
              height=700)

# Customize the layout
fig3.update_layout(
    showlegend=False,
    yaxis=dict(
        tickprefix='$',
        tickformat=',.0f',
        range=[-15, 120],
    ),
    xaxis=dict(
        tickmode='array',
        tickvals=list(range(len(clean_sales['Name'].unique()))),
        ticktext=sorted(clean_sales['Name'].unique())
    ),
    margin=dict(b=100),
    template='plotly_white'
)

# Add caption
fig3.add_annotation(
    xref='paper', yref='paper',
    x=0.5, y=-0.2,
    text='Chart 4',
    showarrow=False,
    font=dict(size=10),
    align='center',
)

# Adjust box opacity
for trace in fig3.data:
    trace.marker.opacity = 0.7

# Display the boxplot in Streamlit
st.plotly_chart(fig3, use_container_width=True)


st.text("")

st.header("Conclusion", divider=True)
st.markdown("""
<span style='font-size:20px;font-weight:bold'>Recommendation:</span> Business loan for LeBelle should be approved.
""", unsafe_allow_html=True)

st.markdown("##### **Rationale:**")
st.markdown("""
- Higher median transaction value (~$25) indicates strong revenue potential.

- Tight interquartile range suggests consistent, predictable income.

- Presence of high-value outliers shows capacity for premium sales.

- Balanced transaction profile demonstrates stability with growth potential.
            """)
st.text("")
st.markdown("**LeBelle's** transaction data reveals a robust business model with steady core revenue and opportunities for high-value sales. This combination of consistency and upside potential shows that LeBelle has an extensive selection of products and customers with the ability to bring in a lot of money. This will lead to them being able to repay the loan the quickest, and makes LeBelle the most attractive candidate for a business loan among the companies analyzed.")

st.markdown("***Note: Additional financial and operational data should be reviewed to confirm this assessment as this recommendation is based solely on transaction amounts.***")
