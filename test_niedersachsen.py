"""Test script specifically for Niedersachsen issues"""

from load_profile_processor import LoadProfileProcessor
import pandas as pd
from datetime import datetime

def test_niedersachsen():
    """Test holiday mapping for Niedersachsen"""
    
    print("🔍 Testing Niedersachsen (NI) holiday mapping...")
    print("=" * 60)
    
    # Test with Niedersachsen
    processor_ni = LoadProfileProcessor('NI')
    
    # Load test data
    with open('test_load_profile_2024.csv', 'r') as f:
        test_csv = f.read()
    
    # Parse source data
    source_df = processor_ni.parse_load_profile(test_csv)
    daily_chunks = processor_ni.chunk_by_days(source_df)
    categorized_source = processor_ni.categorize_days(daily_chunks)
    
    print("\n📊 Source data (2024) with NI holidays:")
    print(f"Total days: {len(daily_chunks)}")
    print(f"School holidays: {len(categorized_source['school_holiday'])} days")
    
    # Show what holidays were found in source
    holiday_types_source = {}
    for src_date, chunk, desc in categorized_source['school_holiday']:
        holiday_type = desc.split()[0] if desc else "unknown"
        if holiday_type not in holiday_types_source:
            holiday_types_source[holiday_type] = []
        holiday_types_source[holiday_type].append((src_date, desc))
    
    print("\n🏫 School holidays found in 2024 for NI:")
    for holiday_type, dates in holiday_types_source.items():
        print(f"  {holiday_type}: {len(dates)} days")
        if dates:
            print(f"    First day: {dates[0][0]} - {dates[0][1]}")
    
    # Get holidays for 2026
    print("\n📅 Target holidays for NI in 2026:")
    holidays_2026 = processor_ni.holiday_fetcher.get_school_holidays(2026)
    for start, end, name in holidays_2026:
        duration = (end - start).days + 1
        print(f"  {name}: {start} to {end} ({duration} days)")
    
    # Generate future profile
    print("\n🔄 Generating 2026 profile...")
    results = processor_ni.generate_future_profiles(source_df, [2026])
    
    if 2026 in results:
        result_df = results[2026]
        
        # Check different holiday periods
        print("\n📋 Checking holiday mappings in 2026:")
        
        # Check each type of holiday
        for start, end, name in holidays_2026[:3]:  # Check first 3 holidays
            print(f"\n  {name}:")
            
            # Sample first 3 days of the holiday
            for i in range(min(3, (end - start).days + 1)):
                check_date = start + pd.Timedelta(days=i)
                day_data = result_df[result_df['timestamp'].dt.date == check_date]
                
                if not day_data.empty:
                    source = day_data.iloc[0]['source']
                    avg_load = day_data['load'].mean()
                    
                    # Analyze the source
                    is_fallback = '(fallback)' in source
                    source_holiday_type = 'unknown'
                    if 'sommerferien' in source.lower():
                        source_holiday_type = 'sommerferien'
                    elif 'osterferien' in source.lower():
                        source_holiday_type = 'osterferien'
                    elif 'herbstferien' in source.lower():
                        source_holiday_type = 'herbstferien'
                    elif 'winterferien' in source.lower():
                        source_holiday_type = 'winterferien'
                    elif 'pfingstferien' in source.lower():
                        source_holiday_type = 'pfingstferien'
                    elif 'weihnachtsferien' in source.lower():
                        source_holiday_type = 'weihnachtsferien'
                    
                    print(f"    Day {i+1} ({check_date}):")
                    print(f"      Source type: {source_holiday_type}")
                    print(f"      Fallback: {'YES ❌' if is_fallback else 'NO ✅'}")
                    print(f"      Full source: {source[:80]}")
    
    # Now test the matching logic directly
    print("\n\n🔬 Direct matching logic test:")
    
    # Test Winterferien matching
    target_desc = "winterferien niedersachsen 2026"
    import re
    target_type = re.sub(r'\s*\d{4}\s*', '', target_desc).strip().lower()
    print(f"\nTarget: '{target_desc}'")
    print(f"Target type (no year): '{target_type}'")
    
    matches_found = 0
    print("\nChecking source holidays:")
    for src_date, chunk, src_desc in categorized_source['school_holiday'][:10]:
        source_type = re.sub(r'\s*\d{4}\s*', '', src_desc).strip().lower()
        matches = (source_type == target_type)
        
        if matches or 'winterferien' in src_desc.lower():
            print(f"  {src_desc}:")
            print(f"    Source type (no year): '{source_type}'")
            print(f"    Match: {matches}")
            matches_found += 1
    
    if matches_found == 0:
        print("  ❌ No winterferien found in source data for NI!")
        print("     This explains why fallback is used.")

if __name__ == "__main__":
    test_niedersachsen()