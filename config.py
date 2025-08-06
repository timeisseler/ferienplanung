"""Configuration for the load profile simulation tool"""

# API endpoints
HOLIDAY_API_URL = "https://get.api-feiertage.de"
SCHOOL_HOLIDAY_API_URL = "https://ferien-api.de/api/v1/"

# German federal states
FEDERAL_STATES = {
    "BW": "Baden-Württemberg",
    "BY": "Bayern", 
    "BE": "Berlin",
    "BB": "Brandenburg",
    "HB": "Bremen",
    "HH": "Hamburg",
    "HE": "Hessen",
    "MV": "Mecklenburg-Vorpommern",
    "NI": "Niedersachsen",
    "NW": "Nordrhein-Westfalen",
    "RP": "Rheinland-Pfalz",
    "SL": "Saarland",
    "SN": "Sachsen",
    "ST": "Sachsen-Anhalt",
    "SH": "Schleswig-Holstein",
    "TH": "Thüringen"
}

# Load profile settings
INTERVALS_PER_DAY = 96  # 15-minute intervals
INTERVAL_MINUTES = 15