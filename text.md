# Web Crawling: Datenbeschaffung im Internet

In Zeiten von Big Data und Machine Learning ist es Konsens, dass viele Entscheidungen durch die Verwendung von Daten verbessert oder überhaupt erst möglich werden. Wo aber diese Daten herkommen ist - wenn keine eigenen Datenbestände genutzt werden - nicht ganz so klar.

Etablierte Unternehmen können auf große, wachsende und gut integrierte Datenbestände zugreifen. Darüber hinaus gibt es eine Vielzahl öffentlicher und kommerzieller Datenbanken, auf die nicht nur komfortabel per API zugegriffen werden kann, sondern die auch schon einen Teil der Auswertung übernehmen.

In der Praxis kommt man aber schnell an einen Punkt, an dem Daten die man sich zur Auswertung wünscht, nicht ausreichend oder gar nicht vorhanden sind. Hier kann es sich lohnen auch unstrukturierte Daten wie Bücher, Artikel oder eben Internetseiten in die Betrachtung einzubeziehen. Letztere sind durch HTML Tags und IDs zumindest teilweise strukturiert.

## Begrifflichkeit

Web Crawling wird häufig mit großen Suchmaschinen wie Google in Verbindung gebracht, deren Crawler das Internet indizieren. Ein Crawler startet mit einem bekannten Stamm an Internetseiten und sammelt erst auf diesen bereits bekannten Seiten Links zu weiteren, vorher noch unbekannten, Webseiten. Auf diese Weise erreicht der Crawler jede Webseite, die auf irgendeine Weise in die Link Struktur des Internets eingebunden ist. Dabei muss er so robust programmiert sein, dass auch unbekannte Seiten zuverlässig verarbeitet werden können.

Web Scraping beschäftigt sich mit der Extraktion von Informationen von einer Webseite. Das muss nicht automatisiert passieren - ist es aber meistens. Jeder Crawler muss Informationen von einer Webseite extrahieren und verarbeiten, ist also auch ein Scraper. Jedes nicht triviales Scraping Unterfangen navigiert zwischen mehreren URLs und hat so auch eine crawling Komponente. Im folgenden verwenden wir der Einfachheit halber nur den allgemeineren Begriff "Crawling".

## Beispiel

Nehmen wir als praktisches Beispiel das Frorum. Hier gibt es viele interessante Artikel, aber weder einen Newsletter noch einen RSS-Feed, um auf dem Laufenden zu bleiben. Im Folgenden nehmen wir das selbst in die Hand und nutzen die Gelegenheit, um die grundlegenden Techniken des Web Crawlings beispielhaft gemeinsam durchzugehen. Am Ende steht ein Programm, dass den Inhalt des Frorums systematisch ausließt und in einer Datenbank abspeichert. Mit ein wenig zusätzlicher Logik könnten wir das Programm in einem gewissen Zeitintervall automatisch laufen und uns informieren lassen, sollte es einen neuen Artikel geben. Genau wäre es auch möglich den Inhalt nach gewissen Begriffen und regulären Ausdrücken zu untersuchen. Das ist aber Stoff für einen anderen Beitrag.

## Setup

Zuerst brauchen wir eine Datenbank, um die Ergebnisse dauerhaft zu speichern. Für kleine Projekte oder zum Testen und Entwickeln kann man SQLite gut einsetzen. SQLite ist als dateibasierte Datenbank schnell einsatzbereit ist, aber aus dem gleichen Grund weniger skalierbar und nicht einfach in einem Netzwerk einzusetzen. PostgreSQL ist ein Datenbankserver mit integrierter Nutzerverwaltung und bietet außerdem eine fast perfekte Abdeckung des SQL-Standards. Wir werden hier eine Postgres Instanz verwenden, grundsätzlich gilt aber jede SQL Datenbank, die man gut kennt, ist eine gute Wahl. 

Für die Datenverarbeitung nutzen wir das im Bereich Data Science sehr populäre Python3. Neben einer umfassenden Standardbibliothek bietet Python ein ausgereiftes Ökosystem von externen Bibliotheken, dem Paketmanager pip und Bindings zu anderen Programmiersprachen wie C. Hier einige Beispiele:

- Pandas ist eine Bibliothek mit Datenstrukturen und Funktionen zur Verarbeitung von multi-dimensionalen Matrizen. Die wichtigste Datenstruktur ist dabei der DataFrame.

- TensorFlow ist eine hardwarenahe Plattform für maschinelles Lernen. Der Zugriff auf die C++ Kernfunktionalität von TensorFlow erfolgt entweder direkt per Python Code oder über weiter abstrahierende Frameworks wie Keras.

- Jupyter Notebooks bietet die Möglichkeit Python Code in Echtzeit auszuführen, anzupassen und ihn mit Markdown Text und Visualisierungen in einer Datei zusammenzufassen und zu teilen. Das ist insbesondere in der Lern- und Entwicklungsphase praktisch.

- Darüber hinaus gibt es eine Vielzahl an Anwendunsfällen für Python Programme. Von der Webentwicklung (Flask, Django) bis zur Entwicklung von GUI Apps (tkinter).



### Datenbank
Nach der Installtion von PostgreSQL können wir eine Datenbank "crawler-db" aufsetzen und einen Datenbanknutzer "crawler" erstellen:

```bash
createuser frorum
createdb frorum_db
```

Anschließend öffnen wir das Postgres Kommandozeilen Interface mit `psql` und konfigurieren die Datenbank mit Standard SQL:

```SQL
ALTER USER frorum WITH ENCRYPTED PASSWORD 'sicheresPasswort';
GRANT ALL PRIVILEGES ON DATABASE frorum_db TO frorum;
ALTER DATABASE frorum_db OWNER TO frorum;
```

Mit `\l` vergewissern wir uns das alles geklappt hat und schließen psql mit `\q`. Die Datenbank ist jetzt bereit und kann von uns bzw. unserem Code befüllt werden.

### Python
Um eine einheitliche Entwicklungsumgebung auch auf mehreren Maschinen zu gewährleisten, nutzen wir einen Umgebungsmanager. Wir installieren pipenv und erstellen eine neue virtuelle Umgebung:

```bash
pip3 install pipenv
pipenv --python 3
```

pipenv erstellt ein Pipfile, in dem alle benötigten Pakete aufgelistet sind. Momentan steht da nur Python 3.8 drin. Um uns das Parsen von HTML-Dokumenten zu erleichtern, fügen wir noch BeautifulSoup4 und lxml hinzu. Um die Postgres-Datenbank per Python Code zu steuern, brauchen wir noch das passende Interface psycopg2. Anschließend können wir die virtuelle Umgebung starten:

```bash
pipenv install bs4 lxml psycopg2
pipenv shell
```

