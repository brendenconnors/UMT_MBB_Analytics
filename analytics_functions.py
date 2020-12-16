# -*- coding: utf-8 -*-
"""
Created on Tue Nov 24 15:52:28 2020

@author: conno
"""
import pandas as pd

rest_cols=['ANDERSON,MACK_mins_since_rest',
       'EGUN,EDDY_mins_since_rest', 'FALLS,TIMMY_mins_since_rest',
       'VAZQUEZ,JOSH_mins_since_rest', 'MANUEL,KENDAL_mins_since_rest',
       'SAMUELSON,JARED_mins_since_rest',
       'CARTER-HOLLI,DERRICK_mins_since_rest', 'OWENS,KYLE_mins_since_rest',
       'PRIDGETT,SAYEED_mins_since_rest','SELCUK,YAGIZHAN_mins_since_rest','JONES,PETER_mins_since_rest']

def max_rest_filter(df,low,high,rest_cols):
    """
    Filters our dataframe to only include events where the max 'mins_since_last_rest' is between low and high.

    Parameters
    ----------
    df : Pandas dataframe
        dataframe of all play-by-play events.
    low : int or float
        The minimum value in our binning
    high : TYPE
        the maximum value in our binning
    rest_cols : list
        list containing all rest columns 

    Returns
    -------
    temp_df : pandas dataframe
        filtered pandas dataframe so the max 'mins_since_last_reast' for players falls into our bin (low, high)

    """
    temp_df=df[df[rest_cols].max(axis=1)>low]
    temp_df = temp_df[temp_df[rest_cols].max(axis=1)<=high]
    
    return temp_df

def calc_duration(df):
    """
    Calculate duration of a given sequence, contained in a pandas dataframe. Meant for use after filtering our dataframe

    Parameters
    ----------
    df : pandas dataframe
        DESCRIPTION.

    Returns
    -------
    duration : float
        duration in minutes

    """
    begin_str = df.Time.iloc[0]
    
    if df.iloc[0].name == 0:
        begin_str='20:00'
    end_str = df.Time.iloc[-1]
    
    begin = int(begin_str.split(':')[0]) + int(begin_str.split(':')[1])/60
    end = int(end_str.split(':')[0]) + int(end_str.split(':')[1])/60
    
    duration = begin-end
    
    return duration

def team_turnover_rate(df,group_idxs):
    """
    Calculate turnover rate for a given filtered dataframe. Dataframe should be a sequence or half, not a full game.

    Parameters
    ----------
    df : pandas dataframe
        pandas dataframe that contains play-by-play
    group_idxs : list
        list of lists of indexes to filter dataframe

    Returns
    -------
    turnover_per_min : float
        turnovers per minute played

    """
    
    total_mins=0
    total_turnovers=0
    
    for sequence in group_idxs:
        temp_df = df.loc[sequence,:]
        duration = calc_duration(temp_df)
        n_turnovers = len(temp_df[temp_df.UM_event=='TURNOVER'])
        total_mins+=duration
        total_turnovers+=n_turnovers
        
        
    turnover_per_min = total_turnovers/total_mins
    
    return turnover_per_min
        
        
        
        
def sequence_splits(df,function):
    from more_itertools import consecutive_groups
    
    dates=list(df.Date.unique())
    splits=[]
    for date in dates:
        temp_df = df[df.Date==date]
        for half in [1,2]:
            half_df = temp_df[temp_df.Half == half]
            groups = consecutive_groups(list(half_df.index))
    
            group_idxs = [list(g) for g in groups]
            
            if len(group_idxs)>0:
                splits.extend(group_idxs)
                
    val = function(df,splits)
    return val
    
