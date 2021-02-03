import pandas as pd
import datetime
import math


class Plane:
    """
    国内線の密度を測定するためのクラス

    Attributes:
        timetable(pd.DataFrame):調査対象の時刻表
        airport2point(dict{code(str),point(tuple(latitude_deg:float, longitude_deg:float))}):空港のコードから座標を取得する辞書
        margin(int):滑走路など飛行前後で上空にいない時間(minute)
        area(int):密度を求める半径(km)
    """

    def __init__(self, data_path, airport_path, margin=10, area=10):
        # 必要なカラムのみを保存
        data_columns = set(
            [
                "Dep Airport Code",
                "Arr Airport Code",
                "Effective From",
                "Effective To",
                "Local Dep Time",
                "Local Arr Time",
                "Flying Time",
            ]
        )
        timetable = pd.read_csv(data_path)
        timetable = timetable[timetable["International/Domestic"] == "Domestic"]
        for column in timetable.columns:
            if column in data_columns:
                continue
            timetable = timetable.drop(column, axis=1)
        self.timetable = timetable

        # データ内に存在する空港のリスト
        airport_list = set(timetable["Dep Airport Code"].unique()) \
                    or set(timetable["Arr Airport Code"].unique())

        # IATAコードと座標を紐付ける
        self.airport2point = {}
        airport_data = pd.read_csv(airport_path)
        airport_data = self.airport_drop(airport_data)
        for _, row in airport_data.iterrows():
            if row["iata_code"] in airport_list:
                self.airport2point[row["iata_code"]] = (row["latitude_deg"], row["longitude_deg"])

        self.margin = datetime.timedelta(minutes=margin)
        self.radius = 6378.1
        self.area = area

    def __len__(self):
        return len(self.timetable)

    def airport_drop(self, data):
        """
        空港情報から不要な行を落とす
        """

        data = data[data["iso_country"]=="JP"]
        data = data[data["type"] != "heliport"]
        data = data[data["type"] != "closed"]
        data = data[data["name"] != "Kochi Ryoma Airport"]
        data = data.dropna(subset = ["iata_code", "latitude_deg", "longitude_deg"])

        return data

    def str2date(self, string):
        d, m, y = [int(i) for i in string.split("/")]
        t = datetime.date(y,m,d)
        return t

    def int2time(self, num):
        h = num//100
        m = num%100
        t = datetime.time(h,m)
        return t

    def divide(self, dep_point, arr_point, dep_datetime, arr_datetime, judge_datetime):
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

        point = ((arr_datetime - judge_datetime).total_seconds() * dep_point \
                + (judge_datetime - dep_datetime).total_seconds() * arr_point) \
                / (arr_datetime - dep_datetime).total_seconds()

        return point

    def get_point(self, idx, judge_datetime):
        """
        飛行機一機の座標を求める。
        線形計算。

        Args:
            idx(int):知りたいフライトのdataにおけるindex
            judge_datetime(datetime):位置を知りたい時刻
        Returns:
            tuple(latitude_deg:float, longitude_deg:float):飛行機のjudge_timeにおける座標
        Note:
            judge_time時に空中にいなければNoneを返す。
        """

        # 運行期間外なら処理しない
        ef_from = self.str2date(self.timetable["Effective From"].iloc[idx])
        ef_to = self.str2date(self.timetable["Effective To"].iloc[idx])
        if judge_datetime.date() < ef_from or ef_to < judge_datetime.date():
            return None

        # 時刻情報を処理
        dep_time = self.timetable["Local Dep Time"].iloc[idx]
        arr_time = self.timetable["Local Arr Time"].iloc[idx]
        dep_datetime = datetime.datetime.combine(judge_datetime.date(), self.int2time(dep_time))
        arr_datetime = datetime.datetime.combine(judge_datetime.date(), self.int2time(arr_time))

        if dep_datetime > arr_datetime:
            arr_datetime += datetime.timedelta(days=1)

        # フライトの時間によっては全日の情報を用いる
        if judge_datetime < dep_datetime and judge_datetime.date() - ef_from >= datetime.timedelta(days=1):
            dep_datetime -= datetime.timedelta(days=1)
            arr_datetime -= datetime.timedelta(days=1)

        # marginの時間分は空中にいない
        dep_datetime += self.margin
        arr_datetime -= self.margin

        # 飛行時間が短すぎる場合、求めたい時刻に空中にいない場合を無視
        if arr_datetime <= judge_datetime or arr_datetime <= dep_datetime:
            return None

        dep_airport = self.timetable["Dep Airport Code"].iloc[idx]
        arr_airport = self.timetable["Arr Airport Code"].iloc[idx]
        dep_point = self.airport2point[dep_airport]
        arr_point = self.airport2point[arr_airport]

        try:
            point = (
                self.divide(
                    dep_point[0],
                    arr_point[0],
                    dep_datetime,
                    arr_datetime,
                    judge_datetime,
                ),
                self.divide(
                    dep_point[1],
                    arr_point[1],
                    dep_datetime,
                    arr_datetime,
                    judge_datetime,
                ),
            )
        except:
            return None

        return point

    def distance(self, p1, p2):
        """
        2地点間の距離を返す

        Args:
            p1(tuple(latitude_deg:float, longitude_deg:float)):1つ目の地点の座標(deg)
            p2(tuple(latitude_deg:float, longitude_deg:float)):2つ目の地点の座標(deg)
        Returns:
            dis(float):2地点間の距離(km)
        """
        dis = math.sqrt((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)
        dis = math.radians(dis)
        dis = self.radius*dis

        return dis

    def density(self, judge_datetime, point):
        """
		csvの全データをget_point()で確認していき、中心座標から一定距離内に存在する機体の数を調べる。O(n)でn=200000なので2秒以内に実行可能。
			
		Args:
            judge_datetime(datetime):密度を知りたい時刻
            point(tuple(latitude_deg:float, longitude_deg:float)):密度を知りたい中心座標
        Returns:
            plane_num(int):中心座標から一定距離内に存在する機体の数
        """

        plane_num = 0

        for idx in range(len(self)):
            plane_point = self.get_point(idx, judge_datetime)
            if plane_point is None:
                continue
            if self.distance(plane_point, point) <=self.area:
                plane_num+=1

        return plane_num
