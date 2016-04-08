from db_funcs import get_metadata
from datetime import datetime


# award categories to take into account
categories = ["Best Picture", "Best Director", "Best Actor", "Best Actress", "Best Supporting Actor",
              "Best Supporting Actress"]

# populate sqlite database with data for films released between 2000 and the current year
for year in range(2001, datetime.now().year+1):
    for idx, val in enumerate(categories):
        get_metadata(year, idx, val)
