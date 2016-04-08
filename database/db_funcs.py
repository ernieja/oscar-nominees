import requests
from bs4 import BeautifulSoup
import simplejson
import sqlite3 as lite
import unicodedata


# remove accents (helpful when searching database later)
def strip_accents(s):
    form = unicodedata.normalize("NFD", s)
    return u"".join([c for c in form if not unicodedata.combining(c)])


# return relevant html section for both pages
def get_soup(url_end, page):
    if page == "af_nominees":
        url = "http://www.filmaffinity.com/en/awards.php?award_id=academy_awards&year=" + str(url_end)
        section = "div.full-content"
    elif page == "af_movie":
        url = "http://www.filmaffinity.com" + url_end
        section = "div#left-column"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    decoded = soup.encode('latin-1').decode('utf-8', errors='ignore')
    return BeautifulSoup(decoded, "html.parser").select(section)


# individually fix a few movie titles that don't match between the two sites
def rename_film(film_dict):
    film_dict['Film'].replace("&", "%26")
    corrections = {"Love": "Amour", "Birdman": "Birdman or (The Unexpected Virtue of Ignorance)", "To Return": "Volver",
                   "Mrs. Henderson Presents": "Mrs Henderson Presents", "Pride and Prejudice": "Pride & Prejudice",
                   "Extremely Loud and Incredibly Close": "Extremely Loud & Incredibly Close"}
    for film in ["Love", "Birdman", "Mrs. Henderson Presents", "Pride and Prejudice", "To Return",
                 "Extremely Loud and Incredibly Close"]:
        if film_dict['Film'] == film:
            return corrections[film]
    return film_dict['Film']


# import json from web API
def get_json(title, year):
    json_url = "http://www.omdbapi.com/?t=%s&y=%04d&r=json"
    data = requests.get(json_url % (str.lower(title.replace(" ", "+").replace("&", "%26")), year)).content
    js = simplejson.loads(data)
    metadata = {"Director": js["Director"], "Rated": js["Rated"], "Genre": js["Genre"],
                "imdbRating": float(js["imdbRating"]), "Metascore": int(js["Metascore"])}
    return metadata


def insert_nominees(film_dict, outcome):
    con = lite.connect("oscars.db")
    c = con.cursor()

    tblstr = '''CREATE TABLE IF NOT EXISTS nominees(
                award_year INTEGER,
                award TEXT,
                nominee TEXT,
                film TEXT,
                result TEXT,
                PRIMARY KEY (award_year, award, nominee, film)
                FOREIGN KEY(film) REFERENCES films(film)
                )'''
    c.execute(tblstr)

    c.execute('INSERT INTO nominees VALUES (?, ?, ?, ?, ?)', (film_dict['Award_Year'], film_dict['Category'],
                                                              film_dict['Nom_Name'], film_dict['Film'], outcome))
    con.commit()
    c.close()
    con.close()


def insert_movies(film_dict):
    normal_film = strip_accents(film_dict['Film'])
    con = lite.connect("oscars.db")
    c = con.cursor()

    tblstr = '''CREATE TABLE IF NOT EXISTS films(
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
                    )'''
    c.execute(tblstr)

    c.execute("SELECT * FROM films WHERE film=? AND year=?", (film_dict['Film'], film_dict['Year']))
    data = c.fetchone()
    if data is None:
        c.execute('INSERT INTO films VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (film_dict["Award_Year"],
                                                                              film_dict["Film"], normal_film,
                                                                              film_dict["Year"], film_dict["Director"],
                                                                              film_dict["Genre"], film_dict["Rated"],
                                                                              film_dict["Writer"],
                                                                              film_dict["Metascore"],
                                                                              film_dict["imdbRating"]))
    con.commit()
    c.close()
    con.close()


# top three billed actors for film
def top_actors(soup):
    actor_list = soup.select('div.cast > a')
    for a in range(len(actor_list)):
        actor_list.insert(0, actor_list.pop().getText().strip())
    return actor_list


def insert_people_db(film, category_index, film_dict):
    for actor in top_actors(film):
        insert_people(actor, film_dict['Film'], "actor")
    if int(category_index) > 1:
        insert_people(film_dict['Nom_Name'], film_dict['Film'], "actor")
    director_list = film_dict['Director'].split(",")
    for director in director_list:
        insert_people(director.strip(), film_dict['Film'], "director")


def insert_people(name, film, role):
    normal_name = strip_accents(name)
    con = lite.connect("oscars.db")
    c = con.cursor()

    tblstr = '''CREATE TABLE IF NOT EXISTS people(
                    name TEXT,
                    normal_name TEXT,
                    film TEXT,
                    role TEXT,
                    PRIMARY KEY(name, film, role),
                    FOREIGN KEY(film) REFERENCES films(film)
                    )'''
    c.execute(tblstr)

    c.execute("SELECT * FROM people WHERE name=? AND film=? AND role=?", (name, film, role))
    data = c.fetchone()
    if data is None:
        c.execute('INSERT INTO people VALUES (?, ?, ?, ?)', (name, normal_name, film, role))
    con.commit()
    c.close()
    con.close()


def get_metadata(award_year, index, category):
    nominees = get_soup(award_year, "af_nominees")[index].select('li')
    winner = 0
    for nom in nominees:
        # parse html
        film_data = {'Film': nom.find('a', 'movie-title-link').getText().strip(), 'Award_Year': award_year}

        # create entry for nominee name and award category
        film_data['Category'] = category
        if int(index) < 1:
            film_data['Nom_Name'] = film_data['Film']
        else:
            film_data['Nom_Name'] = nom.find('div', 'nom-text').getText().strip()

        # screenwriter and release date are retrieved from the film's own web page
        film_url = nom.find('a', 'movie-title-link')['href']
        film_meta = get_soup(film_url, "af_movie")[0]
        new_data = {'Year': int(film_meta.find(itemprop="datePublished").getText()),
                    'Writer': film_meta.find("dt", string='Screenwriter').find_next("dd").getText()}

        # compile rest of metadata from omdb and merge these dictionaries with original film_data dictionary
        film_data['Film'] = rename_film(film_data)
        new_data.update(get_json(film_data['Film'], new_data['Year']))
        film_data.update(new_data)

        # load data in sqlite databases
        insert_movies(film_data)
        if winner == 0:
            insert_nominees(film_data, "Won")
            winner += 1
        else:
            insert_nominees(film_data, "Nominated")
        insert_people_db(nom, index, film_data)
