# -*- coding: utf-8 -*-
"""
Created on Tue Nov 24 13:02:17 2020

@author: conno
"""
import re 
import pandas as pd
import numpy as np
from datetime import datetime

def find_first_half_index(tables):
    for index,table in enumerate(tables):
        try:
            caption = table.caption.get_text()
        except:
            caption = ''
        if 'First Half' in caption:
            return index
        else:
            pass
    return 'No First Half table found'
        

def find_date(soup):
    txt = [t.text for t in soup.findAll('dd')]
    for tag in txt:
        results = re.findall(r'(\d+/\d+/\d+)',tag)
        if len(results)!=0:
            return results[0]
    return 'No date found'


def get_starters(tables):
    if 'Montana' in tables[1].caption.text and 'Montana State' not in tables[1].caption.text and 'Montana Tech' not in tables[1].caption.text:
        idx=1
    else:
        idx=4
        
    starters_df = pd.read_html(tables[idx].prettify())[0]
    starters = list(starters_df[starters_df['GS']=='*']['Player'])
    #remove numbers from starters, strip whitespace, and capitalize each. We are trying to match play-by-play names
    starters = ["".join(filter(lambda x: not x.isdigit(), name)).strip().upper() for name in starters]
    starters = [name.split()[1]+','+name.split()[0] for name in starters]
    return starters



def players_on_court(df, starters, name_col='UM_event_player',event_col='UM_event'):
    all_players = set(df[name_col]) #get all players from the game, remove duplicates, team, nan
    try:
        all_players.remove('TEAM')
    except:
        pass
    try:
        all_players.remove(np.nan)
    except:
        pass
    
    all_players = [name.strip() for name in all_players] #just in case
    df[name_col] = df[name_col].str.strip()
    df[event_col] = df[event_col].str.strip()
    
    for name in all_players: #Initialize player columns as all zeros
        df[name]=0
        
    for starter in starters: #Get our starters initialized as 1's
        df.loc[0,starter]=1
    
    for player in all_players:
        for index,row in df.iterrows():
            if index !=0:
                if (row[name_col] == player) and (row[event_col] == 'SUB IN'):
                    df.loc[index,player]=1

                elif (row[name_col] == player) and (row[event_col] == 'SUB OUT'):
                    df.loc[index,player]=0

                else:
                    df.loc[index,player]=df.loc[index-1,player]
    return df,all_players



def minutes_on_floor(df,player_column_names):
        
        time_series = pd.to_datetime(df.loc[:,'Time'],format='%M:%S') #Convert Time to datetime objects for subtraction
        
        for name in player_column_names: #Initialize player mins columns to zeros
            new_col = name+'_mins_since_rest'
            df[new_col]=0
        
        #First row
        for player in player_column_names:
            start = datetime(year=1900, month=1, day=1, hour=0, minute=20)
            
            if df.loc[0,player]==1:
                diff = (start-time_series[0]).seconds #get the difference in seconds
                mins_diff = diff/60
                df.loc[0,player+'_mins_since_rest'] = mins_diff
                
        #Rest of rows       
        for player in player_column_names:
            time_tracker=[df.loc[0,player+'_mins_since_rest']]
            for idx,row in df.iloc[1:,].iterrows():

                if row[player]==1:

                    diff = (time_series[idx-1]-time_series[idx]).seconds #get the difference in seconds
                    mins_diff = diff/60
                    df.loc[idx,player+'_mins_since_rest'] = df.loc[idx-1,player+'_mins_since_rest'] + mins_diff
                    
                else:
                    df.loc[idx,player+'_mins_since_rest']=0
                    
        
        return df
    
    
