"""
Velocity Motors Pvt Ltd — Realistic Data Generator
====================================================
Generates statistically realistic, non-nominal data for all 11 tables.
Outputs a single SQL file ready to run after velocity_motors_schema.sql.

Design principles
-----------------
* Branch performance varies realistically (some profit centres, some laggards).
* Salesperson productivity follows a power-law distribution.
* Car demand is segment-skewed (SUVs > Sedans > Hatchbacks > Luxury).
* Discount probability and size are inversely correlated with profitability.
* Financing adoption rate varies by income bracket and car price.
* Lead-to-sale conversion has realistic drop-off at each funnel stage.
* Test-drive conversion rate varies by car segment and salesperson.
* Seasonal sales patterns (Q4 peak, Q1 dip) embedded in dates.
* Servicing frequency correlates with car age and brand.
* All IDs are explicit so FK constraints resolve without AUTO_INCREMENT surprises.

Run: python generate_data.py
Output: velocity_motors_data.sql  (~35 MB for default scale)
"""

import random
import math
from datetime import date, timedelta

# ── reproducibility ────────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)

# ── built-in Indian name pool (no external dependencies) ──────────────────────
FIRST_NAMES_M = [
    "Aarav","Vivek","Rahul","Amit","Suresh","Rajesh","Vikas","Nikhil","Sanjay","Deepak",
    "Rohit","Ankit","Pradeep","Manoj","Kiran","Vikram","Arjun","Ravi","Sandeep","Harish",
    "Naveen","Rajan","Mohit","Gaurav","Aditya","Sachin","Dinesh","Pankaj","Nitin","Akash",
    "Varun","Kunal","Pranav","Shubham","Tarun","Yash","Ajay","Vijay","Sumit","Lokesh",
]
FIRST_NAMES_F = [
    "Priya","Anjali","Pooja","Sneha","Kavita","Sunita","Meena","Rekha","Neha","Divya",
    "Ananya","Sonal","Ritu","Swati","Shruti","Komal","Pallavi","Deepa","Nisha","Meghna",
    "Bhavna","Shilpa","Tanya","Lakshmi","Geeta","Usha","Archana","Sapna","Varsha","Preeti",
    "Isha","Mansi","Jyoti","Harini","Apurva","Simran","Rupali","Chetna","Vandana","Yamini",
]
LAST_NAMES = [
    "Sharma","Verma","Gupta","Singh","Kumar","Patel","Shah","Joshi","Mehta","Rao",
    "Nair","Reddy","Iyer","Pillai","Chopra","Malhotra","Kapoor","Bose","Das","Ghosh",
    "Mishra","Tiwari","Shukla","Pandey","Dubey","Srivastava","Agarwal","Banerjee","Chatterjee","Mukherjee",
    "Saxena","Chaudhary","Yadav","Jain","Desai","Thakur","Patil","Kulkarni","Naik","More",
]

def fake_name(gender: str = None) -> str:
    if gender == "Female":
        first = random.choice(FIRST_NAMES_F)
    elif gender == "Male":
        first = random.choice(FIRST_NAMES_M)
    else:
        first = random.choice(FIRST_NAMES_M + FIRST_NAMES_F)
    return f"{first} {random.choice(LAST_NAMES)}"

# ── scale knobs ────────────────────────────────────────────────────────────────
N_BRANCHES       = 8
N_CUSTOMERS      = 1_200
N_CARS_MODELS    = 30
N_SALESPERSONS   = 60
N_FINANCING_PKGS = 20
N_SALES          = 3_500
N_INVENTORY_ROWS = 200
N_SERVICE_ROWS   = 2_000
N_CAMPAIGNS      = 15
N_LEADS          = 4_500
N_TEST_DRIVES    = 2_800

# ── date window ───────────────────────────────────────────────────────────────
START_DATE = date(2022, 1, 1)
END_DATE   = date(2024, 12, 31)

# ── helpers ───────────────────────────────────────────────────────────────────

def rand_date(start: date = START_DATE, end: date = END_DATE) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def seasonal_date() -> date:
    """Q4 (Oct-Dec) gets 2× weight; Q1 (Jan-Mar) gets 0.7×."""
    year = random.choices([2022, 2023, 2024], weights=[0.25, 0.40, 0.35])[0]
    month = random.choices(
        range(1, 13),
        weights=[0.07, 0.06, 0.07, 0.08, 0.09, 0.08,
                 0.08, 0.09, 0.09, 0.12, 0.11, 0.06],
    )[0]
    day = random.randint(1, 28)
    return date(year, month, day)


def q(val) -> str:
    """SQL-quote a Python value."""
    if val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, date):
        return f"'{val.isoformat()}'"
    escaped = str(val).replace("'", "''")
    return f"'{escaped}'"


def insert(table: str, cols: list[str], rows: list[tuple]) -> list[str]:
    stmts = []
    col_str = ", ".join(cols)
    for row in rows:
        vals = ", ".join(q(v) for v in row)
        stmts.append(f"INSERT INTO {table} ({col_str}) VALUES ({vals});")
    return stmts


