"""Debug why string matching fails for holidays"""

from load_profile_processor import LoadProfileProcessor

def debug_string_matching():
    """Debug the exact string matching logic"""
    
    processor = LoadProfileProcessor('BW')
    
    # Load and categorize source data
    with open('test_load_profile_2024.csv', 'r') as f:
        test_csv = f.read()
    
    source_df = processor.parse_load_profile(test_csv)
    daily_chunks = processor.chunk_by_days(source_df)
    categorized_source = processor.categorize_days(daily_chunks)
    
    # Test strings
    target_desc = "osterferien baden-württemberg 2026"
    
    print("🔍 Testing string matching logic:\n")
    
    # Get first osterferien from source
    source_oster = None
    for src_date, chunk, src_desc in categorized_source['school_holiday']:
        if 'osterferien' in src_desc.lower():
            source_oster = src_desc
            break
    
    if source_oster:
        print(f"Source holiday: '{source_oster}'")
        print(f"Target holiday: '{target_desc}'")
        print(f"\nConverted to lowercase:")
        print(f"Source: '{source_oster.lower()}'")
        print(f"Target: '{target_desc.lower()}'")
        
        # Test the exact matching logic from line 137
        test1 = source_oster.lower() in target_desc.lower()
        test2 = target_desc.lower() in source_oster.lower()
        
        print(f"\nMatching tests:")
        print(f"Test 1 - source in target: '{source_oster.lower()}' in '{target_desc.lower()}' = {test1}")
        print(f"Test 2 - target in source: '{target_desc.lower()}' in '{source_oster.lower()}' = {test2}")
        print(f"Combined (OR): {test1 or test2}")
        
        # The problem is clear: "osterferien baden-württemberg 2024" is NOT contained in "osterferien baden-württemberg 2026"
        # and vice versa because of the year difference!
        
        print("\n❌ PROBLEM IDENTIFIED:")
        print("   The matching logic compares the FULL string including the year!")
        print("   'osterferien baden-württemberg 2024' != 'osterferien baden-württemberg 2026'")
        print("\n   We need to match on holiday TYPE, not the full description with year.")
        
        # Test better matching
        print("\n✅ BETTER APPROACH:")
        
        # Extract holiday type without year
        import re
        
        def extract_holiday_type(desc):
            # Remove year (4 digits) and normalize
            return re.sub(r'\s*\d{4}\s*', '', desc).strip().lower()
        
        source_type = extract_holiday_type(source_oster)
        target_type = extract_holiday_type(target_desc)
        
        print(f"Source type (no year): '{source_type}'")
        print(f"Target type (no year): '{target_type}'")
        print(f"Match: {source_type == target_type}")

if __name__ == "__main__":
    debug_string_matching()