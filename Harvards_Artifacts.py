import sqlite3
import requests
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu

import mysql.connector
from mysql.connector import Error
conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Guvi@123456",
        database="Harvards_Articraft"
    )

cursor = conn.cursor()

api_key = "c960b09c-f1be-425a-af36-40a931dd1fd9"
url = "https://api.harvardartmuseums.org/object"

# ------------------------------------------------ Create Tables ------------------------------------------------ #
def create_tables():
    cursor.execute("""CREATE TABLE IF NOT EXISTS artifact_metadata (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    culture TEXT,
                    period TEXT,
                    century TEXT,
                    medium TEXT,
                    dimensions VARCHAR(75),
                    department TEXT,
                    description TEXT,
                    classification TEXT,
                    accessionyear INTEGER,
                    accessionmethod TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS artifact_media (
                    object_id INTEGER,
                    imagecount INT,
                    mediacount INT,
                    colorcount INT,
                    rankorder INT,
                    datebegin INT,
                    dateend INT,
                    FOREIGN KEY(objectid) REFERENCES artifact_metadata(id)
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS artifact_color (
                  objectid INTEGER,
                  color TEXT,
                  spectrum TEXT,
                  hue TEXT,
                  percent REAL,
                  css3 TEXT,
                  FOREIGN KEY(objectid) REFERENCES artifact_metadata(id)
    )""")

create_tables()

# ------------------------------------------------ Data Collection ------------------------------------------------ #
def classes(api_key, class_name):
    all_records = []
    page_size = 100

    for page in range(1, 26):  # 25 pages
        response = requests.get(
            url,
            params={
                "apikey": api_key,
                "size": page_size,
                "hasimage": 1,
                "page": page,
                "classification": class_name
            }
        )
        data = response.json()
        records = data.get('records', [])
        all_records.extend(records)

    return all_records

# ------------------------------------------------ Extract Metadata, Media, Colors ------------------------------------------------ #
def artifacts_details(records):
    metadata = []
    media = []
    colors = []

    for i in records:
        # Metadata
        metadata.append({
            'id': i.get('id'),
            'title': i.get('title'),
            'culture': i.get('culture'),
            'period': i.get('period'),
            'division': i.get('division'),
            'medium': i.get('medium'),
            'dimensions': i.get('dimensions'),
            'description': i.get('description'),
            'dept': i.get('department'),
            'classification': i.get('classification'),
            'accessionyear': i.get('accessionyear'),
            'accessionmethod': i.get('accessionmethod')
        })

        # Media
        media.append({
            'objectid': i.get('objectid'),
            'imagecount': i.get('imagecount'),
            'mediacount': i.get('mediacount'),
            'colorcount': i.get('colorcount'),
            'rank': i.get('rank'),
            'datebegin': i.get('datebegin'),
            'dateend': i.get('dateend')
        })

        # Colors
        color_details = i.get('colors')
        if color_details:
            for j in color_details:
                colors.append({
                    'objectid': i.get('objectid'),
                    'color': j.get('color'),
                    'spectrum': j.get('spectrum'),
                    'hue': j.get('hue'),
                    'percent': j.get('percent'),
                    'css3': j.get('css3')
                })

    return metadata, media, colors