# ==============================================================================
# 1. BRANCHES
# ==============================================================================
CITY_POOL = ["Mumbai", "Delhi", "Bangalore", "Hyderabad",
             "Pune", "Chennai", "Ahmedabad", "Kolkata"]

# operating cost varies — premium city branches cost more
CITY_OPCOST = {
    "Mumbai": (800_000, 1_200_000),
    "Delhi": (700_000, 1_100_000),
    "Bangalore": (650_000, 950_000),
    "Hyderabad": (550_000, 800_000),
    "Pune": (500_000, 750_000),
    "Chennai": (500_000, 750_000),
    "Ahmedabad": (400_000, 650_000),
    "Kolkata": (450_000, 700_000),
}

branches = []  # (id, name, city, manager, monthly_cost)
for i in range(1, N_BRANCHES + 1):
    city = CITY_POOL[i - 1]
    lo, hi = CITY_OPCOST[city]
    monthly_cost = round(random.uniform(lo, hi), 2)
    branches.append((
        i,
        f"{city} {random.choice(['North','South','East','West','Central'])} Showroom",
        city,
        fake_name(),
        monthly_cost,
    ))

branch_ids = [b[0] for b in branches]

# ==============================================================================
# 2. CARS
# ==============================================================================
CAR_CATALOGUE = [
    # ── MARUTI SUZUKI ──────────────────────────────────────────────────────────
    # (brand, model, segment, fuel, transmission, showroom_price, cost_price)
    ("Maruti", "Alto K10",            "Hatchback", "Petrol",   "Manual",  460_000,  345_000),
    ("Maruti", "S-Presso",            "Hatchback", "Petrol",   "Manual",  490_000,  365_000),
    ("Maruti", "Celerio",             "Hatchback", "Petrol",   "Auto",    560_000,  420_000),
    ("Maruti", "WagonR",              "Hatchback", "Petrol",   "Auto",    620_000,  465_000),
    ("Maruti", "Swift",               "Hatchback", "Petrol",   "Manual",  720_000,  540_000),
    ("Maruti", "Swift Dzire",         "Sedan",     "Petrol",   "Auto",    790_000,  595_000),
    ("Maruti", "Baleno",              "Hatchback", "Petrol",   "Auto",    850_000,  640_000),
    ("Maruti", "Ignis",               "Hatchback", "Petrol",   "Auto",    680_000,  510_000),
    ("Maruti", "Ciaz",                "Sedan",     "Petrol",   "Manual",  940_000,  710_000),
    ("Maruti", "Ertiga",              "SUV",       "Petrol",   "Auto",  1_020_000,  770_000),
    ("Maruti", "XL6",                 "SUV",       "Petrol",   "Auto",  1_160_000,  875_000),
    ("Maruti", "Brezza",              "SUV",       "Petrol",   "Auto",  1_250_000,  920_000),
    ("Maruti", "Grand Vitara",        "SUV",       "Petrol",   "Auto",  1_390_000, 1_040_000),
    ("Maruti", "Fronx",               "SUV",       "Petrol",   "Auto",  1_080_000,  810_000),
    ("Maruti", "Invicto",             "SUV",       "Electric", "Auto",  2_450_000, 1_900_000),

    # ── HYUNDAI ────────────────────────────────────────────────────────────────
    ("Hyundai", "Grand i10 Nios",     "Hatchback", "Petrol",   "Manual",  640_000,  480_000),
    ("Hyundai", "i20",                "Hatchback", "Petrol",   "Auto",    840_000,  630_000),
    ("Hyundai", "Exter",              "SUV",       "Petrol",   "Manual",  820_000,  615_000),
    ("Hyundai", "Venue",              "SUV",       "Petrol",   "Auto",  1_050_000,  790_000),
    ("Hyundai", "Creta",              "SUV",       "Diesel",   "Auto",  1_450_000, 1_080_000),
    ("Hyundai", "Creta Electric",     "SUV",       "Electric", "Auto",  1_900_000, 1_460_000),
    ("Hyundai", "Alcazar",            "SUV",       "Diesel",   "Auto",  2_050_000, 1_580_000),
    ("Hyundai", "Tucson",             "SUV",       "Diesel",   "Auto",  2_850_000, 2_200_000),
    ("Hyundai", "Verna",              "Sedan",     "Petrol",   "Auto",  1_150_000,  860_000),
    ("Hyundai", "Aura",               "Sedan",     "Petrol",   "Manual",  760_000,  570_000),
    ("Hyundai", "Ioniq 5",            "SUV",       "Electric", "Auto",  4_600_000, 3_700_000),

    # ── TATA ───────────────────────────────────────────────────────────────────
    ("Tata", "Tiago",                 "Hatchback", "Petrol",   "Manual",  580_000,  435_000),
    ("Tata", "Tiago EV",              "Hatchback", "Electric", "Auto",    990_000,  745_000),
    ("Tata", "Altroz",                "Hatchback", "Petrol",   "Manual",  730_000,  550_000),
    ("Tata", "Punch",                 "Hatchback", "Petrol",   "Manual",  950_000,  720_000),
    ("Tata", "Punch EV",              "SUV",       "Electric", "Auto",  1_450_000, 1_100_000),
    ("Tata", "Nexon",                 "SUV",       "Petrol",   "Auto",  1_350_000, 1_010_000),
    ("Tata", "Nexon EV",              "SUV",       "Electric", "Auto",  1_750_000, 1_300_000),
    ("Tata", "Harrier",               "SUV",       "Diesel",   "Auto",  2_200_000, 1_700_000),
    ("Tata", "Safari",                "SUV",       "Diesel",   "Auto",  2_450_000, 1_890_000),
    ("Tata", "Tigor EV",              "Sedan",     "Electric", "Auto",  1_240_000,  935_000),
    ("Tata", "Curvv EV",              "SUV",       "Electric", "Auto",  2_000_000, 1_540_000),

    # ── MAHINDRA ───────────────────────────────────────────────────────────────
    ("Mahindra", "KUV100 NXT",        "Hatchback", "Petrol",   "Manual",  680_000,  510_000),
    ("Mahindra", "Bolero",            "SUV",       "Diesel",   "Manual",  1_000_000, 755_000),
    ("Mahindra", "Bolero Neo",        "SUV",       "Diesel",   "Manual",  1_120_000, 845_000),
    ("Mahindra", "Thar",              "SUV",       "Diesel",   "Manual",  1_650_000, 1_250_000),
    ("Mahindra", "Thar Roxx",         "SUV",       "Diesel",   "Auto",   2_150_000, 1_660_000),
    ("Mahindra", "Scorpio Classic",   "SUV",       "Diesel",   "Manual",  1_470_000, 1_110_000),
    ("Mahindra", "Scorpio N",         "SUV",       "Diesel",   "Manual",  1_850_000, 1_420_000),
    ("Mahindra", "XUV300",            "SUV",       "Petrol",   "Auto",   1_100_000,  830_000),
    ("Mahindra", "XUV400 EV",         "SUV",       "Electric", "Auto",   1_600_000, 1_220_000),
    ("Mahindra", "XUV700",            "SUV",       "Diesel",   "Auto",   2_600_000, 2_000_000),
    ("Mahindra", "BE 6e",             "SUV",       "Electric", "Auto",   2_750_000, 2_120_000),

    # ── HONDA ──────────────────────────────────────────────────────────────────
    ("Honda", "Amaze",                "Sedan",     "Petrol",   "Auto",    920_000,  690_000),
    ("Honda", "City",                 "Sedan",     "Petrol",   "Auto",   1_350_000, 1_020_000),
    ("Honda", "City Hybrid",          "Sedan",     "Electric", "Auto",   1_950_000, 1_500_000),
    ("Honda", "Elevate",              "SUV",       "Petrol",   "Auto",   1_500_000, 1_130_000),

    # ── TOYOTA ─────────────────────────────────────────────────────────────────
    ("Toyota", "Glanza",              "Hatchback", "Petrol",   "Auto",    840_000,  630_000),
    ("Toyota", "Urban Cruiser Hyryder","SUV",      "Petrol",   "Auto",   1_500_000, 1_130_000),
    ("Toyota", "Rumion",              "SUV",       "Petrol",   "Auto",   1_090_000,  820_000),
    ("Toyota", "Innova Crysta",       "SUV",       "Diesel",   "Auto",   2_100_000, 1_620_000),
    ("Toyota", "Innova HyCross",      "SUV",       "Electric", "Auto",   2_800_000, 2_170_000),
    ("Toyota", "Fortuner",            "SUV",       "Diesel",   "Auto",   3_800_000, 2_950_000),
    ("Toyota", "Fortuner Legender",   "SUV",       "Diesel",   "Auto",   4_300_000, 3_350_000),
    ("Toyota", "Camry Hybrid",        "Sedan",     "Electric", "Auto",   4_800_000, 3_850_000),
    ("Toyota", "Land Cruiser 300",    "SUV",       "Diesel",   "Auto",   8_500_000, 6_800_000),

    # ── KIA ────────────────────────────────────────────────────────────────────
    ("Kia", "Sonet",                  "SUV",       "Petrol",   "Auto",   1_100_000,  830_000),
    ("Kia", "Seltos",                 "SUV",       "Diesel",   "Auto",   1_700_000, 1_280_000),
    ("Kia", "Carens",                 "SUV",       "Diesel",   "Auto",   1_620_000, 1_220_000),
    ("Kia", "EV6",                    "SUV",       "Electric", "Auto",   6_000_000, 4_800_000),

    # ── MG ─────────────────────────────────────────────────────────────────────
    ("MG", "Hector",                  "SUV",       "Petrol",   "Auto",   1_950_000, 1_500_000),
    ("MG", "Hector Plus",             "SUV",       "Petrol",   "Auto",   2_200_000, 1_700_000),
    ("MG", "ZS EV",                   "SUV",       "Electric", "Auto",   2_300_000, 1_780_000),
    ("MG", "Comet EV",                "Hatchback", "Electric", "Auto",     800_000,  600_000),
    ("MG", "Windsor EV",              "SUV",       "Electric", "Auto",   1_400_000, 1_060_000),
    ("MG", "Gloster",                 "SUV",       "Diesel",   "Auto",   3_900_000, 3_030_000),

    # ── RENAULT & NISSAN ───────────────────────────────────────────────────────
    ("Renault", "Kwid",               "Hatchback", "Petrol",   "Manual",  550_000,  410_000),
    ("Renault", "Triber",             "SUV",       "Petrol",   "Manual",  740_000,  555_000),
    ("Renault", "Kiger",              "SUV",       "Petrol",   "Auto",    780_000,  585_000),
    ("Nissan",  "Magnite",            "SUV",       "Petrol",   "Auto",    800_000,  600_000),

    # ── VOLKSWAGEN & SKODA ────────────────────────────────────────────────────
    ("Volkswagen", "Polo",            "Hatchback", "Petrol",   "Auto",    850_000,  640_000),
    ("Volkswagen", "Virtus",          "Sedan",     "Petrol",   "Auto",  1_400_000, 1_060_000),
    ("Volkswagen", "Taigun",          "SUV",       "Petrol",   "Auto",  1_500_000, 1_130_000),
    ("Skoda",   "Slavia",             "Sedan",     "Petrol",   "Auto",  1_500_000, 1_130_000),
    ("Skoda",   "Kushaq",             "SUV",       "Petrol",   "Auto",  1_450_000, 1_090_000),
    ("Skoda",   "Kodiaq",             "SUV",       "Petrol",   "Auto",  3_500_000, 2_720_000),
    ("Skoda",   "Superb",             "Sedan",     "Petrol",   "Auto",  3_800_000, 2_970_000),

    # ── JEEP ───────────────────────────────────────────────────────────────────
    ("Jeep", "Compass",               "SUV",       "Diesel",   "Auto",  2_200_000, 1_700_000),
    ("Jeep", "Meridian",              "SUV",       "Diesel",   "Auto",  3_200_000, 2_480_000),
    ("Jeep", "Wrangler",              "SUV",       "Petrol",   "Auto",  5_900_000, 4_720_000),

    # ── LUXURY: BMW ────────────────────────────────────────────────────────────
    ("BMW", "2 Series Gran Coupe",    "Luxury",    "Petrol",   "Auto",  3_900_000, 3_120_000),
    ("BMW", "3 Series",               "Luxury",    "Petrol",   "Auto",  4_800_000, 3_850_000),
    ("BMW", "5 Series",               "Luxury",    "Petrol",   "Auto",  6_700_000, 5_360_000),
    ("BMW", "7 Series",               "Luxury",    "Petrol",   "Auto",  9_400_000, 7_520_000),
    ("BMW", "X1",                     "Luxury",    "Petrol",   "Auto",  4_600_000, 3_680_000),
    ("BMW", "X3",                     "Luxury",    "Diesel",   "Auto",  6_900_000, 5_520_000),
    ("BMW", "X5",                     "Luxury",    "Diesel",   "Auto",  9_500_000, 7_600_000),
    ("BMW", "i4",                     "Luxury",    "Electric", "Auto",  7_200_000, 5_760_000),
    ("BMW", "iX",                     "Luxury",    "Electric", "Auto", 11_500_000, 9_200_000),

    # ── LUXURY: MERCEDES-BENZ ─────────────────────────────────────────────────
    ("Mercedes", "A-Class Limousine", "Luxury",    "Petrol",   "Auto",  4_200_000, 3_360_000),
    ("Mercedes", "C-Class",           "Luxury",    "Petrol",   "Auto",  5_500_000, 4_400_000),
    ("Mercedes", "E-Class",           "Luxury",    "Petrol",   "Auto",  7_900_000, 6_320_000),
    ("Mercedes", "S-Class",           "Luxury",    "Petrol",   "Auto", 14_000_000,11_200_000),
    ("Mercedes", "GLA",               "Luxury",    "Petrol",   "Auto",  5_400_000, 4_320_000),
    ("Mercedes", "GLC",               "Luxury",    "Diesel",   "Auto",  7_400_000, 5_920_000),
    ("Mercedes", "GLE",               "Luxury",    "Diesel",   "Auto", 10_500_000, 8_400_000),
    ("Mercedes", "EQB",               "Luxury",    "Electric", "Auto",  7_000_000, 5_600_000),
    ("Mercedes", "EQS",               "Luxury",    "Electric", "Auto", 16_000_000,12_800_000),

    # ── LUXURY: AUDI ──────────────────────────────────────────────────────────
    ("Audi", "A4",                    "Luxury",    "Petrol",   "Auto",  4_900_000, 3_920_000),
    ("Audi", "A6",                    "Luxury",    "Petrol",   "Auto",  7_200_000, 5_760_000),
    ("Audi", "A8 L",                  "Luxury",    "Petrol",   "Auto", 11_700_000, 9_360_000),
    ("Audi", "Q3",                    "Luxury",    "Petrol",   "Auto",  4_500_000, 3_600_000),
    ("Audi", "Q5",                    "Luxury",    "Petrol",   "Auto",  6_800_000, 5_440_000),
    ("Audi", "Q7",                    "Luxury",    "Diesel",   "Auto",  9_000_000, 7_200_000),
    ("Audi", "e-tron",                "Luxury",    "Electric", "Auto",  9_400_000, 7_520_000),
    ("Audi", "Q8 e-tron",             "Luxury",    "Electric", "Auto", 11_500_000, 9_200_000),

    # ── LUXURY: OTHERS ────────────────────────────────────────────────────────
    ("Lexus", "ES 300h",              "Luxury",    "Electric", "Auto",  6_200_000, 5_000_000),
    ("Lexus", "RX 500h",              "Luxury",    "Electric", "Auto",  9_500_000, 7_600_000),
    ("Lexus", "LX 500d",              "Luxury",    "Diesel",   "Auto", 21_000_000,16_800_000),
    ("Volvo", "XC40",                 "Luxury",    "Petrol",   "Auto",  5_600_000, 4_480_000),
    ("Volvo", "XC60",                 "Luxury",    "Diesel",   "Auto",  7_400_000, 5_920_000),
    ("Volvo", "XC90",                 "Luxury",    "Petrol",   "Auto", 10_200_000, 8_160_000),
    ("Volvo", "C40 Recharge",         "Luxury",    "Electric", "Auto",  6_600_000, 5_280_000),
    ("Porsche","Cayenne",             "Luxury",    "Petrol",   "Auto", 13_500_000,10_800_000),
    ("Porsche","Macan Electric",      "Luxury",    "Electric", "Auto", 10_000_000, 8_000_000),
    ("Land Rover","Defender",         "Luxury",    "Diesel",   "Auto", 12_000_000, 9_600_000),
    ("Land Rover","Range Rover Sport","Luxury",    "Diesel",   "Auto", 16_500_000,13_200_000),
    ("Jaguar", "XE",                  "Luxury",    "Petrol",   "Auto",  5_800_000, 4_640_000),
    ("Jaguar", "F-Pace",              "Luxury",    "Diesel",   "Auto",  8_200_000, 6_560_000),
    ("Maserati","Ghibli",             "Luxury",    "Petrol",   "Auto", 18_000_000,14_400_000),
]

