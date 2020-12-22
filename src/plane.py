import pandas as pd
import datetime
import math


class Plane:
    """
    国内線の密度を測定するためのクラス

    Attributes:
        timetable(pd.DataFrame):時刻表
        airport2point(dict{code(str),point(tuple(latitude_deg:float, longitude_deg:float))}):空港のコードから座標を取得する辞書
        date(datetime.date):インスタンス生成時の日付。日をまたぐ処理で使用
        margin(int):滑走路など飛行前後で上空にいない時間(minute)
        area(int):密度を求める半径(km)
    """

    def __init__(self, data_path, airport_path, margin=10, area=10):
        # 飛行データの内必要なカラムのみを保存
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
        timetable = timetable[timetable["International/Domestic"]=="Domestic"]
        for column in timetable.columns:
            if column in data_columns:
                continue
            timetable = timetable.drop(column, axis=1)
        self.timetable = timetable

        # データ内に存在する空港のリスト
        airport_list = set(timetable["Dep Airport Code"].unique()) or set(timetable["Arr Airport Code"].unique())

        # IATAコードと座標を紐付ける
        self.airport2point = {}
        airport_data = pd.read_csv(airport_path)
        airport_data = self.airport_drop(airport_data)
        for _, row in airport_data.iterrows():
            if row["iata_code"] in airport_list:
                self.airport2point[row["iata_code"]] = (row["latitude_deg"], row["longitude_deg"])

        self.date = datetime.date.today()
        self.margin = datetime.timedelta(minutes=margin)
        self.radius = 6378.1
        self.area = area


    def __len__(self):
        return len(self.timetable)


    def airport_drop(self, data):
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


    def int2datetime(self, num):
        h = num//100
        m = num%100
        t = datetime.datetime.combine(self.date, datetime.time(h,m))
        return t


    def divide(self,dep_point, arr_point, dep_datetime, arr_datetime, judge_datetime):
        point = ((arr_datetime - judge_datetime).total_seconds()*dep_point + (judge_datetime - dep_datetime).total_seconds()*arr_point) / (arr_datetime - dep_datetime).total_seconds()

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
        ef = self.str2date(self.timetable["Effective From"].iloc[idx])
        et = self.str2date(self.timetable["Effective To"].iloc[idx])
        ef = datetime.datetime.combine(ef, datetime.time(0, 0))
        et = datetime.datetime.combine(et, datetime.time(23, 59))
        if judge_datetime < ef or et < judge_datetime:
            return None

        # 時刻情報を処理
        dep_time = self.timetable["Local Dep Time"].iloc[idx]
        arr_time = self.timetable["Local Arr Time"].iloc[idx]
        dep_datetime = self.int2datetime(dep_time)
        arr_datetime = self.int2datetime(arr_time)

        if dep_datetime > arr_datetime:
            arr_datetime += datetime.timedelta(days=1)

        dep_datetime += self.margin
        arr_datetime -= self.margin

        if judge_datetime <= dep_datetime or arr_datetime <= judge_datetime or arr_datetime <= dep_datetime:
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
                    judge_datetime
                ),
                self.divide(
                    dep_point[1],
                    arr_point[1],
                    dep_datetime,
                    arr_datetime,
                    judge_datetime
                ),
            )
        except:
            return None

        return point


    def distance(self, p1, p2):
        """
        2地点間の距離を返す

        Args:
        p1(tuple(float,float)):1つ目の地点の座標
        p2(tuple(float,float)):2つ目の地点の座標
        Returns:
        dis(float):2地点間の距離(km)
        """
        dis = math.sqrt((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)
        dis = math.radians(dis)
        dis = self.raius*dis
        return dis


    def density(self, judge_datetime, point):
        """
		csvの全データをget_point()で確認していき、中心座標から一定距離内に存在する機体の数を調べる。O(n)でn=200000なので2秒以内に実行可能。
			
		Args:
            judge_datetime(datetime):密度を知りたい時刻
            point(tuple(latitude:int, longitude:int)):密度を知りたい中心座標
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
