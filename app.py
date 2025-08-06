"""Streamlit app for load profile simulation"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import io
from config import FEDERAL_STATES
from load_profile_processor import LoadProfileProcessor

st.set_page_config(
    page_title="Load Profile Simulator",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Load Profile Simulator")
st.markdown("""
This tool simulates load profiles for future years by intelligently mapping historical patterns 
based on holidays, school holidays, and weekends.
""")

# Initialize session state
if 'processor' not in st.session_state:
    st.session_state.processor = None
if 'source_df' not in st.session_state:
    st.session_state.source_df = None
if 'results' not in st.session_state:
    st.session_state.results = {}

# Sidebar for inputs
with st.sidebar:
    st.header("Configuration")
    
    # Federal state selection
    state_code = st.selectbox(
        "Select Federal State",
        options=list(FEDERAL_STATES.keys()),
        format_func=lambda x: f"{x} - {FEDERAL_STATES[x]}",
        help="Choose the German federal state for holiday calculations"
    )
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Load Profile CSV",
        type=['csv', 'txt'],
        help="CSV format: timestamp;load (with 96 intervals per day)"
    )
    
    # Year selection
    current_year = datetime.now().year
    target_years = st.multiselect(
        "Select Target Years",
        options=list(range(current_year, current_year + 10)),
        default=[current_year + 1],
        help="Choose which years to simulate"
    )
    
    # Process button
    process_button = st.button("🚀 Generate Simulations", type="primary", use_container_width=True)

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 Source Load Profile")
    
    if uploaded_file is not None:
        try:
            # Read and parse file
            content = uploaded_file.read().decode('utf-8')
            processor = LoadProfileProcessor(state_code)
            source_df = processor.parse_load_profile(content)
            
            if not source_df.empty:
                st.session_state.processor = processor
                st.session_state.source_df = source_df
                
                # Display statistics
                st.success(f"✅ Loaded {len(source_df)} data points from year {processor.source_year}")
                
                # Show preview
                with st.expander("Preview Source Data"):
                    st.dataframe(source_df.head(96), use_container_width=True)
                
                # Plot source profile
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=source_df['timestamp'],
                    y=source_df['load'],
                    mode='lines',
                    name='Load',
                    line=dict(color='blue', width=1)
                ))
                fig.update_layout(
                    title=f"Source Load Profile ({processor.source_year})",
                    xaxis_title="Timestamp",
                    yaxis_title="Load",
                    height=400,
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("⚠️ No valid data found in file")
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
    else:
        st.info("👆 Please upload a load profile CSV file")

with col2:
    st.subheader("🔮 Simulated Profiles")
    
    if process_button and st.session_state.processor and st.session_state.source_df is not None:
        if not target_years:
            st.warning("⚠️ Please select at least one target year")
        else:
            with st.spinner("Generating simulations..."):
                try:
                    # Generate future profiles
                    results = st.session_state.processor.generate_future_profiles(
                        st.session_state.source_df,
                        target_years
                    )
                    st.session_state.results = results
                    
                    st.success(f"✅ Generated profiles for {len(results)} years")
                    
                    # Display results for each year
                    for year, df in results.items():
                        with st.expander(f"Year {year}", expanded=True):
                            # Statistics
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Data Points", len(df))
                            with col_b:
                                st.metric("Avg Load", f"{df['load'].mean():.2f}")
                            with col_c:
                                st.metric("Peak Load", f"{df['load'].max():.2f}")
                            
                            # Download button
                            csv_content = st.session_state.processor.export_to_csv(df, include_source=True)
                            st.download_button(
                                label=f"📥 Download {year} Profile",
                                data=csv_content,
                                file_name=f"load_profile_{year}_simulated.csv",
                                mime="text/csv"
                            )
                    
                except Exception as e:
                    st.error(f"❌ Error generating simulations: {str(e)}")
    
    elif st.session_state.results:
        # Show previous results
        st.info(f"📊 Showing results for years: {', '.join(map(str, st.session_state.results.keys()))}")
        
        # Combined plot
        fig = go.Figure()
        colors = ['green', 'red', 'purple', 'orange', 'brown']
        
        for idx, (year, df) in enumerate(st.session_state.results.items()):
            # Sample data for visualization (show first week)
            sample_df = df.head(96 * 7)
            fig.add_trace(go.Scatter(
                x=sample_df['timestamp'],
                y=sample_df['load'],
                mode='lines',
                name=str(year),
                line=dict(color=colors[idx % len(colors)], width=1)
            ))
        
        fig.update_layout(
            title="Simulated Load Profiles (First Week)",
            xaxis_title="Timestamp",
            yaxis_title="Load",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Download buttons for each year
        for year, df in st.session_state.results.items():
            csv_content = st.session_state.processor.export_to_csv(df, include_source=True)
            st.download_button(
                label=f"📥 Download {year} Profile",
                data=csv_content,
                file_name=f"load_profile_{year}_simulated.csv",
                mime="text/csv",
                key=f"download_{year}"
            )
    else:
        st.info("👈 Configure and process to see simulations")

# Footer
st.markdown("---")
st.markdown("""
### How it works:
1. **Upload** your historical load profile (CSV with timestamp and load columns)
2. **Select** your federal state for accurate holiday data
3. **Choose** target years for simulation
4. **Generate** realistic future load profiles that preserve seasonal patterns
5. **Download** annotated CSV files with source information

The tool maps holidays, school holidays, and weekends from your historical data to the corresponding 
dates in future years, ensuring realistic load patterns.
""")

# Example CSV format
with st.expander("📋 Example CSV Format"):
    st.code("""timestamp;load
2025-01-01 00:00;1039,44
2025-01-01 00:15;1016,96
2025-01-01 00:30;1031,84
2025-01-01 00:45;972,96
...
""", language='csv')