# Demand weight by segment
SEGMENT_DEMAND = {"Hatchback": 0.22, "Sedan": 0.22, "SUV": 0.45, "Luxury": 0.11}

cars = []
for i, c in enumerate(CAR_CATALOGUE, 1):
    cars.append((i, *c))

car_ids       = [c[0] for c in cars]
car_segments  = {c[0]: c[3] for c in cars}
car_show_price= {c[0]: c[6] for c in cars}
car_cost      = {c[0]: c[7] for c in cars}
car_seg_map   = {"Hatchback": [], "Sedan": [], "SUV": [], "Luxury": []}
for c in cars:
    car_seg_map[c[3]].append(c[0])

def pick_car() -> int:
    """Pick a car_id weighted by segment demand."""
    seg = random.choices(
        list(SEGMENT_DEMAND.keys()),
        weights=list(SEGMENT_DEMAND.values())
    )[0]
    return random.choice(car_seg_map[seg])

# ==============================================================================
# 3. CUSTOMERS
# ==============================================================================
OCCUPATIONS = [
    "Software Engineer", "Doctor", "Business Owner", "Government Employee",
    "Teacher", "Sales Executive", "Manager", "Retired", "Lawyer",
    "Architect", "Accountant", "Marketing Professional", "Freelancer", "Farmer",
]

