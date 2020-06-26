import re
import psycopg2
import urllib.request as req

from bs4 import BeautifulSoup as bs

# Verbindung zur DB herstellen
conn = psycopg2.connect("dbname=frorum_db user=frorum password=sicheresPasswort")
cur = conn.cursor()
cur.execute("SELECT version()")
print("Verbindung zu %s hergestellt" % cur.fetchone())

# Verbindung zum Server herstellen und HTML-Datei laden
url = "https://www.frobese.de/frorum/post/"
response = req.urlopen(url)
page = response.read()
soup = bs(page, "lxml")

# Navigation durchs DOM
content = soup.body.find(id="content")
elements = content.find_all(class_=re.compile("card"))

posts = elements[2:]
for tag in posts:
    title = tag.h5
    link = title.parent.get("href")
    
    # Datensätze in die Datenbank schreiben
    cur.execute("INSERT INTO index (title, link) VALUES (%s, %s)", (title.string, link))
    print("==> %s eingefügt" % title.string)
    
# Verbindung zur Datenbank schließen
conn.commit()
conn.close()
