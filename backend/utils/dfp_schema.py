# backend/utils/dfp_schema.py

DFP_SCHEMA = """
Tables:

dealers (
    id INT,
    lotname VARCHAR,
    active INT,
    created_at DATETIME
)

units (
    id INT,
    dealer_id INT,
    floored_on DATETIME,
    first_floored_on DATETIME,
    reverse_on DATETIME,
    repo_on DATETIME,
    sold_on DATETIME,
    payoff_on DATETIME
)
"""

DFP_ENUMS = """
Enums:

  dealers.active: 
    1: 'Active'
    2: 'Inactive'
    3: 'Hidden'
    4: 'Suspended'
    5: 'Collection'
    6: 'Modified Contract'
    999: 'Application'
    2000: 'Prospect'
    2002: 'Hidden Prospect'
"""

DFP_RELATIONSHIPS = """
Relationships:

dealers.id = units.dealer_id
"""

DFP_FEWSHOT_EXAMPLES = """
Q: How many active dealers are there?
A: SELECT COUNT(*) FROM dealers WHERE active = 1;

Q: Show the 10 most recent repo'd units.
A: SELECT * FROM units WHERE repo_on IS NOT NULL ORDER BY repo_on DESC LIMIT 10;

Q: How many units are floored?
A: SELECT COUNT(*) FROM units WHERE payoff_on IS NULL AND reverse_on IS NULL AND repo = 2;

Q: How many units are sold, but not yet paid off?
A: SELECT COUNT(*) FROM units WHERE sold_on IS NOT NULL AND payoff_on IS NULL;
"""
