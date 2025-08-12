"""Simulate what happens when user runs the app"""

from load_profile_processor import LoadProfileProcessor
import pandas as pd

def simulate_app():
    """Simulate the app workflow"""
    
    print("🎮 SIMULATING APP WORKFLOW")
    print("=" * 60)
    
    # User selects NI and uploads file
    state = 'NI'
    print(f"User selected: {state}")
    
    with open('test_load_profile_2024.csv', 'r') as f:
        csv_content = f.read()
    
    # Initialize processor (as app does)
    processor = LoadProfileProcessor(state)
    
    # Parse load profile (as app does)
    source_df = processor.parse_load_profile(csv_content)
    print(f"✅ Loaded {len(source_df)} data points from year {processor.source_year}")
    
    # User selects target year 2026
    target_years = [2026]
    print(f"User selected target years: {target_years}")
    
    # Generate future profiles (as app does)
    print("\n🔄 Generating simulations...")
    results = processor.generate_future_profiles(source_df, target_years)
    
    for year, df in results.items():
        print(f"\n📅 Year {year}: {len(df)} data points generated")
        
        # Export to CSV (as app does for download)
        csv_output = processor.export_to_csv(df, include_source=True)
        
        # Save full output
        filename = f'full_output_ni_{year}.csv'
        with open(filename, 'w') as f:
            f.write(csv_output)
        print(f"✅ Full output saved to {filename}")
        
        # Analyze what's in the output
        lines = csv_output.split('\n')
        
        # Find all unique holiday types in the output
        holiday_types_found = set()
        fallback_count = 0
        proper_match_count = 0
        
        for line in lines[1:]:  # Skip header
            if ';' in line:
                parts = line.split(';')
                if len(parts) >= 3:
                    source = parts[2]
                    
                    # Check for fallback
                    if '(fallback)' in source:
                        fallback_count += 1
                    elif 'School holiday:' in source:
                        proper_match_count += 1
                    
                    # Extract holiday type
                    for holiday in ['winterferien', 'osterferien', 'pfingstferien', 
                                  'sommerferien', 'herbstferien', 'weihnachtsferien']:
                        if holiday in source.lower():
                            holiday_types_found.add(holiday)
        
        print(f"\n📊 Analysis of output:")
        print(f"  Holiday types found: {', '.join(sorted(holiday_types_found))}")
        print(f"  Proper matches: {proper_match_count} intervals")
        print(f"  Fallbacks: {fallback_count} intervals")
        
        if fallback_count > 0:
            print(f"\n  ⚠️ {fallback_count} intervals using fallback!")
            
            # Show some examples of fallback
            print("  Examples of fallback usage:")
            count = 0
            for line in lines[1:]:
                if '(fallback)' in line and count < 3:
                    parts = line.split(';')
                    if len(parts) >= 3:
                        print(f"    {parts[0]}: {parts[2][:60]}...")
                        count += 1

if __name__ == "__main__":
    simulate_app()