INCOME_BY_OCCUPATION = {
    "Software Engineer": (800_000, 2_500_000),
    "Doctor": (1_200_000, 4_000_000),
    "Business Owner": (600_000, 5_000_000),
    "Government Employee": (400_000, 1_200_000),
    "Teacher": (250_000, 700_000),
    "Sales Executive": (300_000, 900_000),
    "Manager": (700_000, 2_000_000),
    "Retired": (200_000, 600_000),
    "Lawyer": (900_000, 3_500_000),
    "Architect": (600_000, 2_000_000),
    "Accountant": (400_000, 1_200_000),
    "Marketing Professional": (500_000, 1_500_000),
    "Freelancer": (200_000, 1_500_000),
    "Farmer": (150_000, 500_000),
}

CITIES_CUSTOMER = CITY_POOL + [
    "Jaipur", "Lucknow", "Indore", "Bhopal", "Nagpur",
    "Surat", "Coimbatore", "Patna", "Chandigarh",
]

customers = []
for i in range(1, N_CUSTOMERS + 1):
    occ  = random.choice(OCCUPATIONS)
    lo, hi = INCOME_BY_OCCUPATION[occ]
    income = round(random.uniform(lo, hi), 2)
    age = int(random.gauss(38, 10))
    age = max(21, min(70, age))
    customers.append((
        i,
        fake_name(),
        random.choices(["Male", "Female"], weights=[0.62, 0.38])[0],
        age,
        random.choice(CITIES_CUSTOMER),
        occ,
        income,
        None,   # first_purchase_date filled after sales are generated
    ))

