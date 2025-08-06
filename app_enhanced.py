"""Enhanced Streamlit app with better visualization and validation"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import io
from config import FEDERAL_STATES
from load_profile_processor import LoadProfileProcessor
from analysis_tools import LoadProfileAnalyzer, VisualizationGenerator

st.set_page_config(
    page_title="Load Profile Simulator - Enhanced",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .validation-pass {
        color: green;
        font-weight: bold;
    }
    .validation-fail {
        color: red;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Load Profile Simulator - Enhanced Analysis")
st.markdown("""
Advanced load profile simulation with comprehensive validation and analysis tools.
""")

# Initialize session state
if 'processor' not in st.session_state:
    st.session_state.processor = None
if 'source_df' not in st.session_state:
    st.session_state.source_df = None
if 'results' not in st.session_state:
    st.session_state.results = {}
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = LoadProfileAnalyzer()
if 'viz_generator' not in st.session_state:
    st.session_state.viz_generator = VisualizationGenerator()

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    state_code = st.selectbox(
        "Select Federal State",
        options=list(FEDERAL_STATES.keys()),
        format_func=lambda x: f"{x} - {FEDERAL_STATES[x]}",
        help="Choose the German federal state for holiday calculations"
    )
    
    uploaded_file = st.file_uploader(
        "Upload Load Profile CSV",
        type=['csv', 'txt'],
        help="CSV format: timestamp;load (with 96 intervals per day)"
    )
    
    current_year = datetime.now().year
    target_years = st.multiselect(
        "Select Target Years",
        options=list(range(current_year, current_year + 10)),
        default=[current_year + 1, current_year + 2],
        help="Choose which years to simulate"
    )
    
    st.divider()
    
    # Advanced Options
    with st.expander("🔧 Advanced Options"):
        show_anomalies = st.checkbox("Show Anomaly Detection", value=True)
        validation_threshold = st.slider("Validation Strictness", 1, 10, 5)
        comparison_mode = st.radio("Comparison Mode", ["Side-by-side", "Overlay", "Difference"])
    
    process_button = st.button("🚀 Generate & Analyze", type="primary", use_container_width=True)

# Main content - create tabs for better organization
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Data Input", 
    "🔮 Simulation Results", 
    "📈 Comparison Analysis",
    "✅ Validation",
    "📋 Reports"
])

with tab1:
    if uploaded_file is not None:
        try:
            content = uploaded_file.read().decode('utf-8')
            processor = LoadProfileProcessor(state_code)
            source_df = processor.parse_load_profile(content)
            
            if not source_df.empty:
                st.session_state.processor = processor
                st.session_state.source_df = source_df
                
                col1, col2, col3, col4 = st.columns(4)
                
                # Display key metrics
                stats = st.session_state.analyzer.calculate_statistics(source_df)
                
                with col1:
                    st.metric("📈 Average Load", f"{stats['mean']:.2f}")
                with col2:
                    st.metric("⚡ Peak Load", f"{stats['max']:.2f}")
                with col3:
                    st.metric("📉 Min Load", f"{stats['min']:.2f}")
                with col4:
                    st.metric("📊 Load Factor", f"{stats['load_factor']:.2%}")
                
                # Source profile visualization
                st.subheader("Source Load Profile Analysis")
                
                # Create subplots for source analysis
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=('Full Year Profile', 'Daily Average Pattern', 
                                  'Weekly Pattern', 'Load Distribution')
                )
                
                # Full year profile
                fig.add_trace(
                    go.Scatter(x=source_df['timestamp'], y=source_df['load'],
                              mode='lines', name='Load', line=dict(color='blue', width=1)),
                    row=1, col=1
                )
                
                # Daily average pattern
                hourly_avg = source_df.groupby(source_df['timestamp'].dt.hour)['load'].mean()
                fig.add_trace(
                    go.Scatter(x=hourly_avg.index, y=hourly_avg.values,
                              mode='lines+markers', name='Hourly Avg',
                              line=dict(color='green', width=2)),
                    row=1, col=2
                )
                
                # Weekly pattern (first week)
                week_data = source_df.head(96 * 7)
                fig.add_trace(
                    go.Scatter(x=list(range(len(week_data))), y=week_data['load'],
                              mode='lines', name='Week Pattern',
                              line=dict(color='purple', width=1)),
                    row=2, col=1
                )
                
                # Load distribution
                fig.add_trace(
                    go.Histogram(x=source_df['load'], nbinsx=50, name='Distribution',
                                marker_color='orange'),
                    row=2, col=2
                )
                
                fig.update_layout(height=700, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
                
                # Data quality check
                st.subheader("📊 Data Quality Check")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    completeness = (len(source_df) / (365 * 96)) * 100
                    st.metric("Data Completeness", f"{completeness:.1f}%",
                             "✅ Good" if completeness > 95 else "⚠️ Check data")
                
                with col2:
                    cv = stats['cv']
                    st.metric("Variability (CV)", f"{cv:.1f}%",
                             "Normal" if 20 < cv < 80 else "Check pattern")
                
                with col3:
                    peak_ratio = stats['peak_to_average']
                    st.metric("Peak/Avg Ratio", f"{peak_ratio:.2f}",
                             "Typical" if 1.5 < peak_ratio < 3 else "Unusual")
                
            else:
                st.error("⚠️ No valid data found in file")
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
    else:
        st.info("👆 Please upload a load profile CSV file to begin")

with tab2:
    if process_button and st.session_state.processor and st.session_state.source_df is not None:
        if not target_years:
            st.warning("⚠️ Please select at least one target year")
        else:
            with st.spinner("🔄 Generating simulations and analyzing patterns..."):
                try:
                    results = st.session_state.processor.generate_future_profiles(
                        st.session_state.source_df,
                        target_years
                    )
                    st.session_state.results = results
                    
                    st.success(f"✅ Successfully generated profiles for {len(results)} years")
                    
                    # Display results for each year
                    for year, df in results.items():
                        with st.expander(f"📅 Year {year} Simulation", expanded=True):
                            # Calculate statistics
                            sim_stats = st.session_state.analyzer.calculate_statistics(df)
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Avg Load", f"{sim_stats['mean']:.2f}",
                                         f"{sim_stats['mean'] - st.session_state.analyzer.calculate_statistics(st.session_state.source_df)['mean']:.2f}")
                            with col2:
                                st.metric("Peak Load", f"{sim_stats['max']:.2f}",
                                         f"{sim_stats['max'] - st.session_state.analyzer.calculate_statistics(st.session_state.source_df)['max']:.2f}")
                            with col3:
                                st.metric("Total Energy", f"{sim_stats['total_energy']:.0f} kWh")
                            with col4:
                                st.metric("Load Factor", f"{sim_stats['load_factor']:.2%}")
                            
                            # Sample visualization
                            st.subheader("Sample Week Comparison")
                            sample_size = 96 * 7
                            
                            fig = go.Figure()
                            
                            # Source sample
                            source_sample = st.session_state.source_df.head(sample_size)
                            fig.add_trace(go.Scatter(
                                x=list(range(len(source_sample))),
                                y=source_sample['load'],
                                mode='lines',
                                name='Source',
                                line=dict(color='blue', width=2)
                            ))
                            
                            # Simulated sample
                            sim_sample = df.head(sample_size)
                            fig.add_trace(go.Scatter(
                                x=list(range(len(sim_sample))),
                                y=sim_sample['load'],
                                mode='lines',
                                name=f'Simulated {year}',
                                line=dict(color='red', width=2, dash='dash')
                            ))
                            
                            fig.update_layout(
                                title="First Week Comparison",
                                xaxis_title="15-min Intervals",
                                yaxis_title="Load",
                                height=400,
                                hovermode='x unified'
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Download button
                            csv_content = st.session_state.processor.export_to_csv(df, include_source=True)
                            st.download_button(
                                label=f"📥 Download {year} Profile with Annotations",
                                data=csv_content,
                                file_name=f"load_profile_{year}_simulated.csv",
                                mime="text/csv",
                                key=f"download_{year}_tab2"
                            )
                            
                except Exception as e:
                    st.error(f"❌ Error generating simulations: {str(e)}")
    
    elif st.session_state.results:
        st.info(f"📊 Showing previous results for: {', '.join(map(str, st.session_state.results.keys()))}")
        for year, df in st.session_state.results.items():
            with st.expander(f"📅 Year {year}"):
                csv_content = st.session_state.processor.export_to_csv(df, include_source=True)
                st.download_button(
                    label=f"📥 Download {year} Profile",
                    data=csv_content,
                    file_name=f"load_profile_{year}_simulated.csv",
                    mime="text/csv",
                    key=f"download_{year}_existing"
                )

with tab3:
    if st.session_state.source_df is not None and st.session_state.results:
        st.header("📊 Comprehensive Comparison Analysis")
        
        # Generate comprehensive comparison
        comparison_fig = st.session_state.viz_generator.create_comparison_plot(
            st.session_state.source_df,
            st.session_state.results
        )
        
        st.plotly_chart(comparison_fig, use_container_width=True)
        
        # Detailed comparison metrics
        st.subheader("📈 Statistical Comparison")
        
        for year, sim_df in st.session_state.results.items():
            comparison = st.session_state.analyzer.compare_profiles(
                st.session_state.source_df,
                sim_df
            )
            
            with st.expander(f"Year {year} Comparison Details"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**Source Statistics**")
                    for key, value in comparison['statistics']['source'].items():
                        st.write(f"{key}: {value:.2f}")
                
                with col2:
                    st.markdown("**Simulated Statistics**")
                    for key, value in comparison['statistics']['simulated'].items():
                        st.write(f"{key}: {value:.2f}")
                
                with col3:
                    st.markdown("**Relative Differences (%)**")
                    for key, diff in comparison['statistics']['differences'].items():
                        color = "green" if abs(diff['relative']) < 10 else "orange" if abs(diff['relative']) < 20 else "red"
                        st.markdown(f"<span style='color:{color}'>{key}: {diff['relative']:.1f}%</span>", 
                                  unsafe_allow_html=True)
                
                if 'correlation' in comparison:
                    st.metric("Pattern Correlation", f"{comparison['correlation']:.3f}",
                             "Good match" if comparison['correlation'] > 0.8 else "Check mapping")
    else:
        st.info("📊 Generate simulations first to see comparison analysis")

with tab4:
    if st.session_state.results:
        st.header("✅ Validation Results")
        
        for year, sim_df in st.session_state.results.items():
            validation = st.session_state.analyzer.validate_mapping(sim_df)
            
            with st.expander(f"Year {year} Validation", expanded=True):
                # Overall score gauge
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    score_color = "green" if validation['overall_score'] > 80 else "orange" if validation['overall_score'] > 60 else "red"
                    st.markdown(f"""
                    <div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px;'>
                        <h1 style='color: {score_color};'>{validation['overall_score']:.0f}%</h1>
                        <p>Overall Validation Score</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**Validation Checks:**")
                    
                    checks = [
                        ("Data Completeness", validation['data_completeness']),
                        ("Weekend Pattern", validation['weekend_pattern_preserved']),
                        ("Seasonal Variation", validation['seasonal_variation_realistic']),
                        ("Holiday Consistency", validation['holiday_consistency'])
                    ]
                    
                    for check_name, passed in checks:
                        if passed:
                            st.markdown(f"✅ {check_name}")
                        else:
                            st.markdown(f"❌ {check_name}")
                    
                    if validation['issues']:
                        st.warning("⚠️ Issues found:")
                        for issue in validation['issues']:
                            st.write(f"• {issue}")
                
                # Anomaly detection
                if show_anomalies:
                    anomalies = st.session_state.analyzer.detect_anomalies(sim_df)
                    if not anomalies.empty:
                        st.subheader("🔍 Anomalies Detected")
                        st.write(f"Found {len(anomalies)} potential anomalies")
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=sim_df['timestamp'],
                            y=sim_df['load'],
                            mode='lines',
                            name='Normal',
                            line=dict(color='blue', width=1)
                        ))
                        fig.add_trace(go.Scatter(
                            x=anomalies['timestamp'],
                            y=anomalies['load'],
                            mode='markers',
                            name='Anomalies',
                            marker=dict(color='red', size=8, symbol='x')
                        ))
                        fig.update_layout(
                            title=f"Anomaly Detection - Year {year}",
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("✅ Generate simulations first to see validation results")

with tab5:
    if st.session_state.source_df is not None and st.session_state.results:
        st.header("📋 Detailed Analysis Report")
        
        # Generate comprehensive report
        report_lines = [
            "# LOAD PROFILE SIMULATION REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Configuration",
            f"- Federal State: {state_code} ({FEDERAL_STATES[state_code]})",
            f"- Source Year: {st.session_state.processor.source_year}",
            f"- Target Years: {', '.join(map(str, target_years))}",
            "",
            "## Source Profile Statistics",
        ]
        
        source_stats = st.session_state.analyzer.calculate_statistics(st.session_state.source_df)
        for key, value in source_stats.items():
            report_lines.append(f"- {key}: {value:.2f}")
        
        report_lines.extend(["", "## Simulation Results"])
        
        for year, sim_df in st.session_state.results.items():
            sim_stats = st.session_state.analyzer.calculate_statistics(sim_df)
            validation = st.session_state.analyzer.validate_mapping(sim_df)
            
            report_lines.extend([
                f"", 
                f"### Year {year}",
                f"- Validation Score: {validation['overall_score']:.1f}%",
                f"- Average Load: {sim_stats['mean']:.2f}",
                f"- Peak Load: {sim_stats['max']:.2f}",
                f"- Load Factor: {sim_stats['load_factor']:.2%}",
                f"- Total Energy: {sim_stats['total_energy']:.0f} kWh"
            ])
            
            if validation['issues']:
                report_lines.append("- Issues:")
                for issue in validation['issues']:
                    report_lines.append(f"  * {issue}")
        
        report_lines.extend([
            "",
            "## Seasonal Analysis",
        ])
        
        seasonal_stats = st.session_state.analyzer.calculate_seasonal_patterns(st.session_state.source_df)
        for season, stats in seasonal_stats.items():
            report_lines.append(f"- {season}: Mean={stats['mean']:.2f}, Peak={stats['peak']:.2f}")
        
        report_content = "\n".join(report_lines)
        
        st.text_area("Report Preview", report_content, height=400)
        
        st.download_button(
            label="📥 Download Full Report",
            data=report_content,
            file_name=f"load_profile_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
        
        # Export all data as Excel
        if st.button("📊 Export All Data to Excel"):
            with pd.ExcelWriter('load_profile_analysis.xlsx', engine='openpyxl') as writer:
                st.session_state.source_df.to_excel(writer, sheet_name='Source Data', index=False)
                for year, df in st.session_state.results.items():
                    df.to_excel(writer, sheet_name=f'Simulated {year}', index=False)
            st.success("✅ Excel file created: load_profile_analysis.xlsx")
    else:
        st.info("📋 Generate simulations first to create reports")

# Footer with tips
st.markdown("---")
with st.expander("💡 Tips for Best Results"):
    st.markdown("""
    - **Data Quality**: Ensure your source data has complete 96 intervals per day
    - **Federal State**: Select the correct state for accurate holiday mapping
    - **Validation Score**: Aim for >80% validation score for reliable simulations
    - **Pattern Preservation**: Check that weekend and seasonal patterns are maintained
    - **Anomaly Detection**: Review detected anomalies to identify potential data issues
    """)