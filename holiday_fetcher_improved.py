"""Improved module for fetching German holidays with fallback data"""

import requests
from datetime import datetime, date
from typing import Dict, List, Tuple
import pandas as pd
from config import HOLIDAY_API_URL, SCHOOL_HOLIDAY_API_URL

# Fallback holiday data for common German holidays
FALLBACK_HOLIDAYS = {
    "Neujahr": "01-01",
    "Karfreitag": None,  # Varies by year
    "Ostermontag": None,  # Varies by year
    "Tag der Arbeit": "05-01",
    "Christi Himmelfahrt": None,  # Varies by year
    "Pfingstmontag": None,  # Varies by year
    "Tag der Deutschen Einheit": "10-03",
    "Weihnachten": "12-25",
    "2. Weihnachtstag": "12-26"
}

class HolidayFetcher:
    def __init__(self, federal_state: str):
        self.federal_state = federal_state.upper()
        self.holidays_cache = {}
        self.school_holidays_cache = {}
    
    def get_public_holidays(self, year: int) -> Dict[str, date]:
        """Fetch public holidays with multiple fallback strategies"""
        cache_key = f"{year}_{self.federal_state}"
        if cache_key in self.holidays_cache:
            return self.holidays_cache[cache_key]
        
        holidays = {}
        
        # Try primary API
        try:
            holidays = self._fetch_from_primary_api(year)
        except Exception as e:
            print(f"Primary API failed: {e}")
            
        # If no holidays fetched, use fallback data
        if not holidays:
            holidays = self._get_fallback_holidays(year)
            
        self.holidays_cache[cache_key] = holidays
        return holidays
    
    def _fetch_from_primary_api(self, year: int) -> Dict[str, date]:
        """Try to fetch from the primary API"""
        holidays = {}
        
        # Try the simple API first
        try:
            url = f"https://date.nager.at/api/v3/publicholidays/{year}/DE"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            for holiday in data:
                # Check if holiday applies to our state
                counties = holiday.get('counties', [])
                if not counties or f"DE-{self.federal_state}" in counties:
                    holiday_date = datetime.strptime(holiday['date'], '%Y-%m-%d').date()
                    holidays[holiday['localName']] = holiday_date
                    
        except Exception as e:
            print(f"Nager API failed: {e}")
            
        return holidays
    
    def _get_fallback_holidays(self, year: int) -> Dict[str, date]:
        """Generate basic holiday dates as fallback"""
        holidays = {}
        
        # Fixed date holidays
        for name, date_str in FALLBACK_HOLIDAYS.items():
            if date_str:
                month, day = map(int, date_str.split('-'))
                holidays[name] = date(year, month, day)
        
        # Calculate Easter and related holidays
        easter = self._calculate_easter(year)
        holidays["Karfreitag"] = easter - pd.Timedelta(days=2)
        holidays["Ostersonntag"] = easter
        holidays["Ostermontag"] = easter + pd.Timedelta(days=1)
        holidays["Christi Himmelfahrt"] = easter + pd.Timedelta(days=39)
        holidays["Pfingstmontag"] = easter + pd.Timedelta(days=50)
        
        return holidays
    
    def _calculate_easter(self, year: int) -> date:
        """Calculate Easter Sunday using Gauss's Easter algorithm"""
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        n = (h + l - 7 * m + 114) // 31
        p = (h + l - 7 * m + 114) % 31
        return date(year, n, p + 1)
    
    def get_school_holidays(self, year: int) -> List[Tuple[date, date, str]]:
        """Get school holidays with fallback to typical periods"""
        cache_key = f"{year}_{self.federal_state}"
        if cache_key in self.school_holidays_cache:
            return self.school_holidays_cache[cache_key]
        
        holidays = []
        
        # Try to fetch from API
        try:
            holidays = self._fetch_school_holidays_api(year)
        except Exception as e:
            print(f"School holiday API failed: {e}")
            
        # If no holidays fetched, use typical periods
        if not holidays:
            holidays = self._get_typical_school_holidays(year)
            
        self.school_holidays_cache[cache_key] = holidays
        return holidays
    
    def _fetch_school_holidays_api(self, year: int) -> List[Tuple[date, date, str]]:
        """Fetch school holidays from API"""
        holidays = []
        
        try:
            # Map state codes for the API
            state_map = {
                'BW': 'BW', 'BY': 'BY', 'BE': 'BE', 'BB': 'BB',
                'HB': 'HB', 'HH': 'HH', 'HE': 'HE', 'MV': 'MV',
                'NI': 'NI', 'NW': 'NW', 'RP': 'RP', 'SL': 'SL',
                'SN': 'SN', 'ST': 'ST', 'SH': 'SH', 'TH': 'TH'
            }
            
            state_code = state_map.get(self.federal_state, self.federal_state)
            url = f"https://ferien-api.de/api/v1/holidays/{state_code}/{year}"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                for holiday in data:
                    start_str = holiday.get('start', '')
                    end_str = holiday.get('end', '')
                    name = holiday.get('name', 'Schulferien')
                    
                    # Parse dates with multiple format attempts
                    start = self._parse_date(start_str)
                    end = self._parse_date(end_str)
                    
                    if start and end:
                        # Normalize holiday name to include state and year for consistency
                        normalized_name = self._normalize_holiday_name(name, year)
                        holidays.append((start, end, normalized_name))
                        
        except Exception as e:
            print(f"API error: {e}")
            
        return holidays
    
    def _normalize_holiday_name(self, name: str, year: int) -> str:
        """Normalize holiday name to ensure consistent format"""
        # Convert to lowercase for consistency
        name_lower = name.lower()
        
        # Map state codes to full names
        state_names = {
            'BW': 'baden-württemberg',
            'BY': 'bayern',
            'BE': 'berlin',
            'BB': 'brandenburg',
            'HB': 'bremen',
            'HH': 'hamburg',
            'HE': 'hessen',
            'MV': 'mecklenburg-vorpommern',
            'NI': 'niedersachsen',
            'NW': 'nordrhein-westfalen',
            'RP': 'rheinland-pfalz',
            'SL': 'saarland',
            'SN': 'sachsen',
            'ST': 'sachsen-anhalt',
            'SH': 'schleswig-holstein',
            'TH': 'thüringen'
        }
        
        state_name = state_names.get(self.federal_state, self.federal_state.lower())
        
        # Check if the name already contains the state and year
        has_state = state_name in name_lower
        has_year = str(year) in name
        
        # Build normalized name
        if not has_state and not has_year:
            # Name has neither state nor year (e.g., "Winterferien")
            return f"{name_lower} {state_name} {year}"
        elif not has_state:
            # Has year but no state
            return f"{name_lower.replace(str(year), '')} {state_name} {year}".strip()
        elif not has_year:
            # Has state but no year
            return f"{name_lower} {year}"
        else:
            # Already has both
            return name_lower
    
    def _parse_date(self, date_str: str) -> date:
        """Parse date string with multiple format attempts"""
        if not date_str:
            return None
            
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except (ValueError, TypeError):
                continue
                
        return None
    
    def _get_typical_school_holidays(self, year: int) -> List[Tuple[date, date, str]]:
        """Generate typical school holiday periods as fallback"""
        holidays = []
        
        # Typical German school holiday periods (approximate)
        # Winter holidays (around February)
        name = self._normalize_holiday_name("Winterferien", year)
        holidays.append((date(year, 2, 10), date(year, 2, 24), name))
        
        # Easter holidays (around Easter)
        easter = self._calculate_easter(year)
        name = self._normalize_holiday_name("Osterferien", year)
        holidays.append((easter - pd.Timedelta(days=7), easter + pd.Timedelta(days=7), name))
        
        # Whitsun holidays (around Pentecost)
        name = self._normalize_holiday_name("Pfingstferien", year)
        holidays.append((easter + pd.Timedelta(days=49), easter + pd.Timedelta(days=56), name))
        
        # Summer holidays (July-August, varies by state)
        name = self._normalize_holiday_name("Sommerferien", year)
        if self.federal_state in ['BY', 'BW']:
            # Southern states typically later
            holidays.append((date(year, 7, 25), date(year, 9, 7), name))
        else:
            # Northern states typically earlier
            holidays.append((date(year, 7, 1), date(year, 8, 15), name))
        
        # Autumn holidays (October)
        name = self._normalize_holiday_name("Herbstferien", year)
        holidays.append((date(year, 10, 14), date(year, 10, 25), name))
        
        # Christmas holidays
        name = self._normalize_holiday_name("Weihnachtsferien", year)
        holidays.append((date(year, 12, 23), date(year, 12, 31), name))
        if year < 2100:  # Avoid going into next year for last year
            holidays.append((date(year + 1, 1, 1), date(year + 1, 1, 6), name))
        
        return holidays
    
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