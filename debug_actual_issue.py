"""Debug what's actually happening with the data"""

from load_profile_processor import LoadProfileProcessor
import pandas as pd

def debug_actual_issue():
    """Find out why we're still seeing only sommerferien"""
    
    print("🔍 DEBUGGING THE ACTUAL ISSUE")
    print("=" * 60)
    
    # Test with NI since that's where the problem is
    processor_ni = LoadProfileProcessor('NI')
    
    # Load test data
    with open('test_load_profile_2024.csv', 'r') as f:
        test_csv = f.read()
    
    source_df = processor_ni.parse_load_profile(test_csv)
    daily_chunks = processor_ni.chunk_by_days(source_df)
    categorized_source = processor_ni.categorize_days(daily_chunks)
    
    print("\n📊 Source Data Analysis for NI:")
    print(f"Total days chunked: {len(daily_chunks)}")
    print(f"School holidays: {len(categorized_source['school_holiday'])} days")
    
    # Count holiday types in source
    holiday_types = {}
    for src_date, chunk, desc in categorized_source['school_holiday']:
        # Extract just the holiday type (first word)
        holiday_type = desc.split()[0] if desc else "unknown"
        if holiday_type not in holiday_types:
            holiday_types[holiday_type] = 0
        holiday_types[holiday_type] += 1
    
    print("\n📚 Holiday types in 2024 source:")
    for htype, count in holiday_types.items():
        print(f"  {htype}: {count} days")
    
    # Now let's trace exactly what happens when we map to 2026
    print("\n\n🔄 Tracing the mapping process for 2026:")
    print("-" * 40)
    
    # Get 2026 holidays
    holidays_2026 = processor_ni.holiday_fetcher.get_school_holidays(2026)
    
    print(f"\n2026 holidays from fetcher: {len(holidays_2026)}")
    for start, end, name in holidays_2026[:3]:
        print(f"  {name}: {start} to {end}")
    
    # Now trace the actual mapping for a specific date
    test_date = pd.Timestamp('2026-02-10').date()  # Should be Winterferien
    
    print(f"\n\n🎯 Tracing mapping for {test_date}:")
    
    # What category is this date?
    category, description = processor_ni.holiday_fetcher.categorize_date(test_date, 2026)
    print(f"  Category: {category}")
    print(f"  Description: '{description}'")
    
    if category == 'school_holiday':
        # Remove year for matching (this is our fix)
        import re
        target_type = re.sub(r'\s*\d{4}\s*', '', description).strip().lower()
        print(f"  Target type (no year): '{target_type}'")
        
        # Find matching holidays in source
        matching_holidays = []
        for src_date, chunk, src_desc in categorized_source['school_holiday']:
            source_type = re.sub(r'\s*\d{4}\s*', '', src_desc).strip().lower()
            if source_type == target_type:
                matching_holidays.append((src_date, chunk, src_desc))
        
        print(f"  Matching holidays found: {len(matching_holidays)}")
        
        if matching_holidays:
            print("  ✅ Should use proper matching")
            for i, (src_date, _, src_desc) in enumerate(matching_holidays[:3]):
                print(f"    Match {i+1}: {src_date} - {src_desc}")
        else:
            print("  ❌ No matches - will use fallback")
            print("  This is why fallback is being used!")
    
    # Actually run the mapping
    print("\n\n📈 Running actual mapping:")
    result_df = processor_ni.map_to_future_year(categorized_source, 2026)
    
    # Check what we got for February 2026
    feb_dates = pd.date_range('2026-02-10', '2026-02-12')
    for check_date in feb_dates:
        day_data = result_df[result_df['timestamp'].dt.date == check_date.date()]
        if not day_data.empty:
            source = day_data.iloc[0]['source']
            print(f"\n  {check_date.date()}: {source}")

if __name__ == "__main__":
    debug_actual_issue()