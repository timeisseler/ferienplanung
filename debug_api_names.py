"""Debug the exact holiday names returned by the API"""

from holiday_fetcher_improved import HolidayFetcher

def debug_api_names():
    """Check exact holiday names from API"""
    
    print("🔍 Debugging holiday name format from API...")
    print("=" * 60)
    
    # Test both BW and NI
    for state in ['BW', 'NI']:
        print(f"\n📍 State: {state}")
        print("-" * 40)
        
        fetcher = HolidayFetcher(state)
        
        # Get holidays for 2024 and 2026
        for year in [2024, 2026]:
            print(f"\n  Year {year}:")
            holidays = fetcher.get_school_holidays(year)
            
            for start, end, name in holidays[:3]:  # First 3 holidays
                print(f"    '{name}'")
                # Check format
                print(f"      Raw name: {repr(name)}")
                print(f"      Lower: '{name.lower()}'")
                print(f"      Has year: {str(year) in name}")
                
        # Test categorize_date which provides the actual description used in matching
        print(f"\n  Categorization test for {state}:")
        import datetime
        
        # Test a known holiday date
        if state == 'NI':
            test_date = datetime.date(2026, 2, 10)  # Winterferien NI
        else:
            test_date = datetime.date(2026, 3, 30)  # Osterferien BW
            
        for year in [2024, 2026]:
            if year == 2024:
                if state == 'NI':
                    test_date = datetime.date(2024, 2, 1)  # Winterferien NI 2024
                else:
                    test_date = datetime.date(2024, 3, 23)  # Osterferien BW 2024
                    
            category, description = fetcher.categorize_date(test_date, year)
            print(f"    {year} {test_date}: category='{category}', desc='{description}'")

if __name__ == "__main__":
    debug_api_names()