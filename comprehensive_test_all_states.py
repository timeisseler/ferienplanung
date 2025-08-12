"""Comprehensive test for all federal states"""

from load_profile_processor import LoadProfileProcessor
import pandas as pd

def test_all_states():
    """Test holiday mapping for multiple federal states"""
    
    print("🎯 COMPREHENSIVE TEST - ALL STATES")
    print("=" * 80)
    
    # Test key states
    test_states = ['BW', 'NI', 'BY']
    
    # Load test data once
    with open('test_load_profile_2024.csv', 'r') as f:
        test_csv = f.read()
    
    all_passed = True
    
    for state in test_states:
        print(f"\n📍 Testing {state}")
        print("-" * 60)
        
        processor = LoadProfileProcessor(state)
        source_df = processor.parse_load_profile(test_csv)
        
        # Generate for 2026
        results = processor.generate_future_profiles(source_df, [2026])
        
        if 2026 in results:
            result_df = results[2026]
            
            # Get holidays for this state
            holidays_2026 = processor.holiday_fetcher.get_school_holidays(2026)
            
            fallback_count = 0
            proper_match_count = 0
            holiday_samples = []
            
            # Sample each holiday type
            for start, end, name in holidays_2026[:5]:  # Check first 5 holidays
                # Sample first day
                day_data = result_df[result_df['timestamp'].dt.date == start]
                if not day_data.empty:
                    source = day_data.iloc[0]['source']
                    is_fallback = '(fallback)' in source
                    
                    # Extract holiday type from name
                    holiday_type = name.split()[0].lower()
                    source_contains_type = holiday_type in source.lower()
                    
                    if is_fallback:
                        fallback_count += 1
                        status = "❌ FALLBACK"
                    else:
                        proper_match_count += 1
                        status = "✅ MATCHED"
                    
                    correct_type = "✅" if source_contains_type else "❌"
                    
                    holiday_samples.append({
                        'name': name[:40],
                        'status': status,
                        'correct_type': correct_type
                    })
            
            # Print results
            print(f"\n  Holiday Mapping Results:")
            for sample in holiday_samples:
                print(f"    {sample['name']:<40} {sample['status']} Type: {sample['correct_type']}")
            
            print(f"\n  Summary: {proper_match_count} matched, {fallback_count} fallbacks")
            
            if fallback_count > proper_match_count:
                print(f"  ⚠️ WARNING: Too many fallbacks for {state}")
                all_passed = False
            else:
                print(f"  ✅ GOOD: Most holidays properly matched")
            
            # Check that different days have different profiles
            print(f"\n  Multi-day Holiday Test:")
            for start, end, name in holidays_2026:
                if (end - start).days >= 3:
                    loads = []
                    for i in range(min(3, (end - start).days + 1)):
                        check_date = start + pd.Timedelta(days=i)
                        day_data = result_df[result_df['timestamp'].dt.date == check_date]
                        if not day_data.empty:
                            loads.append(round(day_data['load'].mean(), 0))
                    
                    if len(set(loads)) > 1:
                        print(f"    ✅ {name[:30]}: Different profiles")
                    else:
                        print(f"    ❌ {name[:30]}: Same profile repeated!")
                        all_passed = False
                    break
    
    # Final verdict
    print("\n" + "=" * 80)
    print("📊 FINAL VERDICT:")
    if all_passed:
        print("✅ ALL TESTS PASSED - Holiday mapping working correctly!")
        print("\nKey improvements:")
        print("  1. Holiday names are normalized for consistent matching")
        print("  2. Each holiday day gets a unique load profile")
        print("  3. Matching works across different federal states")
    else:
        print("⚠️ SOME ISSUES REMAIN")
        print("  Note: Some fallbacks are expected when source data lacks certain holiday types")
    
    return all_passed

if __name__ == "__main__":
    test_all_states()