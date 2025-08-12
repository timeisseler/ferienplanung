"""Debug script to understand why holiday matching always falls back"""

import pandas as pd
from datetime import datetime, date
from load_profile_processor import LoadProfileProcessor

def debug_holiday_matching():
    """Debug why holidays always use fallback"""
    
    print("🔍 Debugging holiday matching logic...")
    
    # Initialize processor
    processor = LoadProfileProcessor('BW')
    
    # Load the actual test data
    with open('test_load_profile_2024.csv', 'r') as f:
        test_csv = f.read()
    
    # Parse the data
    source_df = processor.parse_load_profile(test_csv)
    daily_chunks = processor.chunk_by_days(source_df)
    categorized_source = processor.categorize_days(daily_chunks)
    
    print(f"\n📊 Source data analysis:")
    print(f"Total days: {len(daily_chunks)}")
    print(f"School holidays: {len(categorized_source['school_holiday'])}")
    
    # Analyze school holidays in source (2024)
    print("\n🏫 School holidays in 2024 source data:")
    holiday_groups = {}
    for src_date, chunk, desc in categorized_source['school_holiday']:
        if desc not in holiday_groups:
            holiday_groups[desc] = []
        holiday_groups[desc].append(src_date)
    
    for holiday_name, dates in holiday_groups.items():
        dates_sorted = sorted(dates)
        print(f"\n  {holiday_name}:")
        print(f"    Period: {dates_sorted[0]} to {dates_sorted[-1]} ({len(dates)} days)")
        print(f"    First 3 days: {dates_sorted[:3]}")
    
    # Get holidays for 2026
    print("\n\n📅 School holidays in target year 2026:")
    holidays_2026 = processor.holiday_fetcher.get_school_holidays(2026)
    for start, end, name in holidays_2026:
        duration = (end - start).days + 1
        print(f"  {name}: {start} to {end} ({duration} days)")
    
    # Test the matching logic for Osterferien
    print("\n\n🔄 Testing matching logic for Osterferien 2026:")
    
    # Find Osterferien in 2026
    oster_2026 = None
    for start, end, name in holidays_2026:
        if 'osterferien' in name.lower():
            oster_2026 = (start, end, name)
            break
    
    if oster_2026:
        print(f"Target: {oster_2026[2]} from {oster_2026[0]} to {oster_2026[1]}")
        
        # Check first day of Osterferien 2026
        test_date = oster_2026[0]
        category, description = processor.holiday_fetcher.categorize_date(test_date, 2026)
        print(f"\nCategorization of {test_date}:")
        print(f"  Category: {category}")
        print(f"  Description: '{description}'")
        
        # Now check what source holidays would match
        print(f"\nMatching logic test:")
        print(f"  Looking for source holidays matching: '{description}'")
        
        matching_count = 0
        for src_date, chunk, src_desc in categorized_source['school_holiday']:
            # This is the matching logic from load_profile_processor.py line 137
            matches = (src_desc.lower() in description.lower() or 
                      description.lower() in src_desc.lower())
            
            if matches:
                matching_count += 1
                if matching_count <= 3:
                    print(f"    ✓ Match found: '{src_desc}' on {src_date}")
            elif matching_count == 0 and src_desc != src_desc:  # Just to show first few non-matches
                print(f"    ✗ No match: '{src_desc}' vs '{description}'")
                print(f"       Test 1: '{src_desc.lower()}' in '{description.lower()}' = {src_desc.lower() in description.lower()}")
                print(f"       Test 2: '{description.lower()}' in '{src_desc.lower()}' = {description.lower() in src_desc.lower()}")
                break
        
        print(f"\n  Total matches found: {matching_count}")
        
        if matching_count == 0:
            print("\n  ⚠️ No matches found! This explains why fallback is always used.")
            print("     The source data might not have 'osterferien' holidays,")
            print("     or the name format doesn't match between years.")
    
    # Check if source has Osterferien
    print("\n\n🔍 Checking if source data has Osterferien:")
    has_oster = False
    for src_date, chunk, src_desc in categorized_source['school_holiday']:
        if 'osterferien' in src_desc.lower():
            if not has_oster:
                print(f"  Found: '{src_desc}' starting {src_date}")
                has_oster = True
    
    if not has_oster:
        print("  ❌ No Osterferien found in source data!")
        print("     This is why matching fails and fallback is used.")

if __name__ == "__main__":
    debug_holiday_matching()