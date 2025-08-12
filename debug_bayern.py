"""Debug Bayern issue with repeated profiles"""

from load_profile_processor import LoadProfileProcessor
import pandas as pd

def debug_bayern():
    """Debug why Bayern has repeated profiles"""
    
    print("🔍 Debugging Bayern (BY) holiday mapping...")
    
    # Load test data
    with open('test_load_profile_2024.csv', 'r') as f:
        test_csv = f.read()
    
    processor = LoadProfileProcessor('BY')
    source_df = processor.parse_load_profile(test_csv)
    daily_chunks = processor.chunk_by_days(source_df)
    categorized_source = processor.categorize_days(daily_chunks)
    
    # Check source holidays for BY
    print("\n📊 Source holidays for BY in 2024:")
    holiday_counts = {}
    for src_date, chunk, desc in categorized_source['school_holiday']:
        holiday_type = desc.split()[0] if desc else "unknown"
        if holiday_type not in holiday_counts:
            holiday_counts[holiday_type] = []
        holiday_counts[holiday_type].append(src_date)
    
    for holiday_type, dates in holiday_counts.items():
        print(f"  {holiday_type}: {len(dates)} days")
        if dates and holiday_type == 'winterferien':
            print(f"    Dates: {dates[:5]}")
    
    # Check if BY winterferien has only 1 day in source
    if 'winterferien' in holiday_counts and len(holiday_counts['winterferien']) == 1:
        print("\n  ⚠️ PROBLEM: Only 1 day of winterferien in source for BY!")
        print("     This causes the same day to be repeated in mapping.")
    
    # Generate and check 2026
    results = processor.generate_future_profiles(source_df, [2026])
    if 2026 in results:
        result_df = results[2026]
        
        # Check winterferien 2026
        holidays_2026 = processor.holiday_fetcher.get_school_holidays(2026)
        for start, end, name in holidays_2026:
            if 'winterferien' in name.lower():
                print(f"\n📅 Checking {name} from {start} to {end}")
                
                for i in range(min(5, (end - start).days + 1)):
                    check_date = start + pd.Timedelta(days=i)
                    day_data = result_df[result_df['timestamp'].dt.date == check_date]
                    if not day_data.empty:
                        source = day_data.iloc[0]['source']
                        avg_load = day_data['load'].mean()
                        print(f"  Day {i+1}: avg={avg_load:.2f}, source: {source[:60]}")
                break

if __name__ == "__main__":
    debug_bayern()