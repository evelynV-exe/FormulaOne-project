import fastf1
from fastf1.ergast import Ergast
import pandas as pd
import os

#enable cache
os.makedirs('content/f1_cache', exist_ok=True)
fastf1.Cache.enable_cache('content/f1_cache')
ergast = Ergast()

#BOLD
BOLD = '\033[1m'
END = '\033[0m'

#colors
GREEN  = '\033[92m'
YELLOW = '\033[93m'
RED    = '\033[91m'
PURPLE = '\033[95m'
CYAN   = '\033[96m'

TYRE_COLORS = {
    'SOFT': '\033[91m',    # Red
    'MEDIUM': '\033[93m',  # Yellow
    'HARD': '\033[97m',    # White
    'INTERMEDIATE': '\033[92m', # Green
    'WET': '\033[94m',     # Blue
}

#season
season = int(input("Enter the season year (e.g.2022): "))
race = input("Enter race name: ").strip()
sessionType = input("Enter the session " "(R=Race, Q=Qualifying, FP1, FP2, FP3, S=Sprint): ").strip().upper()
driver = input("Enter the driver code (e.g. VER, HAM, LEC): ").strip().upper()

#load session                   Y   Race    session
session = fastf1.get_session(season, race, sessionType)
session.load()

#results
results = session.results

#Round
ROUND = session.event['RoundNumber']

#driver standing
standings = ergast.get_driver_standings(season, ROUND)
standings_df = standings.content[0]

#constructor standing
constructor = ergast.get_constructor_standings(season, ROUND)
constructor_df = constructor.content[0]

#select driver
All_laps = session.laps.pick_drivers(driver)

print(f"\nLap Times for {driver}: \n")

print(f"{'Lap':<5} "
      f"{'Time':<15} "
      f"{'Tyre':<15} "
      f"{'Stint':<6} "
      f"{'Status'}")
print("=" * 60)

Qlaps = All_laps.pick_quicklaps()
Qnum = set(Qlaps['LapNumber'])

fastest = None
times = []

prev_stint = None
pitEvent = []

valid_laps = All_laps[All_laps['LapTime'].notna()]
absoluteFastest = valid_laps['LapTime'].dt.total_seconds().min()

#get the lap time for each lap
for _, lap in All_laps.iterrows():

    #skip invalid lap times
    if pd.isna(lap['LapTime']): continue

    seconds = lap['LapTime'].total_seconds()
    times.append(seconds)

    if fastest is None or seconds < fastest:
        fastest = seconds

    laptime_str = f"{int(seconds//60)}:{seconds%60:06.3f}"

    if seconds == absoluteFastest:
        laptime_str = f"{PURPLE}{laptime_str}{END}"

    status = []
    track = str(lap['TrackStatus'])

    if track == '1': status.append(f"{GREEN}GREEN{END}")
    elif track == '2': status.append(f"{YELLOW}YELLOW{END}")
    elif track in ['4', '6', '7']: status.append(f"{RED}SAFETY CAR / VSC{END}")
    else: status.append(f"TRACK {track}")

    if pd.notna(lap['PitInTime']): status.append(f"{CYAN}PIT IN{END}")
    if pd.notna(lap['PitOutTime']): status.append("PIT OUT")

    if lap['LapNumber'] in Qnum: status.append(f"{PURPLE}QUICK{END}")

    tyre = lap['Compound']
    color = TYRE_COLORS.get(tyre, '\033[97m')
    tyreDisplay = f"{color}{tyre}{END}"

    stint = lap['Stint']

    if prev_stint is not None and stint != prev_stint:
            pitEvent.append((int(lap['LapNumber']),
                            prev_stint, stint, tyre))
    prev_stint = stint

    print(f"{int(lap['LapNumber']):<5} {laptime_str} {tyreDisplay} {stint:<6} {', '.join(status)}")
    
#Lap Time
laps = All_laps.copy()
# remove invalid laps
laps = laps[laps['LapTime'].notna()]

#remove pit in/out laps
laps = laps[laps['PitInTime'].isna() &
            laps['PitOutTime'].isna()]

#remove the safety car / vcs laps
laps = laps[laps['TrackStatus'] == '1']

laps = laps.pick_quicklaps()

race_pace = laps['LapTime'].mean()
pace_second = race_pace.total_seconds()
minutes = int(pace_second//60)
sec = pace_second % 60

print("=" * 50)

#results
driverResult = results[results['Abbreviation'] == driver].iloc[0]
teamName = driverResult['TeamName']

search_term = teamName.split()[0]

driverStanding = standings_df[standings_df['driverCode'] == driver]
teamStanding = constructor_df[constructor_df['constructorName'].str.contains(search_term, case=False, na=False)]

print(f"\n{BOLD}Team                          :{END} {driverResult['TeamName']}")
print(f"{BOLD}Position Finished             :{END} P{int(driverResult['Position'])}")
print(f"{BOLD}Points earned                 :{END} {driverResult['Points']}")

print('-' * 25)

if not driverStanding.empty:
    d_pts = driverStanding['points'].iloc[0]
    d_pos = driverStanding['position'].iloc[0]
    print(f"{BOLD}DRIVER STANDING             :{END} P{int(d_pos)}")
    print(f"{BOLD}TOTAL DRIVER POINTS         :{END} {d_pts}")
else:
    print("Driver Standing data not found.")

print('-' * 25)

if not teamStanding.empty:
    team_row = teamStanding.iloc[0]

    c_pts = team_row['points']
    c_pos = team_row['position']
    c_teamName = team_row['constructorName']

    print(f"{BOLD}CONSTRUCTOR STANDING        :{END} P{int(c_pos)}")
    print(f"{BOLD}TOTAL CONSTRUCTOR POINTS    :{END} {c_pts}")
else:
    print(f"Constructor data for '{teamName}' not found in Ergast.")

print("=" * 50)

print(f"\n{BOLD}Race Pace:{END} {minutes}:{sec:06.3f}")

#pit stops
print(f"\n{BOLD}Pit Stops / Stint Changes:{END}\n")
if len(pitEvent) == 0:
    print("No pit stops detected.")
else:
    for lapNum, oldStint, newStint, tyre in pitEvent:
        color = TYRE_COLORS.get(tyre, '')
        tyreDisplay = f"{color}{tyre.ljust(8)}{END}"
        print(f"Pit stop before lap {lapNum} | "
              f"Stint {oldStint} -> {newStint} | "
              f"New Tyre: {tyreDisplay}")

#average time
avg = sum(times) / len(times)

fastest_lap = laps.pick_fastest()
slowest_lap = laps.loc[laps['LapTime'].idxmax()]

stats = [("Fastest", fastest_lap['LapTime'].total_seconds(), fastest_lap['LapNumber']), 
         ("Slowest", slowest_lap['LapTime'].total_seconds(), slowest_lap['LapNumber']), 
         ("Average", avg, None)]

#print the result
for label, value, lap_num in stats:
    minutes = int(value//60)
    remaining = value%60

    time = f"{minutes}:{remaining:06.3f}"

    if label=="Fastest":
        display = f"{PURPLE}{BOLD}{time}{END}"
    else:
        display = f"{BOLD}{time}{END}"

    if lap_num is not None:
        print(f"\n{BOLD}{label}{END} : {display} at lap {int(lap_num)}")
    else:
        print(f"\n{BOLD}{label}{END} : {display}")