def player_foul_rate(df, player, window_size=1):
    from more_itertools import consecutive_groups
    import numpy as np
    um_col = 'FOUL by '+player
    rest_col = player+'_mins_since_rest'
    
    
    windows=[]
    duration_list=[]
    foul_list=[]
    for i in range(21-window_size):
        lower_bound = i
        upper_bound = i+window_size
        
        
        temp_df=df[(df[rest_col]>=lower_bound) & (df[rest_col]<upper_bound)]
        
        dates=list(temp_df.Date.unique())
        splits=[]
        for date in dates:
            temp_df2 = temp_df[temp_df.Date==date]
            for half in [1,2]:
                half_df = temp_df2[temp_df2.Half == half]
                groups = consecutive_groups(list(half_df.index))
        
                group_idxs = [list(g) for g in groups]
                
                if len(group_idxs)>0:
                    splits.extend(group_idxs)
                    
        
        total_duration=0
        total_fouls=0
        for split in splits:
            temp_df3 = temp_df.loc[split,:]
            duration = calc_duration(temp_df3)
            n_fouls = len(temp_df3[temp_df3.UM==um_col])
            total_duration+=duration
            total_fouls+=n_fouls
  

        
        windows.append((lower_bound,upper_bound))
        duration_list.append(total_duration)
        foul_list.append(total_fouls)
        
    return foul_list, duration_list, windows

def team_foul_rate(df, window_size=1):
    from more_itertools import consecutive_groups
    import numpy as np

    rest_cols=['ANDERSON,MACK_mins_since_rest',
       'EGUN,EDDY_mins_since_rest', 'FALLS,TIMMY_mins_since_rest',
       'VAZQUEZ,JOSH_mins_since_rest', 'MANUEL,KENDAL_mins_since_rest',
       'SAMUELSON,JARED_mins_since_rest',
       'CARTER-HOLLI,DERRICK_mins_since_rest', 'OWENS,KYLE_mins_since_rest',
       'PRIDGETT,SAYEED_mins_since_rest','SELCUK,YAGIZHAN_mins_since_rest','JONES,PETER_mins_since_rest']
    
    windows=[]
    duration_list=[]
    foul_list=[]
    for i in range(21-window_size):
        lower_bound = i
        upper_bound = i+window_size
        
        
        temp_df=df[(df[rest_cols].mean(axis=1)>=lower_bound) & (df[rest_cols].mean(axis=1)<upper_bound)]
        
        dates=list(temp_df.Date.unique())
        splits=[]
        for date in dates:
            temp_df2 = temp_df[temp_df.Date==date]
            for half in [1,2]:
                half_df = temp_df2[temp_df2.Half == half]
                groups = consecutive_groups(list(half_df.index))
        
                group_idxs = [list(g) for g in groups]
                
                
                if len(group_idxs)>0:
                    splits.extend(group_idxs)
                
       
        total_duration=0
        total_fouls=0
        for split in splits:
            temp_df3 = temp_df.loc[split,:]
            duration = calc_duration(temp_df3)
            n_fouls = len(temp_df3[temp_df3.UM_event=='FOUL'])
            total_duration+=duration
            total_fouls+=n_fouls
        


        windows.append((lower_bound,upper_bound))
        duration_list.append(total_duration)
        foul_list.append(total_fouls)
        
    return foul_list, duration_list, windows

def player_season_minutes(df,player):
    from more_itertools import consecutive_groups
    import numpy as np
    
    dates=list(df.Date.unique())
    splits=[]
    for date in dates:
        temp_df = df[df.Date==date]
        for half in [1,2]:
            half_df = temp_df[temp_df.Half == half]
            half_df_p = half_df[half_df[player]==1]
            groups = consecutive_groups(list(half_df_p.index))
    
            group_idxs = [list(g) for g in groups]
            
            if len(group_idxs)>0:
                splits.extend(group_idxs)
    
    total_mins=0
    for split in splits:
        temp_df2 = df.loc[split,:]
        total_mins+=calc_duration(temp_df2)
        
    return total_mins

def player_season_foul_rate(df,player):
    um_col='FOUL by '+player
    player_mins=player_season_minutes(df, player)
    player_fouls = len(df[df.UM==um_col])
    foul_rate=player_fouls/player_mins
    
    return foul_rate

