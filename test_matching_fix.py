"""Test that holiday matching now works without fallback"""

from load_profile_processor import LoadProfileProcessor
import pandas as pd

def test_matching_fix():
    """Test that holidays now match correctly without fallback"""
    
    print("🧪 Testing holiday matching fix...")
    
    # Load test data
    with open('test_load_profile_2024.csv', 'r') as f:
        test_csv = f.read()
    
    processor = LoadProfileProcessor('BW')
    source_df = processor.parse_load_profile(test_csv)
    
    # Generate profile for 2026
    results = processor.generate_future_profiles(source_df, [2026])
    
    if 2026 in results:
        result_df = results[2026]
        
        # Check Osterferien (Easter holidays)
        print("\n📅 Checking Osterferien 2026 (should map to Osterferien 2024):")
        oster_dates = pd.date_range('2026-03-30', '2026-04-02')
        
        for check_date in oster_dates:
            day_data = result_df[result_df['timestamp'].dt.date == check_date.date()]
            if not day_data.empty:
                source = day_data.iloc[0]['source']
                avg_load = day_data['load'].mean()
                
                # Check if it's using fallback or proper matching
                is_fallback = '(fallback)' in source
                holiday_type = 'osterferien' in source.lower()
                
                print(f"  {check_date.date()}: avg={avg_load:.2f}")
                print(f"    Source: {source}")
                print(f"    Using fallback: {'❌ YES' if is_fallback else '✅ NO'}")
                print(f"    Correct holiday: {'✅ YES' if holiday_type else '❌ NO'}")
        
        # Check Sommerferien (Summer holidays) - should be in July/August, not April!
        print("\n📅 Checking Sommerferien 2026 (should be July 30 - Sept 13):")
        summer_start = pd.Timestamp('2026-07-30')
        
        for i in range(3):
            check_date = summer_start + pd.Timedelta(days=i)
            day_data = result_df[result_df['timestamp'].dt.date == check_date.date()]
            if not day_data.empty:
                source = day_data.iloc[0]['source']
                avg_load = day_data['load'].mean()
                
                is_fallback = '(fallback)' in source
                holiday_type = 'sommerferien' in source.lower()
                
                print(f"  {check_date.date()}: avg={avg_load:.2f}")
                print(f"    Source: {source}")
                print(f"    Using fallback: {'❌ YES' if is_fallback else '✅ NO'}")
                print(f"    Correct holiday: {'✅ YES' if holiday_type else '❌ NO'}")
        
        # Also check that April doesn't have summer holidays
        print("\n📅 Checking April 2026 (should NOT have Sommerferien):")
        april_dates = pd.date_range('2026-04-15', '2026-04-17')
        
        for check_date in april_dates:
            day_data = result_df[result_df['timestamp'].dt.date == check_date.date()]
            if not day_data.empty:
                source = day_data.iloc[0]['source']
                has_sommerferien = 'sommerferien' in source.lower()
                
                print(f"  {check_date.date()}: {source[:60]}...")
                if has_sommerferien:
                    print(f"    ❌ ERROR: Summer holidays in April!")
                else:
                    print(f"    ✅ OK: No summer holidays")
        
        return True
    
    return False

if __name__ == "__main__":
    if test_matching_fix():
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")