"""Test script to verify the holiday mapping fix"""

import pandas as pd
from datetime import date
from load_profile_processor import LoadProfileProcessor

def test_holiday_mapping_fix():
    """Test that holidays are mapped correctly with different days having different profiles"""
    
    print("🧪 Testing holiday mapping fix...")
    
    # Initialize processor for a test state
    processor = LoadProfileProcessor('BW')  # Baden-Württemberg
    
    # Create synthetic test data with distinct patterns for each day
    test_csv = """timestamp;load
2024-07-29 00:00;1000,00
2024-07-29 00:15;1001,00
2024-07-29 00:30;1002,00
2024-07-29 00:45;1003,00"""
    
    # Add remaining intervals for day 1 (pattern: 1000-1095)
    for i in range(4, 96):
        hour = i // 4
        minute = (i % 4) * 15
        test_csv += f"\n2024-07-29 {hour:02d}:{minute:02d};{1000 + i},00"
    
    # Add day 2 with different pattern (2000-2095)
    for i in range(96):
        hour = i // 4
        minute = (i % 4) * 15
        test_csv += f"\n2024-07-30 {hour:02d}:{minute:02d};{2000 + i},00"
    
    # Add day 3 with different pattern (3000-3095)
    for i in range(96):
        hour = i // 4
        minute = (i % 4) * 15
        test_csv += f"\n2024-07-31 {hour:02d}:{minute:02d};{3000 + i},00"
    
    # Add day 4 with different pattern (4000-4095)
    for i in range(96):
        hour = i // 4
        minute = (i % 4) * 15
        test_csv += f"\n2024-08-01 {hour:02d}:{minute:02d};{4000 + i},00"
    
    # Add more normal days to have sufficient data
    for day in range(2, 30):
        for i in range(96):
            hour = i // 4
            minute = (i % 4) * 15
            test_csv += f"\n2024-08-{day:02d} {hour:02d}:{minute:02d};{500 + i},00"
    
    # Parse the test data
    source_df = processor.parse_load_profile(test_csv)
    
    # Categorize the days
    daily_chunks = processor.chunk_by_days(source_df)
    categorized_source = processor.categorize_days(daily_chunks)
    
    print(f"📊 Source data has {len(daily_chunks)} days")
    print(f"   - School holidays: {len(categorized_source['school_holiday'])} days")
    print(f"   - Public holidays: {len(categorized_source['public_holiday'])} days")
    print(f"   - Weekends: {len(categorized_source['weekend'])} days")
    print(f"   - Normal days: {len(categorized_source['normal'])} days")
    
    # Map to a future year
    target_year = 2026
    result_df = processor.map_to_future_year(categorized_source, target_year)
    
    # Check if school holidays in 2026 have different load profiles for different days
    print(f"\n🔍 Checking {target_year} mapping...")
    
    # Get school holidays in target year
    target_school_holidays = processor.holiday_fetcher.get_school_holidays(target_year)
    
    if target_school_holidays:
        # Check first school holiday period
        first_holiday = target_school_holidays[0]
        holiday_start = first_holiday[0]
        holiday_end = first_holiday[1]
        holiday_name = first_holiday[2]
        
        print(f"\n📅 Analyzing '{holiday_name}' from {holiday_start} to {holiday_end}")
        
        # Extract load profiles for the first few days of this holiday
        holiday_loads = {}
        current = holiday_start
        day_count = 0
        
        while current <= holiday_end and day_count < 4:
            # Get the load profile for this day
            day_data = result_df[result_df['timestamp'].dt.date == current]
            if not day_data.empty:
                # Get average load for the day to identify the pattern
                avg_load = day_data['load'].mean()
                holiday_loads[current] = avg_load
                print(f"   Day {day_count + 1} ({current}): avg load = {avg_load:.2f}")
            day_count += 1
            current = pd.Timestamp(current) + pd.Timedelta(days=1)
            current = current.date()
        
        # Check if the loads are different (not all the same)
        load_values = list(holiday_loads.values())
        if len(load_values) > 1:
            if len(set([round(v) for v in load_values])) > 1:
                print("\n✅ SUCCESS: Different days have different load profiles!")
                print("   The bug has been fixed - holidays now map each day individually.")
                return True
            else:
                print("\n❌ FAILURE: All days have the same load profile!")
                print("   The bug is still present.")
                return False
        else:
            print("\n⚠️  Not enough holiday days to test")
    else:
        print("\n⚠️  No school holidays found in target year")
    
    return None

if __name__ == "__main__":
    success = test_holiday_mapping_fix()
    if success:
        print("\n🎉 Test passed! The holiday mapping bug has been fixed.")
    elif success is False:
        print("\n😞 Test failed. The bug is still present.")
    else:
        print("\n🤷 Test inconclusive.")