#v1.2 - 200 SMA removed from buy & sell criteria. 
#v1.2 - Exit signal stochastic cross above 50(shorts) or below 50 (longs) 

import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt

#Convert CSV file to Dataframe
df = pd.read_csv("/Users/garethregan/Downloads/1346_1105637_bundle_archive/bitstampUSD_1-min_data_2012-01-01_to_2020-04-22.csv")
#Removes all data that is NAN
df = df.dropna()
# Converts Timestamp data type from string to Datetime. 
df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
#Set index to Timestamp
df.index = df['Timestamp']
# Removes old Timestamp column
df= df.drop('Timestamp', axis=1)
# Selects all times @ 00:00:00 (daily closes)
df= df.at_time('00:00:00')

# Daily moving averages

df['26 EMA'] = df['Close'].ewm(span=26,adjust=False).mean().round(2)
df['55 EMA'] = df['Close'].ewm(span=55,adjust=False).mean().round(2)
df['200 EMA'] = df['Close'].ewm(span=200,adjust=False).mean().round(2)
df['200 SMA'] = df['Close'].rolling(window=200).mean().round(2)

# stochastic oscillator (%K = 100(C – L14)/(H14 – L14))

df['L14'] = df['Low'].rolling(window=14).min()
df['H14'] = df['High'].rolling(window=14).max()
df['%K'] = 100 * ( (df['Close'] - df['L14']) / (df['H14'] - df['L14']) )
df['%D'] = df['%K'].rolling(window=3).mean()

#Plots BTC price and Stochastic

fig, axes = plt.subplots(nrows=2, ncols=1,figsize=(20,10))
df['Close'].plot(ax=axes[0]); axes[0].set_title('Close')
df[['%K','%D']].plot(ax=axes[1]); axes[1].set_title('Oscillator')

# Sell signal criteria

# Price below 200 SMA and EMA = Bearish Market

df['Bear'] = df['Close'] < df['200 EMA']

#Bear Cross of 26 & 55 EMAs with downward slope on 55

df['MA Bear Cross'] = (df['26 EMA'] < df['55 EMA']) & (df['55 EMA'] < df['55 EMA'].shift(1))

#Stoch Bear cross below 50 

df['Stoch Bear Cross'] = ((df['%K'] < df['%D']) & (df['%K'].shift(1) > df['%D'].shift(1))) & (df['%K'] < 50) 

#Sell if all above True. 

df['Sell signal'] = (df['Bear'] & df['MA Bear Cross'] & df['Stoch Bear Cross'] == True)

#Sell exit signal

df['Sell exit'] = (df['%K'] > 50)

#creates a placeholder column to populate with short positions (-1 for short and 0 for flat) using boolean values created above 

df['Short'] = np.nan 
df.loc[df['Sell signal'],'Short'] = -1 
df.loc[df['Sell exit'],'Short'] = 0 

#Set initial position on day 1 to flat

df['Short'][0] = 0 

#Forward fill the position column to represent the holding of positions through time 

df['Short'] = df['Short'].fillna(method='pad') 

# Buy Signal Criteria

# Price above 200 SMA and EMA = Bullish Market

df['Bull'] = df['Close'] > df['200 EMA']

#Bull Cross of 26 & 55 EMAs with downward slope on 55

df['MA Bull Cross'] = (df['26 EMA'] > df['55 EMA']) & (df['55 EMA'] > df['55 EMA'].shift(1))

#Stoch Bull cross Above 50 

df['Stoch Bull Cross'] = ((df['%K'] > df['%D']) & (df['%K'].shift(1) < df['%D'].shift(1))) & (df['%K'] > 50) 

#Buy if all above True. 

df['Buy signal'] = (df['Bull'] & df['MA Bull Cross'] & df['Stoch Bull Cross'] == True)

#Buy exit signal

df['Buy exit'] = (df['%K'] < 50)

#create a placeholder column to polulate with long positions (1 for long and 0 for flat) using boolean values created above 

df['Long'] = np.nan  
df.loc[df['Buy signal'],'Long'] = 1  
df.loc[df['Buy exit'],'Long'] = 0  

#Set initial position on day 1 to flat 

df['Long'][0] = 0  

#Forward fill the position column to represent the holding of positions through time 

df['Long'] = df['Long'].fillna(method='pad') 

#Add Long and Short positions together to get final strategy position (1 for long, -1 for short and 0 for flat) 

df['Position'] = df['Long'] + df['Short']

#plots position

df['Position'].plot(figsize=(20,10))

#Set up a column holding the daily BTC returns

df['Market Returns'] = df['Close'].pct_change()

#Create column for Strategy Returns by multiplying the daily BTC returns by the position that was held at close of previous day

df['Strategy Returns'] = df['Market Returns'] * df['Position'].shift(1)

#Finally plot the strategy returns versus BTC returns

df[['Strategy Returns','Market Returns']].cumsum().plot()

df