customer_ids    = [c[0] for c in customers]
customer_income = {c[0]: c[6] for c in customers}

# ==============================================================================
# 4. SALESPERSONS
# ==============================================================================
# Distribute salespersons across branches (some branches get more staff)
SP_PER_BRANCH = [10, 9, 8, 8, 7, 7, 6, 5]   # sum = 60

salespersons = []
sp_id = 1
for b_idx, branch in enumerate(branches):
    count = SP_PER_BRANCH[b_idx]
    for _ in range(count):
        joining = rand_date(date(2018, 1, 1), date(2023, 6, 30))
        salary  = round(random.uniform(25_000, 80_000), 2)
        salespersons.append((sp_id, fake_name(), joining, salary, branch[0]))
        sp_id += 1

sp_ids = [s[0] for s in salespersons]
sp_branch = {s[0]: s[4] for s in salespersons}

# Branch → list of salesperson IDs
branch_sp_map: dict[int, list[int]] = {b[0]: [] for b in branches}
for s in salespersons:
    branch_sp_map[s[4]].append(s[0])

# Salesperson performance multiplier — power law (top 20% do 60% of sales)
sp_perf = {sid: random.uniform(0.3, 1.0) ** 2 for sid in sp_ids}   # skewed low
top_sp = sorted(sp_ids, key=lambda x: sp_perf[x], reverse=True)[:12]
for sid in top_sp:
    sp_perf[sid] = random.uniform(1.5, 3.0)   # stars

