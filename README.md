#Tool for simulating a load profile into the future

Description: The tool helps its user by simulating a load profile into the next years. 
It is written in python and the frontend is built with streamlit.

For that it takes in the following inputs:

1. Load profile of a year with timestamp, format: 

timestamp;load
2025-01-01 00:00;1039,44
2025-01-01 00:15;1016,96
2025-01-01 00:30;1031,84
2025-01-01 00:45;972,96
2025-01-01 01:00;1048,88
2025-01-01 01:15;985,84
...

2. The required years into the future as an input (e.g. 2026, 2027, ...)

3. The federal state of the uploaded load profile

#What does it do?


1. It grabs all the holidays, holiday days and weekends for the federal state, using https://www.api-feiertage.de/ for holiday days, https://ferien-api.de/ for holidays.
2. It divides the load profile in chunks of days (96 intervals)
3. It build a new load profile in which the chunks of load profiles of holidays, holiday-days or weekends are in the same holiday, holiday-day or weekend in the respective year in the future. (e.g. the load profile for the weekend of KW42 2024 is on the weekend of KW42 2026 and the load profiles of summer holidays 2024 are in the summer holidays of 2026,...)
4. the rest of the year the load profile is the same as in the original year, besides the holidays, and weekends.

The goal is to get a realistic load profile for the years in the future where seasonality, holiday and weekend based anomalies are mapped correctly.

The resulting load profiles should then be downloadable as a csv file in the same format as the input sheet but with comments on where the chunk of load profile comes from (e.g. normal day, weekend KW42, summer-holidays etc.)
