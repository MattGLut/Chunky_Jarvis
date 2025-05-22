DFP_SCHEMA = """
Tables:

dealers (
    id INT, # The unique identifier for the dealer
    lotname VARCHAR, # The name of the dealer's lot
    active INT, # The active status of the dealer
    created_at DATETIME # The date the dealer was created
)

units (
    id INT, # The unique identifier for the unit
    dealer_id INT, # The dealer that the unit belongs to
    floor_on DATETIME, # The date the unit was most recently floored
    first_floored_on DATETIME, # The date the unit was first floored
    reverse_on DATETIME, # The date the unit was reversed
    repo_on DATETIME, # The date the unit was reposessed
    sold_on DATETIME, # The date the unit was sold
    payoff_on DATETIME, # The date the unit was paid off
    repo INT # The repo status of the unit
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

  units.repo:
    1: 'Repo'
    2: 'Not Repo'
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

Q: How many dealers are in dfp?
A: SELECT COUNT(*) FROM dealers;
"""
