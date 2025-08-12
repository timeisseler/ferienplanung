"""Debug script to understand the holiday mapping issue"""

import pandas as pd
from datetime import date
from load_profile_processor import LoadProfileProcessor

def debug_holiday_mapping():
    """Debug the holiday mapping to understand the issue"""
    
    print("🔍 Debugging holiday mapping...")
    
    # Initialize processor
    processor = LoadProfileProcessor('BW')
    
    # Create test data with distinct school holiday days
    test_csv = """timestamp;load"""
    
    # Add Sommerferien 2024 (summer holidays) with distinct patterns
    # Let's say it's from July 25 to Sept 7, 2024 (typical Baden-Württemberg pattern)
    for day_offset in range(10):  # First 10 days of summer holidays
        base_date = pd.Timestamp('2024-07-25') + pd.Timedelta(days=day_offset)
        base_load = 1000 + (day_offset * 1000)  # Each day has distinct base load
        
        for i in range(96):
            hour = i // 4
            minute = (i % 4) * 15
            timestamp = f"{base_date.strftime('%Y-%m-%d')} {hour:02d}:{minute:02d}"
            load = base_load + i
            test_csv += f"\n{timestamp};{load},00"
    
    # Add some normal days
    for day_offset in range(10, 30):
        base_date = pd.Timestamp('2024-01-01') + pd.Timedelta(days=day_offset)
        
        for i in range(96):
            hour = i // 4
            minute = (i % 4) * 15
            timestamp = f"{base_date.strftime('%Y-%m-%d')} {hour:02d}:{minute:02d}"
            load = 500 + i
            test_csv += f"\n{timestamp};{load},00"
    
    # Parse the test data
    source_df = processor.parse_load_profile(test_csv)
    daily_chunks = processor.chunk_by_days(source_df)
    categorized_source = processor.categorize_days(daily_chunks)
    
    print(f"\n📊 Source categorization:")
    print(f"School holidays found: {len(categorized_source['school_holiday'])} days")
    
    # Print details of school holiday chunks
    if categorized_source['school_holiday']:
        print("\n🏫 School holiday chunks in source data:")
        for idx, (src_date, chunk, desc) in enumerate(categorized_source['school_holiday'][:5]):
            avg_load = chunk['load'].mean()
            print(f"  [{idx}] {src_date}: {desc} - avg load: {avg_load:.2f}")
    
    # Now test mapping to 2026
    print("\n\n📅 Testing mapping to 2026...")
    
    # Get 2026 school holidays
    holidays_2026 = processor.holiday_fetcher.get_school_holidays(2026)
    if holidays_2026:
        first_holiday = holidays_2026[0]
        print(f"First holiday in 2026: {first_holiday[2]} from {first_holiday[0]} to {first_holiday[1]}")
        
        # Simulate mapping for first few days
        print("\n🔄 Simulating mapping process:")
        
        for day_offset in range(5):
            current_date = pd.Timestamp(first_holiday[0]) + pd.Timedelta(days=day_offset)
            current_date = current_date.date()
            
            if current_date > first_holiday[1]:
                break
                
            category, description = processor.holiday_fetcher.categorize_date(current_date, 2026)
            print(f"\n  Day {day_offset + 1}: {current_date}")
            print(f"    Category: {category}, Description: {description}")
            
            # Check what the mapping logic would do
            matching_holidays = []
            for src_date, chunk, src_desc in categorized_source['school_holiday']:
                if src_desc.lower() in description.lower() or description.lower() in src_desc.lower():
                    matching_holidays.append((src_date, chunk, src_desc))
                    
            print(f"    Matching source holidays: {len(matching_holidays)}")
            
            if matching_holidays:
                # The logic should use day_position to select different chunks
                holiday_start = current_date
                check_date = current_date
                while check_date >= date(2026, 1, 1):
                    prev_date = pd.Timestamp(check_date) - pd.Timedelta(days=1)
                    prev_date = prev_date.date()
                    prev_cat, prev_desc = processor.holiday_fetcher.categorize_date(prev_date, 2026)
                    if prev_cat != 'school_holiday' or prev_desc != description:
                        break
                    holiday_start = prev_date
                    check_date = prev_date
                
                day_position = (current_date - holiday_start).days
                print(f"    Day position in holiday: {day_position}")
                
                if day_position < len(matching_holidays):
                    src_date, chunk, src_desc = matching_holidays[day_position]
                    avg_load = chunk['load'].mean()
                    print(f"    Would use: {src_date} with avg load {avg_load:.2f}")
                else:
                    idx = day_position % len(matching_holidays)
                    src_date, chunk, src_desc = matching_holidays[idx]
                    avg_load = chunk['load'].mean()
                    print(f"    Would use (cycled): index {idx}, {src_date} with avg load {avg_load:.2f}")

if __name__ == "__main__":
    debug_holiday_mapping()