# ------------------------------------------------ Insert into DB ------------------------------------------------ #
def insert_values(meta, med, col):
    insert_meta = """INSERT INTO artifact_metadata VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    insert_media = """INSERT INTO artifact_media VALUES(%s,%s,%s,%s,%s,%s,%s)"""
    insert_col = """INSERT INTO artifact_color VALUES(%s,%s,%s,%s,%s,%s)"""

    for i in meta:
        values1 = (
            i['id'], i['title'], i['culture'],
            i['period'], i['division'], i['medium'],
            i['dimensions'], i['dept'], i['description'],
            i['classification'], i['accessionyear'], i['accessionmethod']
        )
        cursor.execute(insert_meta, values1)

    for i in med:
        values2 = (
            i['objectid'], i['imagecount'], i['mediacount'],
            i['colorcount'], i['rank'], i['datebegin'], i['dateend']
        )
        cursor.execute(insert_media, values2)

    for i in col:
        values3 = (
            i['objectid'], i['color'], i['spectrum'],
            i['hue'], i['percent'], i['css3']
        )
        cursor.execute(insert_col, values3)

    conn.commit()

# ------------------------------------------------ Streamlit UI ------------------------------------------------ #
st.set_page_config(layout="wide")
st.markdown("<h1 style='text-align: center; color: black;'>🎨🏛️ Harvard’s Artifacts Collection</h1>", unsafe_allow_html=True)

classification = st.text_input("Enter a classification (e.g., Coins, Vessels, Paintings)")
button = st.button("Collect data")
menu = option_menu(None, ["Select Your Choice", "Migrate to SQL", "SQL Queries"], orientation="horizontal")

if button:
    if classification != '':
        records = classes(api_key, classification)
        meta, med, col = artifacts_details(records)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.header("Metadata")
            st.json(meta)
        with c2:
            st.header("Media")
            st.json(med)
        with c3:
            st.header("Color")
            st.json(col)
    else:
        st.error("Kindly enter a classification")

if menu == 'Migrate to SQL':
    cursor.execute("SELECT DISTINCT(classification) FROM artifact_metadata")
    result = cursor.fetchall()
    classes_list = [i[0] for i in result]

    st.subheader("Insert the collected data")
    if st.button("Insert"):
        if classification not in classes_list:
            records = classes(api_key, classification)
            meta, med, col = artifacts_details(records)
            insert_values(meta, med, col)
            st.success("Data Inserted successfully")

            st.header("Inserted Data:")
            st.divider()

            st.subheader("Artifact Metadata")
            cursor.execute("SELECT * FROM artifact_metadata")
            result1 = cursor.fetchall()
            columns = [i[0] for i in cursor.description]
            df1 = pd.DataFrame(result1, columns=columns)
            st.dataframe(df1)

            st.subheader("Artifact Media")
            cursor.execute("SELECT * FROM artifact_media")
            result2 = cursor.fetchall()
            columns = [i[0] for i in cursor.description]
            df2 = pd.DataFrame(result2, columns=columns)
            st.dataframe(df2)

            st.subheader("Artifact Color")
            cursor.execute("SELECT * FROM artifact_color")
            result3 = cursor.fetchall()
            columns = [i[0] for i in cursor.description]
            df3 = pd.DataFrame(result3, columns=columns)
            st.dataframe(df3)
        else:
            st.error("Classification already exists!! Kindly try a different class!")


elif menu == "SQL Queries":

    option = st.selectbox("Queries", (
        "1.List all artifacts from the 20th century belonging to Japanese culture.",
        "2.What are the unique cultures represented in the artifacts?",
        "3.List all artifacts from the Byzantine Period",
        "4.List artifact titles ordered by accession year in descending order.",
        "5.How many artifacts are there per department?",
        "6.Which artifacts have more than 1 image?",
        "7.What is the average rank of all artifacts?",
        "8.Which artifacts have a higher colorcount than mediacount?",
        "9.List all artifacts created between 1500 and 1600.",
        "10.How many artifacts have no media files?",
        "11.What are all the distinct hues used in the dataset?",
        "12.What are the top 5 most used colors by frequency?",
        "13.What is the average coverage percentage for each hue?",
        "14.List all colors used for a given artifact ID.",
        "15.What is the total number of color entries in the dataset?",
        "16.List artifact titles and hues for all artifacts belonging to the Byzantine culture",
        "17.List each artifact title with its associated hues",
        "18.Get artifact titles, cultures, and media ranks where the period is not null.",
        "19.Find artifact titles ranked in the top 10 that include the color hue Grey.",
        "20.How many artifacts exist per classification, and what is the average media count for each?",
        "21.How many artifacts belong to each century?",
        "22.How many artifacts have no description?",
        "23.List all unique department in the dataset",
        "24.How many artifacts are there in total?",
        "25.List all unique spectrum values used in the dataset"
         ), index=None, placeholder="Select a query")

    if option == "1.List all artifacts from the 20th century belonging to Japanese culture.":
        cursor.execute("""SELECT * 
                          FROM artifact_metadata 
                          WHERE century = '20th century' 
                          AND culture = 'Japanese' """)
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "2.What are the unique cultures represented in the artifacts?":
        cursor.execute("""SELECT DISTINCT(culture) FROM artifact_metadata""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "3.List all artifacts from the Byzantine Period":
        cursor.execute("""SELECT * FROM artifact_metadata
                          WHERE period LIKE '%Byzantine%' """)
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "4.List artifact titles ordered by accession year in descending order.":
        cursor.execute("""SELECT title, accessionyear 
                          FROM artifact_metadata
                          ORDER BY accessionyear DESC""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "5.How many artifacts are there per department?":
        cursor.execute("""SELECT department, COUNT(*) AS artifact_count
                          FROM artifact_metadata
                          GROUP BY department""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)


    elif option == "6.Which artifacts have more than 1 image?":
        cursor.execute("""SELECT objectid, imagecount 
                          FROM artifact_media
                          WHERE imagecount > 1""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "7.What is the average rank of all artifacts?":
        cursor.execute("""SELECT AVG(rankorder) AS avg_rankorder FROM artifact_media""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "8.Which artifacts have a higher colorcount than mediacount?":
        cursor.execute("""SELECT objectid, colorcount, mediacount 
                          FROM artifact_media
                          WHERE colorcount > mediacount""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "9.List all artifacts created between 1500 and 1600.":
        cursor.execute("""SELECT * FROM artifact_media
                          WHERE datebegin >= 1500 AND dateend <= 1600""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "10.How many artifacts have no media files?":
        cursor.execute("""SELECT COUNT(*) AS no_media_files
                          FROM artifact_metadata m
                          LEFT JOIN artifact_media me
                          ON m.id = me.objectid
                          WHERE me.objectid IS NULL""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "11.What are all the distinct hues used in the dataset?":
        cursor.execute("""SELECT DISTINCT(hue) FROM artifact_color""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "12.What are the top 5 most used colors by frequency?":
        cursor.execute("""SELECT color, COUNT(*) AS frequency 
                          FROM artifact_color
                          GROUP BY color
                          ORDER BY frequency DESC
                          LIMIT 5""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "13.What is the average coverage percentage for each hue?":
        cursor.execute("""SELECT hue, AVG(percent) AS avg_coverage
                          FROM artifact_color
                          GROUP BY hue""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "14.List all colors used for a given artifact ID.":
        cursor.execute("""SELECT color, hue, spectrum 
                          FROM artifact_color
                          WHERE objectid = 47201""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "15.What is the total number of color entries in the dataset?":
        cursor.execute("""SELECT COUNT(*) AS total_color_entries FROM artifact_color""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "16.List artifact titles and hues for all artifacts belonging to the Byzantine culture":
        cursor.execute("""SELECT m.title, c.hue
                          FROM artifact_metadata m
                          JOIN artifact_color c
                          ON m.id = c.objectid
                          WHERE m.culture = 'Byzantine'""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "17.List each artifact title with its associated hues":
        cursor.execute("""SELECT m.title, c.hue
                          FROM artifact_metadata m
                          JOIN artifact_color c
                          ON m.id = c.objectid""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "18.Get artifact titles, cultures, and media ranks where the period is not null.":
        cursor.execute("""SELECT m.title, m.culture, me.rankorder
                          FROM artifact_metadata m
                          JOIN artifact_media me
                          ON m.id = me.objectid
                          WHERE m.period IS NOT NULL""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "19.Find artifact titles ranked in the top 10 that include the color hue Grey.":
        cursor.execute("""SELECT m.title, me.rankorder, c.hue
                          FROM artifact_metadata m
                          JOIN artifact_media me
                          ON m.id = me.objectid
                          JOIN artifact_color c
                          ON m.id = c.objectid
                          WHERE c.hue = 'Grey'
                          ORDER BY me.rankorder ASC
                          LIMIT 10""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "20.How many artifacts exist per classification, and what is the average media count for each?":
        cursor.execute("""SELECT m.classification, COUNT(*) AS artifact_count, 
                          AVG(me.mediacount) AS avg_mediacount
                          FROM artifact_metadata m
                          JOIN artifact_media me
                          ON m.id = me.objectid
                          GROUP BY m.classification""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "21.How many artifacts belong to each century?":
        cursor.execute("""SELECT century, COUNT(*) AS artifact_count
                          FROM artifact_metadata
                          GROUP BY century""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "22.How many artifacts have no description?":
        cursor.execute("""SELECT COUNT(*) AS no_description
                          FROM artifact_metadata
                          WHERE description IS NULL """)
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "23.List all unique department in the dataset":
        cursor.execute("""SELECT DISTINCT(department)
                          FROM artifact_metadata""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "24.How many artifacts are there in total?":
        cursor.execute("""SELECT COUNT(*) AS total_artifacts
                          FROM artifact_metadata""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)

    elif option == "25.List all unique spectrum values used in the dataset":
        cursor.execute("""SELECT DISTINCT(spectrum)
                          FROM artifact_color""")
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)