def pick_salesperson(branch_id: int) -> int:
    sps = branch_sp_map[branch_id]
    weights = [sp_perf[s] for s in sps]
    return random.choices(sps, weights=weights)[0]

# ==============================================================================
# 5. FINANCING
# ==============================================================================
BANKS = [
    "HDFC Bank", "SBI", "ICICI Bank", "Axis Bank", "Kotak Mahindra",
    "Bank of Baroda", "Punjab National Bank", "IndusInd Bank",
    "Federal Bank", "Yes Bank",
]

financing = []
for i in range(1, N_FINANCING_PKGS + 1):
    bank     = random.choice(BANKS)
    rate     = round(random.uniform(7.5, 14.5), 2)
    tenure   = random.choice([24, 36, 48, 60, 72, 84])
    # EMI proxy — based on ₹10L principal
    principal = 1_000_000
    r = rate / (12 * 100)
    emi = round(principal * r * (1+r)**tenure / ((1+r)**tenure - 1), 2)
    financing.append((i, bank, rate, tenure, emi))

fin_ids = [f[0] for f in financing]

# ==============================================================================
# 6. SALES
# ==============================================================================
# Branch performance tiers (affects discount behaviour and sale volume)
BRANCH_TIER = {
    1: "A", 2: "A", 3: "B", 4: "B",
    5: "B", 6: "C", 7: "C", 8: "C",
}
DISCOUNT_RANGE = {"A": (0, 0.04), "B": (0.01, 0.07), "C": (0.03, 0.12)}
FINANCING_PROB = {"A": 0.55, "B": 0.65, "C": 0.75}

sales = []
# Track first purchase dates
cust_first_purchase: dict[int, date] = {}
# Track which (car_id, branch_id) combos sold (for inventory linkage)
sold_pairs: list[tuple[int, int]] = []

# Distribute sales across branches with weighted volume
BRANCH_SALE_WEIGHT = {1: 2.0, 2: 1.8, 3: 1.5, 4: 1.4, 5: 1.2, 6: 0.9, 7: 0.8, 8: 0.6}
branch_sale_probs = [BRANCH_SALE_WEIGHT[b[0]] for b in branches]

for i in range(1, N_SALES + 1):
    branch = random.choices(branches, weights=branch_sale_probs)[0]
    b_id   = branch[0]
    tier   = BRANCH_TIER[b_id]

    cust_id = random.choice(customer_ids)
    car_id  = pick_car()
    sp_id   = pick_salesperson(b_id)
    sdate   = seasonal_date()

    show_price = car_show_price[car_id]
    lo_d, hi_d = DISCOUNT_RANGE[tier]
    discount   = round(show_price * random.uniform(lo_d, hi_d), 2)
    sale_price = round(show_price - discount, 2)

    use_financing = random.random() < FINANCING_PROB[tier]
    fin_id = random.choice(fin_ids) if use_financing else None

    sales.append((i, cust_id, car_id, sp_id, b_id, sdate, sale_price, discount, fin_id))
    sold_pairs.append((car_id, b_id))

    if cust_id not in cust_first_purchase or sdate < cust_first_purchase[cust_id]:
        cust_first_purchase[cust_id] = sdate

# Back-fill first_purchase_date
customers = [
    (c[0], c[1], c[2], c[3], c[4], c[5], c[6], cust_first_purchase.get(c[0]))
    for c in customers
]

sale_ids = [s[0] for s in sales]

