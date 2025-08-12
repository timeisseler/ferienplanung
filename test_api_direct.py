"""Test the APIs directly to see if they're online"""

import requests
import json

def test_apis():
    """Test both holiday APIs directly"""
    
    print("🔍 Testing Holiday APIs Directly")
    print("=" * 60)
    
    # Test states
    states = ['NI', 'BW']
    years = [2024, 2026]
    
    # Test School Holiday API (ferien-api.de)
    print("\n📚 SCHOOL HOLIDAY API (ferien-api.de):")
    print("-" * 40)
    
    for state in states:
        for year in years:
            url = f"https://ferien-api.de/api/v1/holidays/{state}/{year}"
            print(f"\nTesting: {url}")
            
            try:
                response = requests.get(url, timeout=5)
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"  Response: {len(data)} holidays found")
                    
                    # Show first 2 holidays
                    for holiday in data[:2]:
                        print(f"    - {holiday.get('name', 'Unknown')}: {holiday.get('start', 'N/A')} to {holiday.get('end', 'N/A')}")
                else:
                    print(f"  ❌ Error: {response.text[:100]}")
                    
            except requests.exceptions.Timeout:
                print(f"  ❌ TIMEOUT - API not responding")
            except requests.exceptions.ConnectionError as e:
                print(f"  ❌ CONNECTION ERROR: {e}")
            except Exception as e:
                print(f"  ❌ ERROR: {e}")
    
    # Test Public Holiday API (api-feiertage.de)
    print("\n\n🎊 PUBLIC HOLIDAY API (api-feiertage.de):")
    print("-" * 40)
    
    for state in states:
        for year in years:
            url = f"https://get.api-feiertage.de/?years={year}&states={state.lower()}"
            print(f"\nTesting: {url}")
            
            try:
                response = requests.get(url, timeout=5)
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if 'feiertage' in data:
                        print(f"  Response: Found holiday data")
                    else:
                        print(f"  Response structure: {list(data.keys())[:5]}")
                else:
                    print(f"  ❌ Error: {response.text[:100]}")
                    
            except requests.exceptions.Timeout:
                print(f"  ❌ TIMEOUT - API not responding")
            except requests.exceptions.ConnectionError as e:
                print(f"  ❌ CONNECTION ERROR: {e}")
            except Exception as e:
                print(f"  ❌ ERROR: {e}")
    
    # Test what our fetcher actually uses
    print("\n\n🔧 TESTING OUR FETCHER:")
    print("-" * 40)
    
    from holiday_fetcher_improved import HolidayFetcher
    
    for state in states:
        print(f"\n{state}:")
        fetcher = HolidayFetcher(state)
        
        # Clear cache to force fresh fetch
        fetcher.school_holidays_cache = {}
        
        # Try to get holidays
        holidays_2024 = fetcher.get_school_holidays(2024)
        holidays_2026 = fetcher.get_school_holidays(2026)
        
        print(f"  2024: {len(holidays_2024)} holidays")
        if holidays_2024:
            print(f"    First: {holidays_2024[0][2]}")
        
        print(f"  2026: {len(holidays_2026)} holidays")
        if holidays_2026:
            print(f"    First: {holidays_2026[0][2]}")

if __name__ == "__main__":
    test_apis()