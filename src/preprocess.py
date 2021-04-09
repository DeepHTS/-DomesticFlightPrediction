import os
import tqdm
import pandas as pd
import os
import glob
import datetime


def spire_process(spire_dir, save_dir):
    spire_data = pd.DataFrame()
    default_spire_path = os.path.join(spire_dir, "*")
    for i, spire_path in tqdm.tqdm(enumerate(glob.glob(default_spire_path))):
        data = pd.read_csv(spire_path, low_memory=False)
        data = data[data["origin_airport_icao"] == "RJTT"]
        data = data[data["destination_airport_icao"] == "ROAH"]
        spire_data = spire_data.append(data)
    
    spire_data.drop_duplicates(subset=["icao_actype", "scheduled_departure_time_utc"], inplace=True)
    spire_data.dropna(subset=["scheduled_departure_time_utc", "scheduled_arrival_time_utc"], inplace=True)

    sched_departure_timestamp = []
    sched_arrival_timestamp = []
    for i in range(len(spire_data)):
        sched_departure_timestamp.append(datetime.datetime.strptime(spire_data.iloc[i]["scheduled_departure_time_utc"].replace("Z", ""), "%Y-%m-%dT%H:%M:%S").timestamp())
        sched_arrival_timestamp.append(datetime.datetime.strptime(spire_data.iloc[i]["scheduled_arrival_time_utc"].replace("Z", ""), "%Y-%m-%dT%H:%M:%S").timestamp())

    spire_data["scheduled_departure_timestamp"] = pd.Series(sched_departure_timestamp)
    spire_data["scheduled_arrival_timestamp"] = pd.Series(sched_arrival_timestamp)

    save_path = os.path.join(save_dir, "spire.csv")
    spire_data.to_csv(save_path)
    print("save spire.", len(spire_data))
    return spire_data


def spire_and_flightradar(trainvaltest, spire_data, flights_data, flightradar_position_dir):
    test_candidate_list = []
    cnt = 0
    for idx, flight_csv_path in tqdm.tqdm(enumerate(trainvaltest)):
        if idx % 1000 == 0:
            print(cnt)
        if flight_csv_path[-1] == "\n":
            flight_csv_path = flight_csv_path[:-1]
        flight_id = int(flight_csv_path.split(".")[0])
        position_path = os.path.join(flightradar_position_dir, flight_csv_path)
        positions = pd.read_csv(position_path)
        dep_timestamp = positions.iloc[0]["snapshot_id"]
        arr_timestamp = positions.iloc[-1]["snapshot_id"]
        flight = flights_data[flights_data["flight_id"] == flight_id]

        if len(flight) < 1:
            print("There isn't %s in flight data." % flight_id, type(flight_id))
            continue

        icao_code = flight.iloc[0]["equip"]
        timetables = spire_data[spire_data["icao_actype"] == icao_code]

        for i in range(len(timetables)):
            timetable = timetables.iloc[i]
            sch_from = timetable["scheduled_departure_timestamp"]
            sch_to = timetable["scheduled_arrival_timestamp"]

            if sch_from - 3600 * 2 < dep_timestamp and arr_timestamp < sch_to + 3600 * 2:
                test_candidate_list.append(flight_csv_path)
                cnt += 1
                break

    return test_candidate_list


def get_airport(airport_path):
    airport_info = pd.read_csv(airport_path)
    oka = airport_info[airport_info["iata_code"] == "OKA"]
    hnd = airport_info[airport_info["iata_code"] == "HND"]
    airport2point = {
        "OKA": (oka.iloc[0]["latitude_deg"], oka.iloc[0]["longitude_deg"]),
        "HND": (hnd.iloc[0]["latitude_deg"], hnd.iloc[0]["longitude_deg"]),
    }
    print("read airport.")
    return airport2point


def trainvaltest_process(trainvaltest_path):
    trainvaltest = []
    with open(trainvaltest_path, "r") as f:
        candidate = f.readlines()
        for c in candidate:
            trainvaltest.append(c[:-1])
    print("read trainvaltest.", len(trainvaltest))
    return trainvaltest


def main():
    airport_path = "/home/jo-kwsm/workspace/DomesticFlightPrediction/data/airports.csv"
    save_dir = "/home/jo-kwsm/workspace/DomesticFlightPrediction/data/"
    spire_dir = "/home/jo-kwsm/synology/horie/nict/data/spire_all"
    flightradar_path = "/home/jo-kwsm/synology/horie/nict/data/flightradar24_processed/20190101-20191231_HND-OKA/preprocess/flights.csv"
    flightradar_position_dir = "/home/jo-kwsm/synology/horie/nict/data/flightradar24_processed/20190101-20191231_HND-OKA/spline/positions"
    trainvaltest_dir = "/home/jo-kwsm/synology/horie/nict/data/flightradar24_processed/20190101-20191231_HND-OKA/spline/"
    trainvaltest_path = os.path.join(trainvaltest_dir, "trainvaltest.txt")
    train_path = os.path.join(trainvaltest_dir, "train.txt")
    val_path = os.path.join(trainvaltest_dir, "val.txt")
    test_path = os.path.join(trainvaltest_dir, "test.txt")
    airport2point = get_airport(airport_path)
    flights_data = pd.read_csv(flightradar_path)
    spire_data = spire_process(spire_dir, save_dir)
    # spire_data = pd.read_csv(os.path.join(save_dir, "spire.csv"))

    trainvaltest = trainvaltest_process(trainvaltest_path)
    test_candidate_list = spire_and_flightradar(trainvaltest, spire_data, flights_data, flightradar_position_dir)
    
    with open(test_path, "w") as f:
        f.write("\n".join(test_candidate_list[:1000]))
        f.write("\n")
    with open(val_path, "w") as f:
        f.write("\n".join(test_candidate_list[1000:2000]))
        f.write("\n")
    with open(train_path, "w") as f:
        f.write("\n".join(test_candidate_list[2000:]))
        f.write("\n")
        for d in trainvaltest:
            if not d in test_candidate_list:
                f.write(d)

if __name__ == "__main__":
    main()