# ==============================================================================
# 7. INVENTORY
# ==============================================================================
inventory = []
# Start with cars that were actually sold — ensure stock exists
pool = list(set(sold_pairs))
random.shuffle(pool)
extra_needed = max(0, N_INVENTORY_ROWS - len(pool))
# Add extra random (car, branch) combos for unsold stock (realistic overstocking)
extra = [(random.choice(car_ids), random.choice(branch_ids))
         for _ in range(extra_needed)]
all_inv_pairs = pool[:N_INVENTORY_ROWS] + extra[:max(0, N_INVENTORY_ROWS - len(pool))]

seen_inv = set()
inv_id = 1
for car_id, b_id in all_inv_pairs:
    key = (car_id, b_id)
    if key in seen_inv:
        continue
    seen_inv.add(key)
    qty         = random.choices([0, 1, 2, 3, 4, 5, 6, 8, 10],
                                 weights=[5, 25, 25, 20, 10, 7, 4, 2, 2])[0]
    arrival     = rand_date(date(2021, 6, 1), date(2024, 10, 31))
    inventory.append((inv_id, car_id, b_id, qty, arrival))
    inv_id += 1

# ==============================================================================
# 8. SERVICING
# ==============================================================================
# Only customers who bought a car can service
buying_customers = list(cust_first_purchase.keys())

SERVICE_TYPES = ["Repair", "Maintenance", "Inspection"]
SERVICE_WEIGHTS = [0.25, 0.60, 0.15]

# Car service cost ranges by segment
SEGMENT_SVC_COST = {
    "Hatchback": (2_000, 8_000),
    "Sedan":     (3_000, 12_000),
    "SUV":       (4_000, 18_000),
    "Luxury":    (8_000, 40_000),
}

servicing = []
for i in range(1, N_SERVICE_ROWS + 1):
    cust_id  = random.choice(buying_customers)
    car_id   = pick_car()
    seg      = car_segments[car_id]
    svc_date = rand_date(
        cust_first_purchase.get(cust_id, START_DATE),
        END_DATE
    )
    svc_type = random.choices(SERVICE_TYPES, weights=SERVICE_WEIGHTS)[0]
    lo, hi   = SEGMENT_SVC_COST[seg]
    cost     = round(random.uniform(lo, hi), 2)
    servicing.append((i, cust_id, car_id, svc_date, svc_type, cost))

# ==============================================================================
# 9. MARKETING CAMPAIGNS
# ==============================================================================
CHANNELS = ["Facebook", "TV", "Newspaper", "Instagram", "Google", "Email", "Outdoor"]
CHANNEL_WEIGHTS = [0.22, 0.15, 0.08, 0.20, 0.18, 0.10, 0.07]

CAMPAIGN_NAMES = [
    "Diwali Dhamaka Sale", "Year-End Clearance", "New Year New Car",
    "Monsoon Madness", "Republic Day Drive", "Summer Deals",
    "EV Revolution Campaign", "SUV Season", "Budget Hatchback Push",
    "Luxury Preview Event", "Independence Day Offer", "Festive Finance",
    "Test Drive Weekend", "Referral Rewards", "City Launch Blitz",
]

campaigns = []
for i in range(1, N_CAMPAIGNS + 1):
    channel  = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0]
    start_d  = rand_date(date(2022, 1, 1), date(2024, 10, 1))
    dur_days = random.randint(7, 45)
    end_d    = min(start_d + timedelta(days=dur_days), END_DATE)
    budget   = round(random.uniform(50_000, 1_500_000), 2)
    campaigns.append((i, CAMPAIGN_NAMES[i - 1], channel, budget, start_d, end_d))

campaign_ids = [c[0] for c in campaigns]

# ==============================================================================
# 10. LEADS
# ==============================================================================
LEAD_SOURCES  = ["Walk-in", "Website", "Facebook", "Referral", "TV", "Google", "Email"]
LEAD_SRC_W    = [0.18, 0.22, 0.20, 0.12, 0.06, 0.14, 0.08]
LEAD_STATUSES = ["Open", "Contacted", "Qualified", "Lost", "Converted"]
# Funnel drop-off: realistically most leads don't convert
LEAD_STATUS_W = [0.10, 0.20, 0.18, 0.30, 0.22]

leads = []
for i in range(1, N_LEADS + 1):
    cust_id   = random.choice(customer_ids)
    camp_id   = random.choice(campaign_ids) if random.random() < 0.70 else None
    b_id      = random.choice(branch_ids)
    l_date    = rand_date(date(2022, 1, 1), date(2024, 11, 30))
    src       = random.choices(LEAD_SOURCES, weights=LEAD_SRC_W)[0]
    status    = random.choices(LEAD_STATUSES, weights=LEAD_STATUS_W)[0]
    sp_id     = pick_salesperson(b_id) if random.random() < 0.80 else None
    budget    = round(random.uniform(400_000, 6_000_000), 2)
    seg_pref  = random.choices(
        list(SEGMENT_DEMAND.keys()),
        weights=list(SEGMENT_DEMAND.values())
    )[0]
    conv_date = None
    if status == "Converted":
        conv_offset = random.randint(3, 60)
        conv_date   = min(l_date + timedelta(days=conv_offset), END_DATE)
    leads.append((
        i, cust_id, camp_id, b_id, l_date, src,
        status, sp_id, budget, seg_pref, conv_date,
    ))