def team_shooting_rate(df, window_size=1):
    from more_itertools import consecutive_groups
    import numpy as np

    rest_cols=['ANDERSON,MACK_mins_since_rest',
       'EGUN,EDDY_mins_since_rest', 'FALLS,TIMMY_mins_since_rest',
       'VAZQUEZ,JOSH_mins_since_rest', 'MANUEL,KENDAL_mins_since_rest',
       'SAMUELSON,JARED_mins_since_rest',
       'CARTER-HOLLI,DERRICK_mins_since_rest', 'OWENS,KYLE_mins_since_rest',
       'PRIDGETT,SAYEED_mins_since_rest','SELCUK,YAGIZHAN_mins_since_rest','JONES,PETER_mins_since_rest']
    
    windows=[]
    duration_list=[]
    make_list=[]
    miss_list=[]
    for i in range(21-window_size):
        lower_bound = i
        upper_bound = i+window_size
        
        
        temp_df=df[(df[rest_cols].mean(axis=1)>=lower_bound) & (df[rest_cols].mean(axis=1)<upper_bound)]
        
        dates=list(temp_df.Date.unique())
        splits=[]
        for date in dates:
            temp_df2 = temp_df[temp_df.Date==date]
            for half in [1,2]:
                half_df = temp_df2[temp_df2.Half == half]
                groups = consecutive_groups(list(half_df.index))
        
                group_idxs = [list(g) for g in groups]
                
                
                if len(group_idxs)>0:
                    splits.extend(group_idxs)
                
       
        total_duration=0
        total_makes=0
        total_miss=0
        for split in splits:
            temp_df3 = temp_df.loc[split,:]
            duration = calc_duration(temp_df3)
            n_makes = len(temp_df3[temp_df3.UM_event.isin(['GOOD JUMPER','GOOD 3PTR','GOOD LAYUP','GOOD DUNK'])])
            n_misses = len(temp_df3[temp_df3.UM_event.isin(['MISS','MISS LAYUP','MISS JUMPER','MISS 3PTR','MISS DUNK'])])
            total_duration+=duration
            total_makes+=n_makes
            total_miss+=n_misses
        


        windows.append((lower_bound,upper_bound))
        duration_list.append(total_duration)
        make_list.append(total_makes)
        miss_list.append(total_miss)
        
        
    return make_list,miss_list, duration_list, windows


def opponent_shooting_rate(df, window_size=1):
    from more_itertools import consecutive_groups
    import numpy as np

    rest_cols=['ANDERSON,MACK_mins_since_rest',
       'EGUN,EDDY_mins_since_rest', 'FALLS,TIMMY_mins_since_rest',
       'VAZQUEZ,JOSH_mins_since_rest', 'MANUEL,KENDAL_mins_since_rest',
       'SAMUELSON,JARED_mins_since_rest',
       'CARTER-HOLLI,DERRICK_mins_since_rest', 'OWENS,KYLE_mins_since_rest',
       'PRIDGETT,SAYEED_mins_since_rest','SELCUK,YAGIZHAN_mins_since_rest','JONES,PETER_mins_since_rest']
    
    windows=[]
    duration_list=[]
    make_list=[]
    miss_list=[]
    for i in range(21-window_size):
        lower_bound = i
        upper_bound = i+window_size
        
        
        temp_df=df[(df[rest_cols].mean(axis=1)>=lower_bound) & (df[rest_cols].mean(axis=1)<upper_bound)]
        
        dates=list(temp_df.Date.unique())
        splits=[]
        for date in dates:
            temp_df2 = temp_df[temp_df.Date==date]
            for half in [1,2]:
                half_df = temp_df2[temp_df2.Half == half]
                groups = consecutive_groups(list(half_df.index))
        
                group_idxs = [list(g) for g in groups]
                
                
                if len(group_idxs)>0:
                    splits.extend(group_idxs)
                
       
        total_duration=0
        total_makes=0
        total_miss=0
        for split in splits:
            temp_df3 = temp_df.loc[split,:]
            duration = calc_duration(temp_df3)
            n_makes = len(temp_df3[temp_df3.Opponent_event.isin(['GOOD JUMPER','GOOD 3PTR','GOOD LAYUP','GOOD DUNK'])])
            n_misses = len(temp_df3[temp_df3.Opponent_event.isin(['MISS','MISS LAYUP','MISS JUMPER','MISS 3PTR','MISS DUNK'])])
            total_duration+=duration
            total_makes+=n_makes
            total_miss+=n_misses
        


        windows.append((lower_bound,upper_bound))
        duration_list.append(total_duration)
        make_list.append(total_makes)
        miss_list.append(total_miss)
        
        
    return make_list,miss_list, duration_list, windows