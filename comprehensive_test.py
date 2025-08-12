"""Comprehensive test to verify the holiday mapping fix works correctly"""

import pandas as pd
from datetime import date, datetime, timedelta
from load_profile_processor import LoadProfileProcessor

def create_comprehensive_test_data():
    """Create test data with multiple different holidays"""
    
    # We need data that includes Osterferien (Easter holidays) so they match when mapping
    test_csv = """timestamp;load"""
    
    # Add Osterferien 2024 (Easter holidays) - let's say April 8-19, 2024
    # Each day should have a distinct pattern
    easter_start = datetime(2024, 4, 8)
    for day_offset in range(12):  # 12 days of Easter holidays
        base_date = easter_start + timedelta(days=day_offset)
        base_load = 1000 + (day_offset * 100)  # Each day gets progressively higher base load
        
        for interval in range(96):
            timestamp = base_date + timedelta(minutes=interval * 15)
            load = base_load + interval * 0.5  # Add time-of-day variation
            test_csv += f"\n{timestamp.strftime('%Y-%m-%d %H:%M')};{load:.2f}".replace('.', ',')
    
    # Add Sommerferien 2024 (Summer holidays) - July 25 - Sept 7
    summer_start = datetime(2024, 7, 25)
    for day_offset in range(20):  # First 20 days of summer holidays
        base_date = summer_start + timedelta(days=day_offset)
        base_load = 2000 + (day_offset * 50)  # Different pattern from Easter
        
        for interval in range(96):
            timestamp = base_date + timedelta(minutes=interval * 15)
            load = base_load + interval * 0.3
            test_csv += f"\n{timestamp.strftime('%Y-%m-%d %H:%M')};{load:.2f}".replace('.', ',')
    
    # Add some normal weekdays
    for day_offset in range(30):
        base_date = datetime(2024, 2, 1) + timedelta(days=day_offset)
        if base_date.weekday() < 5:  # Weekday
            for interval in range(96):
                timestamp = base_date + timedelta(minutes=interval * 15)
                load = 800 + interval * 0.4
                test_csv += f"\n{timestamp.strftime('%Y-%m-%d %H:%M')};{load:.2f}".replace('.', ',')
    
    # Add some weekends
    for week in range(10):
        saturday = datetime(2024, 1, 6) + timedelta(weeks=week)
        for day_offset in range(2):  # Saturday and Sunday
            base_date = saturday + timedelta(days=day_offset)
            for interval in range(96):
                timestamp = base_date + timedelta(minutes=interval * 15)
                load = 700 + interval * 0.2
                test_csv += f"\n{timestamp.strftime('%Y-%m-%d %H:%M')};{load:.2f}".replace('.', ',')
    
    return test_csv

def test_holiday_mapping():
    """Test the holiday mapping with comprehensive data"""
    
    print("🧪 Running comprehensive holiday mapping test...")
    
    # Initialize processor for Baden-Württemberg
    processor = LoadProfileProcessor('BW')
    
    # Create test data
    test_csv = create_comprehensive_test_data()
    
    # Parse and process
    source_df = processor.parse_load_profile(test_csv)
    daily_chunks = processor.chunk_by_days(source_df)
    categorized_source = processor.categorize_days(daily_chunks)
    
    print(f"\n📊 Source data categorization:")
    print(f"  - School holidays: {len(categorized_source['school_holiday'])} days")
    print(f"  - Public holidays: {len(categorized_source['public_holiday'])} days")
    print(f"  - Weekends: {len(categorized_source['weekend'])} days")
    print(f"  - Normal days: {len(categorized_source['normal'])} days")
    
    # Show details of school holidays
    print("\n🏫 School holidays in source:")
    holiday_types = {}
    for src_date, chunk, desc in categorized_source['school_holiday']:
        if desc not in holiday_types:
            holiday_types[desc] = []
        avg_load = chunk['load'].mean()
        holiday_types[desc].append((src_date, avg_load))
    
    for holiday_name, days in holiday_types.items():
        print(f"\n  {holiday_name}:")
        for i, (day, avg_load) in enumerate(days[:5]):  # Show first 5 days
            print(f"    Day {i+1} ({day}): avg load = {avg_load:.2f}")
        if len(days) > 5:
            print(f"    ... and {len(days) - 5} more days")
    
    # Test mapping to 2026
    print("\n\n🎯 Testing mapping to 2026...")
    result_df = processor.map_to_future_year(categorized_source, 2026)
    
    # Check Osterferien (Easter holidays) in 2026
    holidays_2026 = processor.holiday_fetcher.get_school_holidays(2026)
    
    for holiday_start, holiday_end, holiday_name in holidays_2026:
        if 'osterferien' in holiday_name.lower():
            print(f"\n📅 Checking '{holiday_name}' from {holiday_start} to {holiday_end}")
            
            # Check first 5 days of the holiday
            current = holiday_start
            day_loads = []
            
            for day_num in range(min(5, (holiday_end - holiday_start).days + 1)):
                day_data = result_df[result_df['timestamp'].dt.date == current]
                if not day_data.empty:
                    avg_load = day_data['load'].mean()
                    day_loads.append(avg_load)
                    source_info = day_data.iloc[0]['source'] if 'source' in day_data.columns else 'N/A'
                    print(f"  Day {day_num + 1} ({current}): avg load = {avg_load:.2f}")
                    print(f"    Source: {source_info}")
                
                current = current + timedelta(days=1)
            
            # Check if loads are different
            if len(day_loads) > 1:
                unique_loads = len(set([round(load, 0) for load in day_loads]))
                if unique_loads > 1:
                    print("\n✅ SUCCESS: Different days have different load profiles!")
                    return True
                else:
                    print("\n❌ FAILURE: All days have the same load profile!")
                    return False
            break
    
    return None

if __name__ == "__main__":
    success = test_holiday_mapping()
    if success:
        print("\n🎉 The holiday mapping is working correctly!")
    elif success is False:
        print("\n😞 The holiday mapping bug is still present.")
    else:
        print("\n🤷 Test was inconclusive.")