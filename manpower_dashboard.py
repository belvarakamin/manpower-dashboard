import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Man Power Cost Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stMetric {background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
    h1 {color: #1f2937; font-weight: 700;}
    h2, h3 {color: #374151; font-weight: 600;}
    </style>
""", unsafe_allow_html=True)

# AUTHENTICATION
def check_auth():
    """Check if user is authenticated"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.markdown("""
        <div style='display: flex; justify-content: center; align-items: center; height: 80vh;'>
            <div style='background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 400px;'>
                <h2 style='text-align: center; margin-bottom: 20px;'>🔐 Login</h2>
                <p style='text-align: center; color: #6b7280; margin-bottom: 30px;'>Please enter your credentials to access the dashboard</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                # Simple authentication (you can replace this with your actual authentication logic)
                if email == "admin@example.com" and password == "admin123":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid email or password. Please try again.")
                    st.info("Default credentials: admin@example.com / admin123")
        
        return False
    return True

# Check authentication before proceeding
if not check_auth():
    st.stop()

# CONFIGURATION
SHEET_ID = "1k1hQsLcO1dtG1ENtULgJrgjMyXx3z_ONOtKY4Ag1TR4"
SHEET_GIDS = {
    "Employees": 613206813,
    "Salary_Growth": 1085376893,
    "Projects": 932391633,
    "Manpower_Cost_Per_Project": 1316058601,
    "Manpower_Allocation": 1938083475,
    "Project_PnL": 329914575
}

# Session state
if 'selected_projects' not in st.session_state:
    st.session_state.selected_projects = None
if 'selected_teams' not in st.session_state:
    st.session_state.selected_teams = None
if 'date_range' not in st.session_state:
    st.session_state.date_range = None
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None
if 'selected_status' not in st.session_state:
    st.session_state.selected_status = None

@st.cache_data(ttl=600, show_spinner=False)
def load_sheet(sheet_name, gid):
    """Load and properly parse data from Google Sheets"""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        
        # Parse numeric columns
        for col in df.columns:
            if col not in ['Employee Name', 'Project Name', 'Role', 'Team', 'Category', 'Status', 'Status Allocation', 'Employee_id', 'Employee Id']:
                try:
                    if df[col].dtype == 'object':
                        df[col] = df[col].astype(str).str.replace('Rp', '', regex=False)
                        df[col] = df[col].str.replace('.', '', regex=False)
                        df[col] = df[col].str.replace(',', '', regex=False)
                        df[col] = df[col].str.replace('%', '', regex=False)
                        df[col] = df[col].str.strip()
                        converted = pd.to_numeric(df[col], errors='coerce')
                        if not converted.isna().all():
                            df[col] = converted
                except:
                    pass
        
        # Parse date columns
        date_cols = ['Start Date', 'End Date', 'Month', 'Growth Month', 'Month_Key', 'month', 'Join Date']
        for col in date_cols:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except:
                    pass
        
        return df
    except Exception as e:
        st.error(f"Error loading {sheet_name}: {str(e)}")
        return pd.DataFrame()

def format_currency(value):
    """Format as Rupiah"""
    if pd.isna(value) or value == 0:
        return "Rp 0"
    return f"Rp {value:,.0f}".replace(",", ".")

def find_col(df, names):
    """Find column by multiple possible names (case-insensitive)"""
    if df.empty:
        return None
    df_cols_lower = {col.lower(): col for col in df.columns}
    for name in names:
        if name.lower() in df_cols_lower:
            return df_cols_lower[name.lower()]
    return None

def apply_filters(df, date_col=None):
    """Apply filters to dataframe"""
    if df.empty:
        return pd.DataFrame()
    
    filtered_df = df.copy()
    
    # Date filter
    if st.session_state.date_range and date_col and date_col in filtered_df.columns:
        if pd.api.types.is_datetime64_any_dtype(filtered_df[date_col]):
            start_date, end_date = st.session_state.date_range
            mask = (filtered_df[date_col] >= pd.Timestamp(start_date)) & (filtered_df[date_col] <= pd.Timestamp(end_date))
            filtered_df = filtered_df[mask]
    
    # Project filter
    if st.session_state.selected_projects and 'Project Name' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Project Name'] == st.session_state.selected_projects]
    
    # Team filter  
    if st.session_state.selected_teams and 'Team' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Team'] == st.session_state.selected_teams]
    
    # Category filter
    if st.session_state.selected_category and 'Category' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Category'] == st.session_state.selected_category]
    
    # Status filter
    if st.session_state.selected_status and 'Status' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Status'] == st.session_state.selected_status]
    
    return filtered_df

def main():
    # Add logout button in sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.rerun()
    
    st.title("📊 Man Power Cost Analysis Dashboard")
    st.markdown("Real-time insights into employee allocation, project costs, and profitability")
    st.markdown(f"**Data Last Update:** {datetime.now().strftime('%b %d, %Y, %I:%M:%S %p')}")
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading data from Google Sheets..."):
        employees_df = load_sheet("Employees", SHEET_GIDS["Employees"])
        salary_growth_df = load_sheet("Salary_Growth", SHEET_GIDS["Salary_Growth"])
        projects_df = load_sheet("Projects", SHEET_GIDS["Projects"])
        manpower_cost_df = load_sheet("Manpower_Cost_Per_Project", SHEET_GIDS["Manpower_Cost_Per_Project"])
        manpower_allocation_df = load_sheet("Manpower_Allocation", SHEET_GIDS["Manpower_Allocation"])
        project_pnl_df = load_sheet("Project_PnL", SHEET_GIDS["Project_PnL"])
    
    if project_pnl_df.empty:
        st.error("⚠️ Unable to load data. Make sure spreadsheet is public!")
        st.stop()
    
    # Detect column names
    pnl_month_col = find_col(project_pnl_df, ['Month', 'month', 'Date'])
    pnl_revenue_col = find_col(project_pnl_df, ['Revenue', 'revenue'])
    pnl_cost_col = find_col(project_pnl_df, ['Man Power Cost', 'man power cost', 'Cost', 'cost'])
    pnl_pnl_col = find_col(project_pnl_df, ['PnL', 'pnl', 'P&L'])
    proj_name_col = find_col(project_pnl_df, ['Project Name', 'project name'])
    status_col = find_col(project_pnl_df, ['Status', 'status'])
    category_col = find_col(project_pnl_df, ['Category', 'category'])
    margin_col = find_col(project_pnl_df, ['Margin', 'margin'])
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # 1. Date range filter
    if pnl_month_col and pd.api.types.is_datetime64_any_dtype(project_pnl_df[pnl_month_col]):
        min_date = project_pnl_df[pnl_month_col].min().date()
        max_date = project_pnl_df[pnl_month_col].max().date()
        
        date_range = st.sidebar.date_input(
            "📅 Select Date Range",
            value=(min_date, max_date) if st.session_state.date_range is None else st.session_state.date_range,
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            st.session_state.date_range = date_range
    
    # 2. Project filter
    if proj_name_col:
        projects = ["All Projects"] + sorted(project_pnl_df[proj_name_col].dropna().unique().tolist())
        selected_proj = st.sidebar.selectbox("📊 Select Project", projects)
        st.session_state.selected_projects = None if selected_proj == "All Projects" else selected_proj
    
    # 3. Category filter
    if category_col:
        categories = ["All Categories"] + sorted(project_pnl_df[category_col].dropna().unique().tolist())
        selected_cat = st.sidebar.selectbox("📂 Select Category", categories)
        st.session_state.selected_category = None if selected_cat == "All Categories" else selected_cat
    
    # 4. Status filter
    if status_col:
        statuses = ["All Status"] + sorted(project_pnl_df[status_col].dropna().unique().tolist())
        selected_stat = st.sidebar.selectbox("✅ Select Status", statuses)
        st.session_state.selected_status = None if selected_stat == "All Status" else selected_stat
    
    # Reset button
    if st.sidebar.button("🔄 Reset All Filters"):
        st.session_state.selected_projects = None
        st.session_state.selected_teams = None
        st.session_state.selected_category = None
        st.session_state.selected_status = None
        st.session_state.date_range = None
        st.rerun()
    
    # Apply filters
    filtered_pnl_df = apply_filters(project_pnl_df, pnl_month_col)
    filtered_cost_df = apply_filters(manpower_cost_df, find_col(manpower_cost_df, ['Month_Key', 'Month']))
    filtered_allocation_df = apply_filters(manpower_allocation_df, find_col(manpower_allocation_df, ['Month_Key', 'Month']))
    filtered_salary_df = apply_filters(salary_growth_df, find_col(salary_growth_df, ['Growth Month', 'Month']))
    
    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_revenue = filtered_pnl_df[pnl_revenue_col].sum() if pnl_revenue_col and not filtered_pnl_df.empty else 0
        st.metric("💰 Total Revenue", format_currency(total_revenue))
    
    with col2:
        total_cost = filtered_pnl_df[pnl_cost_col].sum() if pnl_cost_col and not filtered_pnl_df.empty else 0
        st.metric("💼 Total Man Power Cost", format_currency(total_cost))
    
    with col3:
        total_pnl = filtered_pnl_df[pnl_pnl_col].sum() if pnl_pnl_col and not filtered_pnl_df.empty else 0
        st.metric("📈 Total P&L", format_currency(total_pnl))
    
    with col4:
        active_employees = len(employees_df) if not employees_df.empty else 0
        st.metric("👥 Active Employees", active_employees)
    
    st.markdown("---")
    
    # TABS untuk setiap chart
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📅 Timeline", 
        "📈 Time Series", 
        "🎯 Profitability", 
        "🥧 Cost Breakdown",
        "📊 P&L Summary",
        "👥 Allocation",
        "💰 Compensation"
    ])
    
    # TAB 1: PROJECT TIMELINE
    with tab1:
        st.subheader("📅 Project Timeline")
        
        start_col = find_col(projects_df, ['Start Date', 'start date'])
        end_col = find_col(projects_df, ['End Date', 'end date'])
        proj_col = find_col(projects_df, ['Project Name', 'project name'])
        
        if start_col and end_col and proj_col and not projects_df.empty:
            timeline_df = projects_df[[proj_col, start_col, end_col]].dropna().sort_values(start_col)
            
            if not timeline_df.empty:
                fig_timeline = go.Figure()
                colors = px.colors.qualitative.Set3
                
                for idx, row in timeline_df.iterrows():
                    duration = row[end_col] - row[start_col]
                    fig_timeline.add_trace(go.Bar(
                        name=row[proj_col],
                        x=[duration],
                        y=[row[proj_col]],
                        orientation='h',
                        base=row[start_col],
                        marker=dict(color=colors[idx % len(colors)]),
                        showlegend=False
                    ))
                
                fig_timeline.update_layout(
                    height=max(400, len(timeline_df) * 30),
                    margin=dict(l=0, r=0, t=10, b=0),
                    plot_bgcolor='white',
                    xaxis_title="Timeline"
                )
                
                st.plotly_chart(fig_timeline, use_container_width=True)
            else:
                st.info("No timeline data available")
        else:
            st.warning("Missing required columns for timeline chart")
    
    # TAB 2: TIME SERIES
    with tab2:
        st.subheader("📈 Time Series Analysis")
        
        if pnl_month_col and pnl_revenue_col and pnl_cost_col and pnl_pnl_col and not filtered_pnl_df.empty:
            time_series = filtered_pnl_df.groupby(pnl_month_col).agg({
                pnl_revenue_col: 'sum',
                pnl_cost_col: 'sum',
                pnl_pnl_col: 'sum'
            }).reset_index()
            
            fig_ts = go.Figure()
            
            # Revenue - solid green
            fig_ts.add_trace(go.Scatter(
                x=time_series[pnl_month_col], 
                y=time_series[pnl_revenue_col],
                name='Revenue', 
                mode='lines+markers',
                line=dict(color='#10b981', width=3)
            ))
            
            # Cost - dashed orange
            fig_ts.add_trace(go.Scatter(
                x=time_series[pnl_month_col], 
                y=time_series[pnl_cost_col],
                name='Man Power Cost', 
                mode='lines+markers',
                line=dict(color='#f59e0b', width=3, dash='dash')
            ))
            
            # P&L - solid blue
            fig_ts.add_trace(go.Scatter(
                x=time_series[pnl_month_col], 
                y=time_series[pnl_pnl_col],
                name='Project P&L', 
                mode='lines+markers',
                line=dict(color='#3b82f6', width=3)
            ))
            
            fig_ts.update_layout(
                height=500,
                hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=0, r=0, t=30, b=0),
                plot_bgcolor='white'
            )
            
            fig_ts.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#e5e7eb')
            fig_ts.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#e5e7eb')
            
            st.plotly_chart(fig_ts, use_container_width=True)
        else:
            st.warning("Missing required columns for time series chart")
    
    # TAB 3: PROFITABILITY MATRIX
    with tab3:
        st.subheader("🎯 Project Profitability Matrix")
        
        if pnl_pnl_col and pnl_revenue_col and pnl_cost_col and status_col and not filtered_pnl_df.empty:
            bubble_df = filtered_pnl_df[[proj_name_col, pnl_pnl_col, pnl_revenue_col, pnl_cost_col, status_col]].dropna()
            
            if not bubble_df.empty:
                fig_bubble = px.scatter(
                    bubble_df,
                    x=pnl_pnl_col, 
                    y=pnl_revenue_col,
                    size=pnl_cost_col,
                    color=status_col,
                    hover_name=proj_name_col,
                    color_discrete_map={'Profitable': '#10b981', 'Loss': '#ef4444'},
                    size_max=60
                )
                
                fig_bubble.update_layout(
                    height=600,
                    margin=dict(l=0, r=0, t=30, b=0),
                    plot_bgcolor='white'
                )
                
                fig_bubble.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#e5e7eb', zeroline=True, zerolinecolor='#9ca3af')
                fig_bubble.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#e5e7eb')
                
                st.plotly_chart(fig_bubble, use_container_width=True)
            else:
                st.info("No profitability data available")
        else:
            st.warning("Missing required columns for profitability matrix")
    
    # TAB 4: COST BREAKDOWN
    with tab4:
        st.subheader("🥧 Cost Breakdown by Team")
        
        team_col = find_col(filtered_cost_df, ['Team', 'team'])
        cost_col = find_col(filtered_cost_df, ['Cost', 'cost'])
        
        if team_col and cost_col and not filtered_cost_df.empty:
            team_cost = filtered_cost_df.groupby(team_col)[cost_col].sum().reset_index().dropna()
            team_cost = team_cost.sort_values(cost_col, ascending=False)
            
            if not team_cost.empty:
                fig_donut = go.Figure(data=[go.Pie(
                    labels=team_cost[team_col],
                    values=team_cost[cost_col],
                    hole=0.5,
                    marker=dict(colors=px.colors.qualitative.Set2),
                    textinfo='label+percent'
                )])
                
                fig_donut.update_layout(
                    height=500,
                    showlegend=True,
                    margin=dict(l=0, r=0, t=30, b=0)
                )
                
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info("No cost data available")
        else:
            st.warning("Missing required columns for cost breakdown")
    
    # TAB 5: P&L SUMMARY TABLE
    with tab5:
        st.subheader("📊 Project P&L Summary")
        
        if not filtered_pnl_df.empty and all([proj_name_col, pnl_pnl_col, pnl_cost_col, pnl_revenue_col]):
            summary_cols = [proj_name_col, category_col, status_col, pnl_pnl_col, pnl_cost_col, pnl_revenue_col, margin_col]
            summary_cols = [c for c in summary_cols if c]
            
            summary_df = filtered_pnl_df[summary_cols].copy()
            
            # Calculate grand total
            total_pnl_val = summary_df[pnl_pnl_col].sum()
            total_cost_val = summary_df[pnl_cost_col].sum()
            total_revenue_val = summary_df[pnl_revenue_col].sum()
            total_margin_val = (total_pnl_val / total_revenue_val * 100) if total_revenue_val > 0 else 0
            
            # Format display
            display_df = summary_df.copy()
            display_df[pnl_pnl_col] = summary_df[pnl_pnl_col].apply(format_currency)
            display_df[pnl_cost_col] = summary_df[pnl_cost_col].apply(format_currency)
            display_df[pnl_revenue_col] = summary_df[pnl_revenue_col].apply(format_currency)
            if margin_col:
                display_df[margin_col] = summary_df[margin_col].apply(lambda x: f"{x:.2f}%")
            
            # Add grand total
            grand_total = {
                proj_name_col: "GRAND TOTAL",
                pnl_pnl_col: format_currency(total_pnl_val),
                pnl_cost_col: format_currency(total_cost_val),
                pnl_revenue_col: format_currency(total_revenue_val),
            }
            
            if category_col:
                grand_total[category_col] = f"{summary_df[category_col].nunique()} Categories"
            if status_col:
                grand_total[status_col] = f"{summary_df[status_col].nunique()} Status"
            if margin_col:
                grand_total[margin_col] = f"{total_margin_val:.2f}%"
            
            grand_total_df = pd.DataFrame([grand_total])
            display_df = pd.concat([display_df, grand_total_df], ignore_index=True)
            
            st.dataframe(display_df, use_container_width=True, height=600)
        else:
            st.warning("Missing required columns for P&L summary")
    
    # TAB 6: EMPLOYEE ALLOCATION
    with tab6:
        st.subheader("👥 Employee Cost Allocation")
        
        if not filtered_allocation_df.empty:
            emp_name_col = find_col(filtered_allocation_df, ['Employee Name', 'employee name'])
            role_col = find_col(filtered_allocation_df, ['Role', 'role'])
            alloc_proj_col = find_col(filtered_allocation_df, ['Allocation per project', 'allocation per project'])
            total_alloc_col = find_col(filtered_allocation_df, ['Total Allocation', 'total allocation'])
            total_cost_col = find_col(filtered_allocation_df, ['Total Cost', 'total cost'])
            
            if emp_name_col:
                st.dataframe(filtered_allocation_df.head(50), use_container_width=True, height=600)
            else:
                st.warning("Missing required columns for allocation table")
        else:
            st.info("No allocation data available")
    
# TAB 7: COMPENSATION
    with tab7:
        st.subheader("💰 Employee Compensation & Benefit Structure")
        
        if not filtered_salary_df.empty:
            # Identify all columns
            groupby_cols = []
            for col_name in ['Employee Name', 'Employee_id', 'Employee Id', 'Role', 'Team']:
                if col_name in filtered_salary_df.columns:
                    groupby_cols.append(col_name)
            
            # Identify numeric columns for aggregation
            exclude_cols = ['Employee Name', 'Employee_id', 'Employee Id', 'Role', 'Team', 
                          'Growth Month', 'Month', 'Date', 'month', 'Join Date']
            
            numeric_cols = []
            for col in filtered_salary_df.columns:
                if col not in exclude_cols and pd.api.types.is_numeric_dtype(filtered_salary_df[col]):
                    numeric_cols.append(col)
            
            # TAHAP 1: Get MAX values per employee for numeric columns
            if groupby_cols and numeric_cols:
                # Group by employee and get max for numeric, first for categorical
                agg_dict = {}
                for col in numeric_cols:
                    agg_dict[col] = 'max'
                
                # Add non-groupby categorical columns
                for col in ['Role', 'Team']:
                    if col in filtered_salary_df.columns and col not in groupby_cols:
                        agg_dict[col] = 'first'
                
                employee_max = filtered_salary_df.groupby('Employee Name', as_index=False).agg(agg_dict)
                
                # TAHAP 2: Calculate Grand Total (SUM of all MAX values)
                grand_total = {'Employee Name': 'GRAND TOTAL'}
                
                # Add categorical columns to grand total
                if 'Employee_id' in employee_max.columns or 'Employee Id' in employee_max.columns:
                    grand_total[find_col(employee_max, ['Employee_id', 'Employee Id']) or 'Employee Id'] = '-'
                if 'Role' in employee_max.columns:
                    grand_total['Role'] = f"{employee_max['Role'].nunique()} Roles"
                if 'Team' in employee_max.columns:
                    grand_total['Team'] = f"{employee_max['Team'].nunique()} Teams"
                
                # Calculate sum for numeric columns
                numeric_totals = {}
                for col in numeric_cols:
                    numeric_totals[col] = employee_max[col].sum()
                    grand_total[col] = numeric_totals[col]
                
                # Create display dataframe with formatting
                display_comp_df = employee_max.copy()
                
                # Format numeric columns
                for col in numeric_cols:
                    if 'Growth' in col or '%' in col or 'growth' in col.lower():
                        # Format as percentage
                        display_comp_df[col] = employee_max[col].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "0.00%")
                        grand_total[col] = f"{numeric_totals[col] / len(employee_max):.2f}%" if len(employee_max) > 0 else "0.00%"
                    else:
                        # Format as currency
                        display_comp_df[col] = employee_max[col].apply(lambda x: format_currency(x) if pd.notna(x) else "Rp 0")
                        grand_total[col] = format_currency(numeric_totals[col])
                
                # Add grand total row
                grand_total_df = pd.DataFrame([grand_total])
                display_comp_df = pd.concat([display_comp_df, grand_total_df], ignore_index=True)
                
                st.dataframe(display_comp_df, use_container_width=True, height=600)
                
                # Show summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("👥 Unique Employees", len(employee_max))
                with col2:
                    total_cost_col = find_col(employee_max, ['Total Cost', 'total cost'])
                    if total_cost_col:
                        st.metric("💰 Total Compensation Cost", format_currency(numeric_totals.get(total_cost_col, 0)))
                with col3:
                    current_sal_col = find_col(employee_max, ['Current Salary', 'current salary', 'Salary'])
                    if current_sal_col:
                        avg_salary = numeric_totals.get(current_sal_col, 0) / len(employee_max) if len(employee_max) > 0 else 0
                        st.metric("📊 Average Salary", format_currency(avg_salary))
            else:
                st.dataframe(filtered_salary_df.head(50), use_container_width=True, height=600)
        else:
            st.info("No compensation data available")
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #6b7280; padding: 20px;'>
            <p>Dashboard created with Streamlit | Data synced from Google Sheets</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()