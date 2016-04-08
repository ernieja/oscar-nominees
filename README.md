# Oscar Nominees

A simple interactive app that pulls from databases populated with Academy Award nominees across six categories:
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

    import sqlite3 as lite

####filmaffinity    
`Beatufiul Soup` is used to parse HTML

The library provides, among other things, the ability to search a `BeautifulSoup` object based on tags, attributes, position on the parse tree, etc. This makes it incredibly easy to navigate a document.

```python
import requests
from bs4 import BeautifulSoup

def get_soup(url_end):
    url = "http://www.filmaffinity.com/en/awards.php?award_id=academy_awards&year=" + str(url_end)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.select("div.full-content")

nominee = get_soup(2000)[0].select('li')[1]
film_url = nominee.find('a', 'movie-title-link')['href']
soup = get_soup(film_url, "af_movie")[0]
some_data = {'Year': int(soup.find(itemprop="datePublished").getText()),
             'Writer': soup.find("dt", string='Screenwriter').find_next("dd").getText()}
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
User can search the database using the following criteria:
* Film title
* Release year range
* Person name
* Genres
* Award category

Results are pulled from the database and displayed in `Pandas` dataframes

```python
import pandas as pd

def get_df(sql_stmt, connection):
    df = pd.read_sql(sql_stmt, connection)
    df.columns = map(str.upper, df.columns)
    return df
```