def build_game(tables,soup,second_half_starters, build_OT=False):

    
    all_periods=[] # all periods will be concatenated together at the end, store here
    date = find_date(soup) #Get date of game
    
    """FIRST HALF"""
    first_half_idx = find_first_half_index(tables)
    
    
    #read in first half play by play
    df1 = pd.read_html(tables[first_half_idx].prettify())
    df1=df1[0]
    
    #Home/Away

    UM_index=df1.columns.get_loc('UM')
    UM_home_away = None
    opp_abbr = None

    if UM_index==1:  #Away team is always located on left side, in column index == 1
        UM_home_away = 'Away'
    else:
        UM_home_away = 'Home'
        
        
    #opponent abbreviation
    if UM_index==1:
        opp_abbr = df1.columns[5]
    else:
        opp_abbr = df1.columns[1]

    df1['Opponent_abbr']=opp_abbr
    df1 = df1.rename(columns={opp_abbr:'Opponent'})
    
    #Time
    df1 = df1.rename(columns={'Time Remaining':'Time'})
    df1.Time.replace('--',None,inplace=True) #This also forward fills the time
    df1['Minutes'] = df1.Time.str.split(':').str[0]
    df1['Seconds'] = df1.Time.str.split(':').str[1]
    
    #Events
    df1['UM_fastbreak'] = df1.UM.str.contains('fastbreak').replace(np.nan,False)
    df1['UM_in_the_paint'] = df1.UM.str.contains('in the paint').replace(np.nan,False)
    df1['Opponent_fastbreak'] = df1.Opponent.str.contains('fastbreak').replace(np.nan,False)
    df1['Opponent_in_the_paint'] = df1.Opponent.str.contains('in the paint').replace(np.nan,False)
    
    df1.UM=df1.UM.str.replace(r"\(.*\)","")
    df1.Opponent = df1.Opponent.str.replace(r"\(.*\)","")
    
    df1['UM_event'] = df1.UM.str.split('by').str[0]
    df1['UM_event_player'] = df1.UM.str.split('by').str[1]
    df1['UM_event_player'] = df1.UM_event_player.str.strip()
    df1['Opponent_event'] = df1.Opponent.str.split('by').str[0]
    df1['Opponent_event_player'] = df1.Opponent.str.split('by').str[1]
    df1['Opponent_event_player'] = df1.Opponent_event_player.str.strip()
    
    
    #Scores

    if UM_home_away == 'Away':
        df1 = df1.rename(columns={'Away Team Score':'UM_score','Home Team Score':'Opponent_score'})
    else:
        df1 = df1.rename(columns={'Away Team Score':'Opponent_score','Home Team Score':'UM_score'})
        
    #Half
    df1['Half']=1
    
    
    #first half starters
    first_half_starters = get_starters(tables)
    
    #Subs
    df1,all_players = players_on_court(df1,first_half_starters)
    
    #Time since last rest
    df1 = minutes_on_floor(df1,all_players)
    
    all_periods.append(df1)
    
    
        
    """SECOND HALF"""  
    
    second_half_idx=first_half_idx+1
    
    
    
    #read in second half play by play
    df2 = pd.read_html(tables[second_half_idx].prettify())
    df2=df2[0]
    
    #opponent abbr
    df2['Opponent_abbr']=opp_abbr
    df2 = df2.rename(columns={opp_abbr:'Opponent'})
    

    #Time
    df2 = df2.rename(columns={'Time Remaining':'Time'})
    df2.Time.replace('--',None,inplace=True) #This also forward fills the time
    df2['Minutes'] = df2.Time.str.split(':').str[0]
    df2['Seconds'] = df2.Time.str.split(':').str[1]
    
    #Events
    df2['UM_fastbreak'] = df2.UM.str.contains('fastbreak').replace(np.nan,False)
    df2['UM_in_the_paint'] = df2.UM.str.contains('in the paint').replace(np.nan,False)
    df2['Opponent_fastbreak'] = df2.Opponent.str.contains('fastbreak').replace(np.nan,False)
    df2['Opponent_in_the_paint'] = df2.Opponent.str.contains('in the paint').replace(np.nan,False)
    
    df2.UM=df2.UM.str.replace(r"\(.*\)","")
    df2.Opponent = df2.Opponent.str.replace(r"\(.*\)","")
    
    df2['UM_event'] = df2.UM.str.split('by').str[0]
    df2['UM_event_player'] = df2.UM.str.split('by').str[1]
    df2['UM_event_player'] = df2.UM_event_player.str.strip()
    df2['Opponent_event'] = df2.Opponent.str.split('by').str[0]
    df2['Opponent_event_player'] = df2.Opponent.str.split('by').str[1]
    df2['Opponent_event_player'] = df2.Opponent_event_player.str.strip()
    
    #Scores

    if UM_home_away == 'Away':
        df2 = df2.rename(columns={'Away Team Score':'UM_score','Home Team Score':'Opponent_score'})
    else:
        df2 = df2.rename(columns={'Away Team Score':'Opponent_score','Home Team Score':'UM_score'})
    
    #Half
    df2['Half']=2
    
    #Second Half Starters
    second_starters = second_half_starters[second_half_starters.Date ==date]['Starters'].values[0]
    
    #Substitutions
    df2,all_players=players_on_court(df2,second_starters)
    
    #Time since last rest
    df2 = minutes_on_floor(df2,all_players)
    
    all_periods.append(df2)
    
    
    """OT FUNCTION"""
    def create_OT(table,ot_number=1,opp_abbr=opp_abbr,UM_home_away=UM_home_away):
        #read in OT play by play
        df = pd.read_html(table.prettify())
        df=df[0]
        
        #opponent abbr
        df['Opponent_abbr']=opp_abbr
        df = df.rename(columns={opp_abbr:'Opponent'})

        #Time
        df = df.rename(columns={'Time Remaining':'Time'})
        df.Time.replace('--',None,inplace=True) #This also forward fills the time
        df['Minutes'] = df.Time.str.split(':').str[0]
        df['Seconds'] = df.Time.str.split(':').str[1]

        #Events
        df['UM_fastbreak'] = df.UM.str.contains('fastbreak').replace(np.nan,False)
        df['UM_in_the_paint'] = df.UM.str.contains('in the paint').replace(np.nan,False)
        df['Opponent_fastbreak'] = df.Opponent.str.contains('fastbreak').replace(np.nan,False)
        df['Opponent_in_the_paint'] = df.Opponent.str.contains('in the paint').replace(np.nan,False)

        df.UM=df.UM.str.replace(r"\(.*\)","")
        df.Opponent = df.Opponent.str.replace(r"\(.*\)","")
        df.UM=df.UM.str.strip()
    
        df['UM_event'] = df.UM.str.split('by').str[0]
        df['UM_event_player'] = df.UM.str.split('by').str[1]
        df.UM_event_player = df.UM_event_player.str.split('(').str[0]
        df['Opponent_event'] = df.Opponent.str.split('by').str[0]
        df['Opponent_event_player'] = df.Opponent.str.split('by').str[1]

        #Scores

        if UM_home_away == 'Away':
            df = df.rename(columns={'Away Team Score':'UM_score','Home Team Score':'Opponent_score'})
        else:
            df = df.rename(columns={'Away Team Score':'Opponent_score','Home Team Score':'UM_score'})

        #Half
        df['Half']=ot_number+2
        
        return df
        
    """ANY OVERTIMES"""
    if build_OT==True:
        ot=True
        n_ots=0
        ot_index=second_half_idx+1
        while ot==True:
            ot_caption = tables[ot_index].caption.get_text()
            
            try:
                ot_caption = tables[ot_index].caption.get_text()
            except:
                ot_caption = ''
    
            if 'OT' in ot_caption:
                n_ots+=1
                ot_df = create_OT(tables[ot_index],ot_number=n_ots)
                
                all_periods.append(ot_df)
            else:
                ot=False
                
            ot_index += 1
    
    game = pd.concat(all_periods,axis=0,ignore_index=True)
    
    #Fix event columns, strip whitespace
    game.UM_event = game.UM_event.str.strip()
    game.UM_event_player = game.UM_event_player.str.strip()
    game.Opponent_event = game.Opponent_event.str.strip()
    game.Opponent_event_player = game.Opponent_event_player.str.strip()
    
    
    #Fix scoring columns, forward fill and remove parenthesis
    game.UM_score=game.UM_score.ffill() 
    game.Opponent_score=game.Opponent_score.ffill()   
    game.UM_score = game.UM_score.astype('str').str.replace(r"\(.*\)","")
    game.Opponent_score = game.Opponent_score.astype('str').str.replace(r"\(.*\)","")
    game.UM_score = game.UM_score.replace('nan',0).astype(float).astype(int)
    game.Opponent_score = game.Opponent_score.replace('nan',0).astype(float).astype(int)
    game['Home_away']=UM_home_away
    
    #Get date column
    game['Date'] = date
    
    game.drop(['Play Team Indicator','Team Indicator','Game Score','Play'],axis=1,inplace=True)
    game.Time.apply(lambda x: datetime.strptime(x, '%M:%S').time())
    
    #Fill missing on court values
    all_players = list(game.UM_event_player.unique())
    try:
        all_players.remove('TEAM')
    except:
        pass
    try:
        all_players.remove(np.nan)
    except:
        pass
    
    all_players = [name.strip() for name in all_players]
    game[all_players]=game[all_players].fillna(0)
    
    

    return game