## Erforschung
Um einen ersten Eindruck der Struktur der Ziel-Webseite zu bekommen, bietet sich das Inspektor-Tool eines Browsers an. Hier sehen wir, dass die [Beitragsliste](https://www.frobese.de/frorum/post/) als Flexbox Layout angelegt ist und jedes Element dieser Tabelle ein div-Tag mit `class="mdl-card ..."` ist.
![inspector](./images/inspector.png)

Zur weiteren Erforschung installieren wir Jupyter und starten ein neues Notebook:
```bash
pipenv install jupyterlab
jupyter notebook
``` 

Wenn wir den Sourcecode der Webseite speichern und direkt mit der HTML-Datei experimentieren, müssen wir nicht jedes mal eine Anfrage an den Server stellen. Dann geht es für uns auch schneller. Nach einem interaktiven Spaziergang (link zum Notebook oder einbetten) durchs DOM verstehen wir die Struktur des HTML-Dokuments so gut, dass wir den relevanten Code in ein Python Skript übernehmen können. Das fertige Skript - nennen wir es index_frorum.py - sieht dann so aus:

```python
import re

from bs4 import BeautifulSoup as bs

with open("./source/frorum.html") as page:
    soup = bs(page, "lxml")

content = soup.body.find(id="content")
elements = content.find_all(class_=re.compile("card"))

posts = elements[2:]
for tag in posts:
    title = tag.h5
    link = title.parent.get("href")
    print(title.string, link)
```

Jetzt bekommen wir alle Informationen, die wir brauchen. Statt diese aber einfach auf dem Terminal auszugeben, sollten wir alles in einer Datenbank speichern. So können wir auch später noch mit diesen Daten arbeiten. Dazu melden wir uns zuerst am Datenbank-Server:
```bash
psql -U frorum -d frorum_db
```
Dann erstellen wir eine Tabelle mit dem entsprechenden Schema:
```sql
CREATE TABLE index (
    id SERIAL PRIMARY KEY,
    title TEXT,
    link TEXT
);
```
Wir kontrollieren mit `\d index` , ob alles geklappt hat. Das sieht gut aus! Jetzt können wir per Python eine Verbindung zur Datenbank aufbauen:
```python
import psycopg2

conn = psycopg2.connect("dbname=frorum_db user=frorum password=sicheresPasswort")
cur = conn.cursor()
```
Jetzt ersetzen wir noch das abschließende `print()` und schreiben stattdessen in die Datenbank:
```python
cur.execute("INSERT INTO index (title, link) VALUES (%s, %s)", (title.string, link))
```
Damit haben wir alle Information, die für uns wichtig sind geordnet in der Datenbank hinterlegt. Wir haben also aus einer HTML-Datei einen strukturierten Datensatz erstellt, mit dem wir leicht weiter arbeiten können. Als letzten Schritt fordern wir die HTML-Datei mit jedem Programmdurchlauf neu vom Server an. Das finale Skript sieht dann so aus:
```python
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
```
Dieses Beispiel ist mit Absicht sehr einfach gewählt. Bei einem "echten" Datensammel-Job braucht man robusteren Code, der auch mit Exceptions und mit Clientseitigen Javascript umgehen können muss. Nur einige der möglichen Schwierigkeiten sind asynchron ladender Inhalt und Cookie-Banner, die dort auftauchen wo man eigentlich die Daten erwartet. Ein leistungsfähiger Crawler sollte parallel arbeiten können und trotztdem immer wissen welche Bereiche schon bearbeitet wurden und welche nicht. Und selbst der beste Crawler muss betreut werden. Das Internet ist schnelllebig und vollständig automatisiert geht es in den wenigsten Fällen.

## Ethisches Web Crawling
Wie bei fast allem gibt es auch hier Regeln, an die man sich halten sollte. Nicht nur als kategorischer Imperativ sondern auch um nicht unwissentlich eine DoS-Attacke zu starten. Jede Internetseite hat eine robots.txt Datei, die angibt, ob und welche Bereiche eine programmatische Verarbeitung erlauben. Diesen codifizierten Willen der Seitenbetreiber sollte man befolgen. Auch ist es ratsam auf die Leistungsfähigkeit des Webservers zu reagieren und die Anzahl der eigenen Anfragen abhängig von der Reaktionszeit des Servers zu machen. So würde der Crawler automatisch bei geringer Last (z.B. nachts) mehr Anfragen stellen und bei langer Reaktionszeit (länger als 100ms) die eigene Aktivität zurückstellen. 
Unabhängig davon kann es sinnvoll sein vor ab mit dem Seitenbetreiber zu sprechen. Möglicherweise gibt es einfachere und für beide Seiten ressourcenschonendere Wege, an die benötigten Daten zu gelangen.

## Datenquellen
Oft muss man sich aber auch gar nicht mit der Datenbeschaffung beschäftigen. Viele interessante Daten wurden schon von jemand anderem gesammelt und dürfen frei verwendet werden. Hier sind die wichtigsten Quellen für diese Datensätze:
- [Common Crawl](https://commoncrawl.org/)
- [AWS OpenData](https://registry.opendata.aws/)
- [awesomedata](https://github.com/awesomedata/awesome-public-datasets)

## Referenzen
- [Datenbank auswählen](https://www.digitalocean.com/community/tutorials/sqlite-vs-mysql-vs-postgresql-a-comparison-of-relational-database-management-systems)
- [Diskussion zum Unterschied zwischen Scraping und Crawling](https://stackoverflow.com/questions/4327392/what-is-the-difference-between-web-crawling-and-web-scraping)

