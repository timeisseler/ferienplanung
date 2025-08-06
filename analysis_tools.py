"""Analysis and validation tools for load profile simulation"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
from config import INTERVALS_PER_DAY

class LoadProfileAnalyzer:
    """Analyze and validate load profiles"""
    
    def __init__(self):
        self.metrics = {}
        
    def calculate_statistics(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive statistics for a load profile"""
        stats = {
            'mean': df['load'].mean(),
            'median': df['load'].median(),
            'std': df['load'].std(),
            'min': df['load'].min(),
            'max': df['load'].max(),
            'peak_to_average': df['load'].max() / df['load'].mean(),
            'load_factor': df['load'].mean() / df['load'].max(),
            'total_energy': df['load'].sum() * 0.25,  # kWh assuming 15-min intervals
            'cv': df['load'].std() / df['load'].mean() * 100  # Coefficient of variation
        }
        return stats
    
    def calculate_daily_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract daily load patterns"""
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['date'] = df['timestamp'].dt.date
        
        # Average hourly pattern
        hourly_pattern = df.groupby('hour')['load'].agg(['mean', 'std'])
        
        # Weekday vs Weekend patterns
        df['is_weekend'] = df['day_of_week'].isin([5, 6])
        weekday_pattern = df[~df['is_weekend']].groupby('hour')['load'].mean()
        weekend_pattern = df[df['is_weekend']].groupby('hour')['load'].mean()
        
        return hourly_pattern, weekday_pattern, weekend_pattern
    
    def calculate_seasonal_patterns(self, df: pd.DataFrame) -> Dict:
        """Calculate seasonal load characteristics"""
        df['month'] = df['timestamp'].dt.month
        df['season'] = df['month'].apply(self._get_season)
        
        seasonal_stats = {}
        for season in ['Winter', 'Spring', 'Summer', 'Fall']:
            season_data = df[df['season'] == season]['load']
            if not season_data.empty:
                seasonal_stats[season] = {
                    'mean': season_data.mean(),
                    'peak': season_data.max(),
                    'valley': season_data.min(),
                    'std': season_data.std()
                }
        
        return seasonal_stats
    
    def _get_season(self, month: int) -> str:
        """Get season from month"""
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:
            return 'Fall'
    
    def detect_anomalies(self, df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
        """Detect anomalies using z-score method"""
        df['z_score'] = np.abs(stats.zscore(df['load']))
        df['is_anomaly'] = df['z_score'] > threshold
        
        anomalies = df[df['is_anomaly']].copy()
        return anomalies
    
    def compare_profiles(self, source_df: pd.DataFrame, simulated_df: pd.DataFrame) -> Dict:
        """Compare source and simulated profiles"""
        comparison = {}
        
        # Statistical comparison
        source_stats = self.calculate_statistics(source_df)
        simulated_stats = self.calculate_statistics(simulated_df)
        
        comparison['statistics'] = {
            'source': source_stats,
            'simulated': simulated_stats,
            'differences': {
                key: {
                    'absolute': simulated_stats[key] - source_stats[key],
                    'relative': ((simulated_stats[key] - source_stats[key]) / source_stats[key] * 100) if source_stats[key] != 0 else 0
                }
                for key in source_stats.keys()
            }
        }
        
        # Pattern correlation
        if len(source_df) == len(simulated_df):
            correlation = np.corrcoef(source_df['load'], simulated_df['load'])[0, 1]
            comparison['correlation'] = correlation
        
        # Load duration curve comparison
        source_ldc = np.sort(source_df['load'])[::-1]
        simulated_ldc = np.sort(simulated_df['load'])[::-1]
        
        comparison['load_duration'] = {
            'source_percentiles': np.percentile(source_ldc, [10, 25, 50, 75, 90]),
            'simulated_percentiles': np.percentile(simulated_ldc, [10, 25, 50, 75, 90])
        }
        
        return comparison
    
    def validate_mapping(self, simulated_df: pd.DataFrame) -> Dict:
        """Validate the quality of day-type mapping"""
        validation = {
            'holiday_consistency': True,
            'weekend_pattern_preserved': True,
            'seasonal_variation_realistic': True,
            'data_completeness': True,
            'issues': []
        }
        
        # Check data completeness
        expected_points = 365 * INTERVALS_PER_DAY
        actual_points = len(simulated_df)
        if actual_points < expected_points * 0.95:
            validation['data_completeness'] = False
            validation['issues'].append(f"Missing data: {expected_points - actual_points} intervals")
        
        # Check weekend patterns
        simulated_df['day_of_week'] = simulated_df['timestamp'].dt.dayofweek
        weekend_loads = simulated_df[simulated_df['day_of_week'].isin([5, 6])]['load'].mean()
        weekday_loads = simulated_df[~simulated_df['day_of_week'].isin([5, 6])]['load'].mean()
        
        if weekend_loads > weekday_loads * 0.95:
            validation['weekend_pattern_preserved'] = False
            validation['issues'].append("Weekend loads not showing expected reduction")
        
        # Check seasonal variation
        seasonal_stats = self.calculate_seasonal_patterns(simulated_df)
        if seasonal_stats:
            summer_avg = seasonal_stats.get('Summer', {}).get('mean', 0)
            winter_avg = seasonal_stats.get('Winter', {}).get('mean', 0)
            
            if abs(summer_avg - winter_avg) < 50:  # Less than 50 units difference
                validation['seasonal_variation_realistic'] = False
                validation['issues'].append("Insufficient seasonal variation")
        
        validation['overall_score'] = sum([
            validation['holiday_consistency'],
            validation['weekend_pattern_preserved'],
            validation['seasonal_variation_realistic'],
            validation['data_completeness']
        ]) / 4 * 100
        
        return validation

class VisualizationGenerator:
    """Generate enhanced visualizations for load profile analysis"""
    
    @staticmethod
    def create_comparison_plot(source_df: pd.DataFrame, simulated_dfs: Dict[int, pd.DataFrame]) -> go.Figure:
        """Create comprehensive comparison visualization"""
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Daily Average Profiles', 'Weekly Patterns',
                'Load Duration Curves', 'Monthly Averages',
                'Distribution Comparison', 'Seasonal Patterns'
            ),
            vertical_spacing=0.12,
            horizontal_spacing=0.15
        )
        
        # Colors for different years
        colors = ['blue', 'red', 'green', 'purple', 'orange']
        
        # 1. Daily Average Profiles
        source_hourly = source_df.groupby(source_df['timestamp'].dt.hour)['load'].mean()
        fig.add_trace(
            go.Scatter(x=source_hourly.index, y=source_hourly.values,
                      name=f"Source", line=dict(color='blue', width=2)),
            row=1, col=1
        )
        
        for idx, (year, sim_df) in enumerate(simulated_dfs.items()):
            sim_hourly = sim_df.groupby(sim_df['timestamp'].dt.hour)['load'].mean()
            fig.add_trace(
                go.Scatter(x=sim_hourly.index, y=sim_hourly.values,
                          name=f"Simulated {year}", 
                          line=dict(color=colors[idx % len(colors)], dash='dash')),
                row=1, col=1
            )
        
        # 2. Weekly Patterns (show one week)
        source_week = source_df.head(INTERVALS_PER_DAY * 7)
        fig.add_trace(
            go.Scatter(x=list(range(len(source_week))), y=source_week['load'].values,
                      name="Source Week", line=dict(color='blue', width=1)),
            row=1, col=2
        )
        
        for idx, (year, sim_df) in enumerate(simulated_dfs.items()):
            sim_week = sim_df.head(INTERVALS_PER_DAY * 7)
            fig.add_trace(
                go.Scatter(x=list(range(len(sim_week))), y=sim_week['load'].values,
                          name=f"Sim {year} Week",
                          line=dict(color=colors[idx % len(colors)], width=1, dash='dot')),
                row=1, col=2
            )
        
        # 3. Load Duration Curves
        source_ldc = np.sort(source_df['load'].values)[::-1]
        percentages = np.linspace(0, 100, len(source_ldc))
        fig.add_trace(
            go.Scatter(x=percentages, y=source_ldc,
                      name="Source LDC", line=dict(color='blue', width=2)),
            row=2, col=1
        )
        
        for idx, (year, sim_df) in enumerate(simulated_dfs.items()):
            sim_ldc = np.sort(sim_df['load'].values)[::-1]
            sim_percentages = np.linspace(0, 100, len(sim_ldc))
            fig.add_trace(
                go.Scatter(x=sim_percentages, y=sim_ldc,
                          name=f"Sim {year} LDC",
                          line=dict(color=colors[idx % len(colors)], dash='dash')),
                row=2, col=1
            )
        
        # 4. Monthly Averages
        source_monthly = source_df.groupby(source_df['timestamp'].dt.month)['load'].mean()
        fig.add_trace(
            go.Bar(x=source_monthly.index, y=source_monthly.values,
                   name="Source Monthly", marker_color='blue', opacity=0.7),
            row=2, col=2
        )
        
        for idx, (year, sim_df) in enumerate(simulated_dfs.items()):
            sim_monthly = sim_df.groupby(sim_df['timestamp'].dt.month)['load'].mean()
            fig.add_trace(
                go.Bar(x=sim_monthly.index, y=sim_monthly.values,
                       name=f"Sim {year}",
                       marker_color=colors[idx % len(colors)], opacity=0.5),
                row=2, col=2
            )
        
        # 5. Distribution Comparison
        fig.add_trace(
            go.Histogram(x=source_df['load'], name="Source Dist",
                        marker_color='blue', opacity=0.5, nbinsx=50),
            row=3, col=1
        )
        
        for idx, (year, sim_df) in enumerate(simulated_dfs.items()):
            fig.add_trace(
                go.Histogram(x=sim_df['load'], name=f"Sim {year}",
                            marker_color=colors[idx % len(colors)], opacity=0.3, nbinsx=50),
                row=3, col=1
            )
        
        # 6. Seasonal Box Plots
        source_df['season'] = source_df['timestamp'].dt.month.apply(
            lambda m: 'Winter' if m in [12, 1, 2] else 'Spring' if m in [3, 4, 5] 
            else 'Summer' if m in [6, 7, 8] else 'Fall'
        )
        
        for season in ['Winter', 'Spring', 'Summer', 'Fall']:
            season_data = source_df[source_df['season'] == season]['load']
            fig.add_trace(
                go.Box(y=season_data, name=f"{season}", marker_color='blue'),
                row=3, col=2
            )
        
        # Update layout
        fig.update_xaxes(title_text="Hour", row=1, col=1)
        fig.update_xaxes(title_text="Interval", row=1, col=2)
        fig.update_xaxes(title_text="Duration (%)", row=2, col=1)
        fig.update_xaxes(title_text="Month", row=2, col=2)
        fig.update_xaxes(title_text="Load", row=3, col=1)
        fig.update_xaxes(title_text="Season", row=3, col=2)
        
        fig.update_yaxes(title_text="Load", row=1, col=1)
        fig.update_yaxes(title_text="Load", row=1, col=2)
        fig.update_yaxes(title_text="Load", row=2, col=1)
        fig.update_yaxes(title_text="Load", row=2, col=2)
        fig.update_yaxes(title_text="Frequency", row=3, col=1)
        fig.update_yaxes(title_text="Load", row=3, col=2)
        
        fig.update_layout(
            height=1200,
            showlegend=True,
            title_text="Comprehensive Load Profile Analysis",
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def create_pattern_matching_plot(source_df: pd.DataFrame, simulated_df: pd.DataFrame) -> go.Figure:
        """Visualize how well patterns are matched between source and simulation"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Holiday Matching', 'Weekend Pattern Preservation',
                'Peak Load Alignment', 'Valley Load Alignment'
            )
        )
        
        # Add visualizations for pattern matching
        # This would be expanded based on the actual holiday/weekend data
        
        return fig
    
    @staticmethod
    def create_validation_dashboard(validation_results: Dict) -> go.Figure:
        """Create a validation dashboard with metrics and indicators"""
        fig = go.Figure()
        
        # Create gauge chart for overall score
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=validation_results.get('overall_score', 0),
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Validation Score"},
            delta={'reference': 80},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        return fig