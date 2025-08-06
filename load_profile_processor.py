"""Module for processing and mapping load profiles"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import List, Dict, Tuple, Optional
from config import INTERVALS_PER_DAY, INTERVAL_MINUTES
from holiday_fetcher_improved import HolidayFetcher

class LoadProfileProcessor:
    def __init__(self, federal_state: str):
        self.federal_state = federal_state
        self.holiday_fetcher = HolidayFetcher(federal_state)
        self.source_profile = None
        self.source_year = None
    
    def parse_load_profile(self, csv_content: str) -> pd.DataFrame:
        """Parse CSV load profile with timestamp and load columns"""
        lines = csv_content.strip().split('\n')
        data = []
        
        for line in lines[1:]:  # Skip header
            parts = line.strip().split(';')
            if len(parts) >= 2:
                timestamp_str = parts[0]
                load_str = parts[1].replace(',', '.')  # Handle German decimal separator
                
                try:
                    timestamp = pd.to_datetime(timestamp_str)
                    load = float(load_str)
                    data.append({'timestamp': timestamp, 'load': load})
                except (ValueError, pd.errors.ParserError):
                    continue
        
        df = pd.DataFrame(data)
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Extract year from first timestamp
        if not df.empty:
            self.source_year = df['timestamp'].iloc[0].year
        
        return df
    
    def chunk_by_days(self, df: pd.DataFrame) -> Dict[date, pd.DataFrame]:
        """Split load profile into daily chunks of 96 intervals"""
        daily_chunks = {}
        
        # Group by date
        df['date'] = df['timestamp'].dt.date
        
        for day, group in df.groupby('date'):
            # Ensure we have 96 intervals
            if len(group) == INTERVALS_PER_DAY:
                daily_chunks[day] = group[['timestamp', 'load']].copy()
        
        return daily_chunks
    
    def categorize_days(self, daily_chunks: Dict[date, pd.DataFrame]) -> Dict[str, List[Tuple[date, pd.DataFrame, str]]]:
        """Categorize each day's load profile by type"""
        categorized = {
            'public_holiday': [],
            'school_holiday': [],
            'weekend': [],
            'normal': []
        }
        
        for day, chunk in daily_chunks.items():
            category, description = self.holiday_fetcher.categorize_date(day, day.year)
            categorized[category].append((day, chunk, description))
        
        return categorized
    
    def map_to_future_year(self, categorized_source: Dict, target_year: int) -> pd.DataFrame:
        """Map categorized load profiles to matching days in target year"""
        result_data = []
        
        # Get target year structure
        target_holidays = self.holiday_fetcher.get_public_holidays(target_year)
        target_school_holidays = self.holiday_fetcher.get_school_holidays(target_year)
        target_weekends = self.holiday_fetcher.get_weekends(target_year)
        
        # Create mapping for each day in target year
        current_date = date(target_year, 1, 1)
        end_date = date(target_year, 12, 31)
        
        while current_date <= end_date:
            category, description = self.holiday_fetcher.categorize_date(current_date, target_year)
            
            # Find matching source profile
            source_chunk = None
            source_info = ""
            
            if category == 'public_holiday':
                # Try to find same holiday in source
                for src_date, chunk, src_desc in categorized_source['public_holiday']:
                    if src_desc == description:
                        source_chunk = chunk
                        source_info = f"Holiday: {description} from {src_date}"
                        break
                # Fallback to any holiday
                if source_chunk is None and categorized_source['public_holiday']:
                    src_date, chunk, src_desc = categorized_source['public_holiday'][0]
                    source_chunk = chunk
                    source_info = f"Holiday: {src_desc} from {src_date}"
            
            elif category == 'school_holiday':
                # Match by holiday type (e.g., summer holidays)
                for src_date, chunk, src_desc in categorized_source['school_holiday']:
                    if src_desc.lower() in description.lower() or description.lower() in src_desc.lower():
                        source_chunk = chunk
                        source_info = f"School holiday: {src_desc} from {src_date}"
                        break
                # Fallback to any school holiday
                if source_chunk is None and categorized_source['school_holiday']:
                    src_date, chunk, src_desc = categorized_source['school_holiday'][0]
                    source_chunk = chunk
                    source_info = f"School holiday: {src_desc} from {src_date}"
            
            elif category == 'weekend':
                # Match by week number
                week_num = current_date.isocalendar()[1]
                for src_date, chunk, src_desc in categorized_source['weekend']:
                    if f"KW{week_num}" in src_desc:
                        source_chunk = chunk
                        source_info = f"Weekend {src_desc} from {src_date}"
                        break
                # Fallback to any weekend
                if source_chunk is None and categorized_source['weekend']:
                    # Use modulo to cycle through available weekends
                    idx = week_num % len(categorized_source['weekend'])
                    src_date, chunk, src_desc = categorized_source['weekend'][idx]
                    source_chunk = chunk
                    source_info = f"Weekend {src_desc} from {src_date}"
            
            else:  # normal day
                # Match by day of week and approximate day of year
                target_doy = current_date.timetuple().tm_yday
                target_dow = current_date.weekday()
                
                best_match = None
                best_diff = float('inf')
                
                for src_date, chunk, _ in categorized_source['normal']:
                    src_doy = src_date.timetuple().tm_yday
                    src_dow = src_date.weekday()
                    
                    if src_dow == target_dow:
                        diff = abs(src_doy - target_doy)
                        if diff < best_diff:
                            best_diff = diff
                            best_match = (src_date, chunk)
                
                if best_match:
                    source_chunk = best_match[1]
                    source_info = f"Normal day from {best_match[0]}"
            
            # Apply the chunk to target date
            if source_chunk is not None:
                for i in range(INTERVALS_PER_DAY):
                    timestamp = datetime.combine(current_date, datetime.min.time()) + timedelta(minutes=i * INTERVAL_MINUTES)
                    load = source_chunk.iloc[i % len(source_chunk)]['load']
                    result_data.append({
                        'timestamp': timestamp,
                        'load': load,
                        'source': source_info
                    })
            
            current_date = pd.Timestamp(current_date) + pd.Timedelta(days=1)
            current_date = current_date.date()
        
        return pd.DataFrame(result_data)
    
    def generate_future_profiles(self, source_df: pd.DataFrame, target_years: List[int]) -> Dict[int, pd.DataFrame]:
        """Generate load profiles for multiple future years"""
        # Chunk source data
        daily_chunks = self.chunk_by_days(source_df)
        categorized_source = self.categorize_days(daily_chunks)
        
        # Generate for each target year
        results = {}
        for year in target_years:
            results[year] = self.map_to_future_year(categorized_source, year)
        
        return results
    
    def export_to_csv(self, df: pd.DataFrame, include_source: bool = True) -> str:
        """Export DataFrame to CSV format with optional source annotations"""
        lines = ['timestamp;load' + (';source' if include_source else '')]
        
        for _, row in df.iterrows():
            timestamp_str = row['timestamp'].strftime('%Y-%m-%d %H:%M')
            load_str = f"{row['load']:.2f}".replace('.', ',')  # German decimal separator
            
            if include_source:
                source = row.get('source', '')
                lines.append(f"{timestamp_str};{load_str};{source}")
            else:
                lines.append(f"{timestamp_str};{load_str}")
        
        return '\n'.join(lines)