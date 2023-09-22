import requests as req
from bs4 import BeautifulSoup
import re
import sqlite3

db_connection = sqlite3.connect('database.db')
db_cursor = db_connection.cursor()


def bus_lines():
    lines = []
    hrefs = []
    res = req.get('http://rozklad.com/maps/index.php?IDKlienta=OSTROW_MZK&cmd=linie')
    # print(res.status_code)
    soup = BeautifulSoup(res.text, 'html.parser')
    line = soup.find_all('a', class_='btn btn-outline-primary')
    for i in line:
        lines.append(i.text)
        hrefs.append(i.get('href'))
        db_cursor.execute("INSERT INTO bus_lines VALUES(:id, :line_name, :line_link)",
                          {
                              'id': None,
                              'line_name': i.text,
                              'line_link': i.get('href')
                          })
        db_connection.commit()
    # print(hrefs)
    return lines, hrefs


def bus_stops(lines, hrefs):
    pattern = r'\((.*?)\)'
    pattern2 = r"'(.*?)'"
    bus_stations = []
    bus_stations_attr = []
    for h, i in enumerate(hrefs):
        res = req.get('http://rozklad.com/maps/' + i)
        soup = BeautifulSoup(res.text, 'html.parser')
        db_cursor.execute('SELECT id FROM bus_lines WHERE (line_name=?)', (lines[h],))
        bus_line_id = db_cursor.fetchone()[0]
        elements_from = soup.find('div', id='przystanki1').find_all('a',
                                                                    class_='p-1 list-group-item list-group-item-action')
        elements_to = soup.find('div', id='przystanki2').find_all('a',
                                                                  class_='p-1 list-group-item list-group-item-action')
        for j, k in enumerate(elements_from):
            bus_stations.append(k.text)
            attr = re.search(pattern, k.get('onclick')).group(1)
            bus_stations_attr.append(attr)
            db_cursor.execute(
                "INSERT INTO bus_stops VALUES(:id, :bus_stop_name, :bus_stop_index, :direction, :map_link, "
                ":attribute, :bus_line_id)",
                {
                    'id': None,
                    'bus_stop_name': k.text,
                    'bus_stop_index': j,
                    'direction': soup.find('div', id='przystanki1').find_all('h2')[0].text.replace("\n", "").replace(" ", ""),
                    'map_link': 'r7xp.php?IDKlienta=OSTROW_MZK&ID={}&cmd=map'.format(re.findall(pattern2, attr)[0]),
                    'attribute': attr,
                    'bus_line_id': int(bus_line_id)
                })
            db_connection.commit()
        for l, m in enumerate(elements_to):
            bus_stations.append(m.text)
            attr = re.search(pattern, m.get('onclick')).group(1)
            bus_stations_attr.append(attr)
            db_cursor.execute(
                "INSERT INTO bus_stops VALUES(:id, :bus_stop_name, :bus_stop_index, :direction, :map_link, "
                ":attribute, :bus_line_id)",
                {
                    'id': None,
                    'bus_stop_name': m.text,
                    'bus_stop_index': l,
                    'direction': soup.find('div', id='przystanki2').find_all('h2')[0].text.replace("\n", "").replace(" ", ""),
                    'map_link': 'r7xp.php?IDKlienta=OSTROW_MZK&ID={}&cmd=map'.format(re.findall(pattern2, attr)[0]),
                    'attribute': attr,
                    'bus_line_id': int(bus_line_id)
                })
            db_connection.commit()
    # print(bus_stations)
    # print(bus_stations_attr)
    return bus_stations_attr


def bus_hours(bus_stations_attr):
    # working_days = []
    # saturdays = []
    # sundays = []
    # legend = []
    pattern = r"'(.*?)'"
    for a in bus_stations_attr:
        db_cursor.execute('SELECT id,  bus_line_id FROM bus_stops WHERE (attribute=?)', (a,))
        ids = db_cursor.fetchone()
        bus_stop_id = ids[0]
        bus_line_id = ids[1]
        matches = re.findall(pattern, a)
        res = req.get(
            'http://rozklad.com/maps/r7xp.php?IDKlienta={}&cmd=rozID&ID={}&IDLinii={}'.format(matches[2], matches[0],
                                                                                              matches[1]))
        soup = BeautifulSoup(res.text, 'html.parser')

        try:
            working_days_soup = soup.find('div', id="collapse-1")
            working_days_hours = working_days_soup.find_all('li', class_='odjazd-list list-group-item')
            for i in working_days_hours:
                hour = i.text[:2]
                minutes = i.text[2:].replace(" ", "").split(".")
                minutes = list(filter(None, minutes))
                for x in minutes:
                    # working_days.append(hour + ":" + x)
                    db_cursor.execute(
                       "INSERT INTO bus_hours VALUES(:id, :hour, :day, :bus_stop_id, :bus_line_id)",
                       {
                           'id': None,
                           'hour': hour + ":" + x,
                           'day': 'r',
                           'bus_stop_id': int(bus_stop_id),
                           'bus_line_id': int(bus_line_id)
                       })
                    db_connection.commit()
        except AttributeError:
            pass

        try:
            saturdays_soup = soup.find('div', id="collapse-2")
            saturdays_hours = saturdays_soup.find_all('li', class_='odjazd-list list-group-item')
            for j in saturdays_hours:
                hour = j.text[:2]
                minutes = j.text[2:].replace(" ", "").split(".")
                minutes = list(filter(None, minutes))
                for x in minutes:
                    # saturdays.append(hour + ":" + x)
                    db_cursor.execute(
                        "INSERT INTO bus_hours VALUES(:id, :hour, :day, :bus_stop_id, :bus_line_id)",
                        {
                            'id': None,
                            'hour': hour + ":" + x,
                            'day': 's',
                            'bus_stop_id': int(bus_stop_id),
                            'bus_line_id': int(bus_line_id)
                        })
                    db_connection.commit()
        except AttributeError:
            pass

        try:
            sundays_soup = soup.find('div', id="collapse-3")
            sundays_hours = sundays_soup.find_all('li', class_='odjazd-list list-group-item')
            for k in sundays_hours:
                hour = k.text[:2]
                minutes = k.text[2:].replace(" ", "").split(".")
                minutes = list(filter(None, minutes))
                for x in minutes:
                    # sundays.append(hour + ":" + x)
                    db_cursor.execute(
                        "INSERT INTO bus_hours VALUES(:id, :hour, :day, :bus_stop_id, :bus_line_id)",
                        {
                            'id': None,
                            'hour': hour + ":" + x,
                            'day': 'w',
                            'bus_stop_id': int(bus_stop_id),
                            'bus_line_id': int(bus_line_id)
                        })
                    db_connection.commit()
        except AttributeError:
            pass

        try:
            legend_soup = soup.find('div', class_='bg-success p-1 mb-1 text-white bg-opacity-75')
            # legend.append(legend_soup)
            db_cursor.execute(
                "INSERT INTO legends VALUES(:id, :legend, :bus_stop_id, :bus_line_id)",
                {
                    'id': None,
                    'legend': legend_soup.text,
                    'bus_stop_id': int(bus_stop_id),
                    'bus_line_id': int(bus_line_id)
                })
            db_connection.commit()
        except AttributeError:
            pass

