"""Test full export to see what users actually get"""

from load_profile_processor import LoadProfileProcessor

def test_full_export():
    """Test what the actual CSV export looks like"""
    
    print("📄 Testing Full Export for NI")
    print("=" * 60)
    
    # Load test data
    with open('test_load_profile_2024.csv', 'r') as f:
        test_csv = f.read()
    
    processor = LoadProfileProcessor('NI')
    source_df = processor.parse_load_profile(test_csv)
    
    # Generate for 2026
    results = processor.generate_future_profiles(source_df, [2026])
    
    if 2026 in results:
        result_df = results[2026]
        
        # Export to CSV with source annotations
        csv_output = processor.export_to_csv(result_df, include_source=True)
        
        # Save a sample
        with open('sample_ni_2026_output.csv', 'w') as f:
            # Just save first 1000 lines for inspection
            lines = csv_output.split('\n')[:1000]
            f.write('\n'.join(lines))
        
        print("✅ Sample saved to sample_ni_2026_output.csv")
        
        # Analyze the source column
        print("\n📊 Analyzing source annotations:")
        
        # Count different source types
        source_counts = {}
        lines = csv_output.split('\n')[1:]  # Skip header
        
        for line in lines[:5000]:  # Check first 5000 lines
            if ';' in line:
                parts = line.split(';')
                if len(parts) >= 3:
                    source = parts[2]
                    
                    # Categorize the source
                    if 'winterferien' in source.lower():
                        key = 'winterferien'
                    elif 'osterferien' in source.lower():
                        key = 'osterferien'
                    elif 'pfingstferien' in source.lower():
                        key = 'pfingstferien'
                    elif 'sommerferien' in source.lower():
                        key = 'sommerferien'
                    elif 'herbstferien' in source.lower():
                        key = 'herbstferien'
                    elif 'weihnachtsferien' in source.lower():
                        key = 'weihnachtsferien'
                    elif 'Normal day' in source:
                        key = 'normal'
                    elif 'Weekend' in source:
                        key = 'weekend'
                    elif 'Holiday' in source:
                        key = 'public_holiday'
                    else:
                        key = 'other'
                    
                    if key not in source_counts:
                        source_counts[key] = 0
                    source_counts[key] += 1
        
        print("\nSource type distribution (first 5000 lines):")
        for source_type, count in sorted(source_counts.items()):
            days = count / 96  # Convert to days
            print(f"  {source_type}: {count} intervals ({days:.1f} days)")
        
        # Check specific dates
        print("\n📅 Checking specific holiday periods:")
        
        # Find Winterferien lines (Feb 10-24)
        print("\nWinterferien (Feb 10-12):")
        for line in lines:
            if '2026-02-10' in line or '2026-02-11' in line or '2026-02-12' in line:
                if '00:00' in line:  # Just show first interval of each day
                    parts = line.split(';')
                    if len(parts) >= 3:
                        print(f"  {parts[0]}: {parts[2][:60]}...")
        
        # Find Sommerferien lines (Jul-Aug)
        print("\nSommerferien (Jul 1-3):")
        for line in lines:
            if '2026-07-01' in line or '2026-07-02' in line or '2026-07-03' in line:
                if '00:00' in line:  # Just show first interval of each day
                    parts = line.split(';')
                    if len(parts) >= 3:
                        print(f"  {parts[0]}: {parts[2][:60]}...")

if __name__ == "__main__":
    test_full_export()