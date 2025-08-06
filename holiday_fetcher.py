"""Module for fetching German holidays and school holidays"""

import requests
from datetime import datetime, date
from typing import Dict, List, Tuple
import pandas as pd
from config import HOLIDAY_API_URL, SCHOOL_HOLIDAY_API_URL

class HolidayFetcher:
    def __init__(self, federal_state: str):
        self.federal_state = federal_state
        self.holidays_cache = {}
        self.school_holidays_cache = {}
    
    def get_public_holidays(self, year: int) -> Dict[str, date]:
        """Fetch public holidays for a specific year and federal state"""
        cache_key = f"{year}_{self.federal_state}"
        if cache_key in self.holidays_cache:
            return self.holidays_cache[cache_key]
        
        try:
            url = f"{HOLIDAY_API_URL}?years={year}&states={self.federal_state.lower()}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            holidays = {}
            data = response.json()
            
            # Parse the new API response format
            if 'feiertage' in data:
                for holiday in data['feiertage']:
                    if str(year) in holiday and self.federal_state.upper() in holiday[str(year)]:
                        for holiday_data in holiday[str(year)][self.federal_state.upper()]:
                            holiday_date = datetime.strptime(holiday_data['datum'], '%Y-%m-%d').date()
                            holidays[holiday_data['fname']] = holiday_date
            else:
                # Try alternative parsing
                for state_data in data:
                    if state_data.get('year') == year and state_data.get('stateCode') == self.federal_state.upper():
                        for holiday_name, holiday_info in state_data.get('holidays', {}).items():
                            if isinstance(holiday_info, dict) and 'date' in holiday_info:
                                holiday_date = datetime.strptime(holiday_info['date'], '%Y-%m-%d').date()
                                holidays[holiday_name] = holiday_date
            
            self.holidays_cache[cache_key] = holidays
            return holidays
        except Exception as e:
            print(f"Error fetching public holidays: {e}")
            return {}
    
    def get_school_holidays(self, year: int) -> List[Tuple[date, date, str]]:
        """Fetch school holidays for a specific year and federal state"""
        cache_key = f"{year}_{self.federal_state}"
        if cache_key in self.school_holidays_cache:
            return self.school_holidays_cache[cache_key]
        
        try:
            url = f"{SCHOOL_HOLIDAY_API_URL}holidays/{self.federal_state}/{year}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            holidays = []
            data = response.json()
            for holiday in data:
                # Handle different date formats from the API
                start_str = holiday.get('start', '')
                end_str = holiday.get('end', '')
                
                # Try different date formats
                for fmt in ['%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%SZ']:
                    try:
                        start = datetime.strptime(start_str, fmt).date() if isinstance(start_str, str) else start_str
                        break
                    except (ValueError, TypeError):
                        continue
                else:
                    # If string parsing fails, check if it's already a date
                    if hasattr(start_str, 'date'):
                        start = start_str.date()
                    elif hasattr(start_str, 'year'):
                        start = start_str
                    else:
                        continue
                
                for fmt in ['%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%SZ']:
                    try:
                        end = datetime.strptime(end_str, fmt).date() if isinstance(end_str, str) else end_str
                        break
                    except (ValueError, TypeError):
                        continue
                else:
                    if hasattr(end_str, 'date'):
                        end = end_str.date()
                    elif hasattr(end_str, 'year'):
                        end = end_str
                    else:
                        continue
                
                name = holiday.get('name', 'Ferien')
                holidays.append((start, end, name))
            
            self.school_holidays_cache[cache_key] = holidays
            return holidays
        except Exception as e:
            print(f"Error fetching school holidays: {e}")
            return []
    
    def get_weekends(self, year: int) -> List[Tuple[date, date, int]]:
        """Get all weekends (Saturday-Sunday) for a year with week number"""
        weekends = []
        current_date = date(year, 1, 1)
        
        # Find first Saturday
        while current_date.weekday() != 5:  # 5 = Saturday
            current_date = pd.Timestamp(current_date) + pd.Timedelta(days=1)
            current_date = current_date.date()
        
        # Collect all weekends
        while current_date.year == year:
            sunday = pd.Timestamp(current_date) + pd.Timedelta(days=1)
            if sunday.year == year:
                week_num = current_date.isocalendar()[1]
                weekends.append((current_date, sunday.date(), week_num))
            current_date = pd.Timestamp(current_date) + pd.Timedelta(days=7)
            current_date = current_date.date()
        
        return weekends
    
    def categorize_date(self, check_date: date, year: int) -> Tuple[str, str]:
        """Categorize a date as holiday, school holiday, weekend, or normal day"""
        # Check public holidays
        holidays = self.get_public_holidays(year)
        for holiday_name, holiday_date in holidays.items():
            if check_date == holiday_date:
                return "public_holiday", holiday_name
        
        # Check school holidays
        school_holidays = self.get_school_holidays(year)
        for start, end, name in school_holidays:
            if start <= check_date <= end:
                return "school_holiday", name
        
        # Check weekends
        if check_date.weekday() in [5, 6]:  # Saturday or Sunday
            week_num = check_date.isocalendar()[1]
            return "weekend", f"KW{week_num}"
        
        return "normal", "Normal day"