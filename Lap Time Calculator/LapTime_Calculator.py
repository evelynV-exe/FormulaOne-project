import fastf1
import os

#enable cache
os.makedirs('content/f1_cache', exist_ok=True)
fastf1.Cache.enable_cache('content/f1_cache')

#                               Y   Race    session
session = fastf1.get_session(2025, 'Monaco', 'R')
session.load()

#select driver
driver_laps = session.laps.pick_drivers('VER')

print("Max Verstappen Lap Time:\n")

fastest = None
times = []

#get the lap time for each lap
for i, lap in enumerate(driver_laps['LapTime']):

    if lap is not None:
        seconds = lap.total_seconds()
        times.append(seconds)

        if fastest is None or seconds < fastest:
            fastest = seconds
        
        minutes = int(seconds//60)
        remaining = seconds % 60

        print(f"Lap {i + 1}: {minutes}:{remaining:06.3f}")

avg = sum(times) / len(times)

fastest_lap = driver_laps.pick_fastest()
slowest_lap = driver_laps.loc[driver_laps['LapTime'].idxmax()]

stats = [("Fastest", fastest_lap['LapTime'].total_seconds(), fastest_lap['LapNumber']), ("Slowest", slowest_lap['LapTime'].total_seconds(), slowest_lap['LapNumber']), ("Average", avg, None)]

#print the result
for label, value, lap_num in stats:
    minutes = int(value//60)
    remaining = value%60

    if lap_num is not None:
        print(f"\n{label} : {minutes}:{remaining:06.3f} at lap {int(lap_num)}")
    else:
        print(f"\n{label} : {minutes}:{remaining:06.3f}")