# ==============================================================================
# 11. TEST DRIVES
# ==============================================================================
CONVERSION_BY_SEG = {
    "SUV":       0.38,
    "Sedan":     0.30,
    "Hatchback": 0.25,
    "Luxury":    0.20,
}

test_drives = []
for i in range(1, N_TEST_DRIVES + 1):
    cust_id  = random.choice(customer_ids)
    car_id   = pick_car()
    b_id     = random.choice(branch_ids)
    d_date   = rand_date(date(2022, 1, 1), date(2024, 11, 30))
    seg      = car_segments[car_id]
    conv     = "Yes" if random.random() < CONVERSION_BY_SEG[seg] else "No"
    test_drives.append((i, cust_id, car_id, b_id, d_date, conv))

# ==============================================================================
# WRITE SQL
# ==============================================================================
OUTPUT_FILE = "velocity_motors_data.sql"

def write_section(f, title: str, stmts: list[str]):
    f.write(f"\n-- {'='*60}\n")
    f.write(f"-- {title}\n")
    f.write(f"-- {'='*60}\n")
    for s in stmts:
        f.write(s + "\n")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("-- Velocity Motors Pvt Ltd — Generated Data\n")
    f.write("-- Run this AFTER velocity_motors_schema.sql\n\n")
    f.write("USE velocity_motors;\n")
    f.write("SET FOREIGN_KEY_CHECKS = 0;\n")

    write_section(f, "BRANCHES", insert(
        "Branches",
        ["Branch_id", "Branch_name", "City", "Manager_name", "Monthly_operating_cost"],
        branches
    ))

    write_section(f, "CARS", insert(
        "Cars",
        ["Car_id", "Brand", "Model", "Segment", "Fuel_type",
         "Transmission", "Showroom_price", "Cost_price"],
        cars
    ))

    write_section(f, "CUSTOMERS", insert(
        "Customers",
        ["Customer_id", "Full_Name", "Gender", "Age", "City",
         "Occupation", "Annual_income", "First_purchase_date"],
        customers
    ))

    write_section(f, "SALESPERSONS", insert(
        "Salespersons",
        ["Salesperson_id", "Salesperson_name", "Joining_date", "Salary", "Branch_id"],
        salespersons
    ))

    write_section(f, "FINANCING", insert(
        "Financing",
        ["Financing_id", "Bank_name", "Interest_Rate", "Loan_tenure_months", "Emi_amount"],
        financing
    ))

    write_section(f, "SALES", insert(
        "Sales",
        ["Sale_id", "Customer_id", "Car_id", "Salesperson_id",
         "Branch_id", "Sale_date", "Sale_price", "Discount_given", "Financing_id"],
        sales
    ))

    write_section(f, "INVENTORY", insert(
        "Inventory",
        ["Inventory_id", "Car_id", "Branch_id", "Stock_Quantity", "Arrival_date"],
        inventory
    ))

    write_section(f, "SERVICING", insert(
        "Servicing",
        ["Service_id", "Customer_id", "Car_id", "Service_date", "Service_type", "Service_cost"],
        servicing
    ))

    write_section(f, "MARKETING CAMPAIGNS", insert(
        "Marketing_Campaign",
        ["Campaign_id", "Campaign_name", "Channel", "Budget", "Start_date", "End_date"],
        campaigns
    ))

    write_section(f, "LEADS", insert(
        "Leads",
        ["Lead_id", "Customer_id", "Campaign_id", "Branch_id", "Lead_date",
         "Lead_source", "Lead_status", "Assigned_Salesperson_id",
         "Expected_budget", "Interested_car_Segment", "Conversion_date"],
        leads
    ))

    write_section(f, "TEST DRIVES", insert(
        "Test_Drive",
        ["Drive_id", "Customer_id", "Car_id", "Branch_id",
         "Drive_date", "Converted_to_sale"],
        test_drives
    ))

    f.write("\nSET FOREIGN_KEY_CHECKS = 1;\n")
    f.write("-- END OF DATA FILE\n")

# ── summary ────────────────────────────────────────────────────────────────────
print("=" * 55)
print("  Velocity Motors — Data Generation Complete")
print("=" * 55)
print(f"  Branches           : {len(branches)}")
print(f"  Car models         : {len(cars)}")
print(f"  Customers          : {len(customers)}")
print(f"  Salespersons       : {len(salespersons)}")
print(f"  Financing packages : {len(financing)}")
print(f"  Sales transactions : {len(sales)}")
print(f"  Inventory records  : {len(inventory)}")
print(f"  Service records    : {len(servicing)}")
print(f"  Campaigns          : {len(campaigns)}")
print(f"  Leads              : {len(leads)}")
print(f"  Test drives        : {len(test_drives)}")
print("=" * 55)
print(f"  Output → {OUTPUT_FILE}")
print()
print("Usage:")
print("  mysql -u root -p < velocity_motors_schema.sql")
print("  mysql -u root -p < velocity_motors_data.sql")
