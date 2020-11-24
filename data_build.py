# -*- coding: utf-8 -*-
"""
Created on Tue Nov 24 12:55:51 2020

@author: conno
"""

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import os
import pandas as pd
import numpy as np
from datetime import datetime
from scraper_functions import *

#Find all links on the page for 2019-20 season, store these
url=r'https://gogriz.com/sports/mens-basketball/schedule/2019-20'
req = Request(url)
html_page = urlopen(req)

soup = BeautifulSoup(html_page, "lxml")

links = []
for link in soup.findAll('a'):
    links.append(link.get('href'))

links=set(links)


#limit our links just to those that are boxscores
boxscore_links=[]
for link in links:
    try:
        if 'boxscore' in link:
            link = r'https://gogriz.com'+link
            boxscore_links.append(link)
    except:
        pass
    

#This name converter is just to convert our file of second half starters into the same names in play-by-play
name_converter ={'Anderson': 'ANDERSON,MACK',
 'Manuel': 'MANUEL,KENDAL',
 'Samuelson': 'SAMUELSON,JARED',
 'Vazquez': 'VAZQUEZ,JOSH',
 'Pridgett': 'PRIDGETT,SAYEED',
 'Owens': 'OWENS,KYLE',
 'Falls': 'FALLS,TIMMY',
 'Carter-Hollinger':'CARTER-HOLLI,DERRICK',
 'Egun':'EGUN,EDDY'}

#Load in our file of second half starters, we need this to keep track of who is on floor
second_half_starters = pd.read_csv('second_half_starters_19_20.csv')
second_half_starters.Starters = second_half_starters.Starters.str.split()

#Convert names to our current format
converted_names=[]
for game in second_half_starters['Starters']:
    converted_names_temp =[]
    for name in game:
        converted_names_temp.append(name_converter[name])
    converted_names.append(converted_names_temp)
    
second_half_starters.Starters = converted_names

all_games=[]
for box in boxscore_links:
    req = Request(box)
    html_page = urlopen(req)
    
    soup = BeautifulSoup(html_page,'lxml')
    tables = soup.findAll('table')
    
    df = build_game(tables,soup,second_half_starters)
    all_games.append(df)
    
data = pd.concat(all_games,axis=0,ignore_index=True)

data.to_csv('testy2.txt', sep='\t',index=False)