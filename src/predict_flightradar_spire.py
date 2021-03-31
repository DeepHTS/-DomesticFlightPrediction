import os
import tqdm
import numpy as np
import pandas as pd


def divide(dep_point, arr_point, dep_datetime, arr_datetime, judge_datetime):
        """
        内分計算によって座標を求める。

        Args:
            dep_point(float):出発地点(deg)
            arr_point(float):到着地点(deg)
            dep_datetime(datetime):出発時刻
            arr_datetime(datetime):到着時刻
            judge_datetime(datetime):位置を知りたい時刻
        Returns:
            point(float):judge_datetimeにおける地点
        """

        point = ((arr_datetime - judge_datetime) * dep_point \
                + (judge_datetime - dep_datetime) * arr_point) \
                / (arr_datetime - dep_datetime)
        # print(
        #     (arr_datetime - judge_datetime),
        #     (judge_datetime - dep_datetime),
        #     (arr_datetime - dep_datetime),
        # )
        return point


def estimate_position(sch_from, sch_to, judge_datetime):
    dep_airport = "HND"
    arr_airport = "OKA"
    dep_point = airport2point[dep_airport]
    arr_point = airport2point[arr_airport]
    # if arr_airport != "OKA":
    #     print(arr_airport)
    point = (
        divide(
            dep_point[0],
            arr_point[0],
            sch_from,
            sch_to,
            judge_datetime,
        ),
        divide(
            dep_point[1],
            arr_point[1],
            sch_from,
            sch_to,
            judge_datetime,
        ),
    )
    return point


def main():
    default_position_path = "/home/jo-kwsm/synology/horie/nict/data/flightradar24_processed/20190101-20191231_HND-OKA/spline/positions"
    test_path = "/home/jo-kwsm/synology/horie/nict/data/flightradar24_processed/20190101-20191231_HND-OKA/spline/new_test.txt"
    spire_data = pd.read_csv("../../data/spire.csv")
    airport_path = "../../data/airports.csv"
    airport_info = pd.read_csv(airport_path)
    oka = airport_info[airport_info["iata_code"] == "OKA"]
    hnd = airport_info[airport_info["iata_code"] == "HND"]
    airport2point = {
        "OKA": (oka.iloc[0]["latitude_deg"], oka.iloc[0]["longitude_deg"]),
        "HND": (hnd.iloc[0]["latitude_deg"], hnd.iloc[0]["longitude_deg"]),
    }
    result = {
        "snapshot_id": [],
        "flight_id": [],
        "Predicted_lat": [],
        "Predicted_lon": [],
    }
    with open(test_path, "r") as f:
        test_data = f.readlines()
        for flight_csv_path in tqdm.tqdm(test_data):
            flight_csv_path = flight_csv_path[:-1]
            flight_id = int(flight_csv_path.split(".")[0])
            test_position_path = os.path.join(default_position_path, flight_csv_path)
            test_positions = pd.read_csv(test_position_path)
            dep_timestamp = test_positions.iloc[0]["snapshot_id"]
            arr_timestamp = test_positions.iloc[-1]["snapshot_id"]
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
                    break

            for i in range(len(test_positions)):
                test_position = test_positions.iloc[i]
                test_timestamp = test_position["snapshot_id"]
                if not test_timestamp % (60*5) == 0:
                    continue
                lat = np.nan
                lon = np.nan
                if sch_from < test_timestamp and test_timestamp < sch_to:
                    lat, lon = estimate_position(sch_from, sch_to, test_timestamp)
                if test_timestamp <= sch_from:
                    lat = airport2point["HND"][0]
                    lon = airport2point["HND"][1]
                if  sch_to <= test_timestamp:
                    lat = airport2point["OKA"][0]
                    lon = airport2point["OKA"][1]
                result["snapshot_id"].append(test_position["snapshot_id"])
                result["flight_id"].append(flight_id)
                result["Predicted_lat"].append(lat)
                result["Predicted_lon"].append(lon)
    
    result_path = "../../data/timetable_result.csv"
    result_df = pd.DataFrame(result, columns=["snapshot_id", "flight_id", "Predicted_lat", "Predicted_lon"])
    result_df.to_csv(result_path, index=None)


if __name__ == "__main__":
    main()
