"""Generate test data for the load profile simulator"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_test_load_profile(year: int = 2024, base_load: float = 1000.0) -> str:
    """Generate a synthetic load profile for testing"""
    
    data_lines = ["timestamp;load"]
    start_date = datetime(year, 1, 1, 0, 0)
    
    # Generate for entire year (96 intervals per day)
    for day in range(365):
        current_date = start_date + timedelta(days=day)
        
        # Vary load based on day type
        is_weekend = current_date.weekday() in [5, 6]
        is_summer = current_date.month in [6, 7, 8]
        is_winter = current_date.month in [12, 1, 2]
        
        # Base pattern for the day
        if is_weekend:
            day_multiplier = 0.8  # Lower load on weekends
        else:
            day_multiplier = 1.0
        
        # Seasonal adjustment
        if is_summer:
            season_multiplier = 1.2  # Higher cooling load
        elif is_winter:
            season_multiplier = 1.15  # Higher heating load
        else:
            season_multiplier = 1.0
        
        for interval in range(96):
            timestamp = current_date + timedelta(minutes=interval * 15)
            
            # Time of day pattern (peak during business hours)
            hour = timestamp.hour + timestamp.minute / 60
            if 7 <= hour <= 19:
                time_multiplier = 1.0 + 0.3 * np.sin((hour - 7) * np.pi / 12)
            else:
                time_multiplier = 0.7
            
            # Calculate load with some random variation
            load = base_load * day_multiplier * season_multiplier * time_multiplier
            load += random.gauss(0, 50)  # Add random noise
            load = max(load, 100)  # Ensure positive load
            
            # Format with German decimal separator
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M')
            load_str = f"{load:.2f}".replace('.', ',')
            data_lines.append(f"{timestamp_str};{load_str}")
    
    return '\n'.join(data_lines)

if __name__ == "__main__":
    # Generate test file
    test_data = generate_test_load_profile(2024)
    
    with open("test_load_profile_2024.csv", "w", encoding="utf-8") as f:
        f.write(test_data)
    
    print("✅ Test data generated: test_load_profile_2024.csv")
    print(f"📊 File contains {test_data.count(chr(10))} lines")