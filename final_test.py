"""Final comprehensive test of all fixes"""

from load_profile_processor import LoadProfileProcessor
import pandas as pd

def final_comprehensive_test():
    """Final test to verify all issues are resolved"""
    
    print("🎯 FINAL COMPREHENSIVE TEST")
    print("=" * 60)
    
    # Load test data
    with open('test_load_profile_2024.csv', 'r') as f:
        test_csv = f.read()
    
    processor = LoadProfileProcessor('BW')
    source_df = processor.parse_load_profile(test_csv)
    
    # Generate profiles for multiple years
    results = processor.generate_future_profiles(source_df, [2025, 2026])
    
    all_tests_passed = True
    
    for year in [2025, 2026]:
        print(f"\n📅 Testing year {year}:")
        print("-" * 40)
        
        if year not in results:
            print(f"❌ Failed to generate profile for {year}")
            all_tests_passed = False
            continue
        
        result_df = results[year]
        
        # Test 1: Check that holidays don't always use fallback
        print("\n1️⃣ Holiday Matching Test:")
        holidays = processor.holiday_fetcher.get_school_holidays(year)
        fallback_count = 0
        proper_match_count = 0
        
        for start, end, name in holidays[:2]:  # Check first 2 holidays
            # Sample first day of each holiday
            day_data = result_df[result_df['timestamp'].dt.date == start]
            if not day_data.empty:
                source = day_data.iloc[0]['source']
                if '(fallback)' in source:
                    fallback_count += 1
                    print(f"   ❌ {name}: Using fallback")
                else:
                    proper_match_count += 1
                    print(f"   ✅ {name}: Proper match")
        
        if proper_match_count > fallback_count:
            print(f"   ✅ PASSED: Most holidays use proper matching")
        else:
            print(f"   ❌ FAILED: Too many fallbacks")
            all_tests_passed = False
        
        # Test 2: Check that multi-day holidays have different profiles each day
        print("\n2️⃣ Multi-Day Holiday Test:")
        for start, end, name in holidays:
            if (end - start).days >= 3:  # Find a holiday with at least 3 days
                loads = []
                for i in range(3):
                    check_date = start + pd.Timedelta(days=i)
                    day_data = result_df[result_df['timestamp'].dt.date == check_date]
                    if not day_data.empty:
                        avg_load = day_data['load'].mean()
                        loads.append(round(avg_load, 0))
                
                unique_loads = len(set(loads))
                if unique_loads > 1:
                    print(f"   ✅ {name}: Different profiles for different days")
                    print(f"      Day loads: {loads}")
                else:
                    print(f"   ❌ {name}: Same profile repeated!")
                    print(f"      Day loads: {loads}")
                    all_tests_passed = False
                break
        
        # Test 3: Check that holidays are in correct months
        print("\n3️⃣ Holiday Date Correctness Test:")
        
        # Check summer holidays are in summer
        summer_holidays = [h for h in holidays if 'sommerferien' in h[2].lower()]
        if summer_holidays:
            summer_start, summer_end, summer_name = summer_holidays[0]
            if summer_start.month in [7, 8]:
                print(f"   ✅ Summer holidays start in {summer_start.strftime('%B')} (correct)")
            else:
                print(f"   ❌ Summer holidays start in {summer_start.strftime('%B')} (wrong!)")
                all_tests_passed = False
        
        # Check Easter holidays are in spring
        easter_holidays = [h for h in holidays if 'osterferien' in h[2].lower()]
        if easter_holidays:
            easter_start, easter_end, easter_name = easter_holidays[0]
            if easter_start.month in [3, 4]:
                print(f"   ✅ Easter holidays start in {easter_start.strftime('%B')} (correct)")
            else:
                print(f"   ❌ Easter holidays start in {easter_start.strftime('%B')} (wrong!)")
                all_tests_passed = False
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS:")
    print("=" * 60)
    
    if all_tests_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nSummary of fixes:")
        print("1. ✅ Fixed holiday mapping to match each day individually")
        print("2. ✅ Fixed holiday name matching by removing year from comparison")
        print("3. ✅ Fixed fallback logic to cycle through available days")
        print("4. ✅ Holidays now map to correct time periods")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please review the output above for details.")
    
    return all_tests_passed

if __name__ == "__main__":
    success = final_comprehensive_test()
    exit(0 if success else 1)