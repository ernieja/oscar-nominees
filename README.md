# Oscar Nominees

A simple interactive app that returns metadata about Academy Award nominees across six categories:
* Best Picture
* Best Director
* Best Actor
* Best Actress
* Best Supporting Actor
* Best Supporting Actress

### Movie Dataset
---
A scraper written in Python collects information from [filmaffinity] (http://www.filmaffinity.com) and [The OMDB API] (http://www.omdbapi.com/) and organizes the data into three tables:
* Film
* People
* Nominees

Tables are stored in a local database for easy `SQLite` access.
```python
import sqlite3 as lite
con = lite.connect("oscars.db")
c = con.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS films(
                 award_year INTEGER,
                 film TEXT,
                 normal_film TEXT,
                 year INTEGER,
                 director TEXT,
                 genre TEXT,
                 rated TEXT,
                 writer TEXT,
                 metascore INTEGER,
                 imdbRating REAL,
                 PRIMARY KEY(film, year)
                 )''')
    
c.execute("""CREATE TABLE IF NOT EXISTS people(
             name TEXT, 
             normal_name TEXT, 
             film TEXT, 
             role TEXT, 
             PRIMARY KEY(name, film, role),
             FOREIGN KEY(film) REFERENCES films(film)
             )""")
             
c.execute('''CREATE TABLE IF NOT EXISTS nominees(
                award_year INTEGER,
                award TEXT,
                nominee TEXT,
                film TEXT,
                result TEXT,
                PRIMARY KEY (award_year, award, nominee, film)
                FOREIGN KEY(film) REFERENCES films(film)
                )''')             

```

####filmaffinity    
`Beatufiul Soup` is used to parse HTML

The library provides, among other things, the ability to search a `BeautifulSoup` object based on tags, attributes, position on the parse tree, etc. This makes it incredibly easy to navigate a document.

```python
import requests
from bs4 import BeautifulSoup

# returns list of HTML within <div class="full-content"> tags
def get_soup(url_end):
    url = "http://www.filmaffinity.com/en/awards.php?award_id=academy_awards&year=" + str(url_end)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.select("div.full-content")

# each <li> tag in the soup contains data for a 2000 Oscar nominee
for nominee in get_soup(2000)[0].select("li"):
    film_url = nominee.find("a", "movie-title-link")["href"]  # gets URL for the <a class="movie-title-link"> tag
    soup = get_soup(film_url, "af_movie")[0]
    # scrape and store release year and screenwriter in dictionary
    some_data = {'Year': int(soup.find(itemprop="datePublished").getText()),
                 'Writer': soup.find("dt", string="Screenwriter").find_next("dd").getText()}
```

####OMDB API
The responses are formatted in `JSON`
```python  
import simplejson

def get_json(title, year):
    json_url = "http://www.omdbapi.com/?t=%s&y=%04d&r=json"
    data = requests.get(json_url % (str.lower(title.replace(" ", "+").replace("&", "%26")), year)).content
    js = simplejson.loads(data)
    data = {"Director": js["Director"], "Rated": js["Rated"], "Genre": js["Genre"],
                "imdbRating": float(js["imdbRating"]), "Metascore": int(js["Metascore"])}
    return data
```
    



### Python Application
----
User can search the database using any of the following criteria:
* Film title
* Release year range
* Person name
* Genres
* Award category

The `pandas` package supports `SQLite` integration. A search query can be interpreted as SQL and read into a DataFrame for display.

```python
import pandas as pd

def get_df(sql_stmt, connection):
    df = pd.read_sql(sql_stmt, connection)
    df.columns = map(str.upper, df.columns)
    return df
```


