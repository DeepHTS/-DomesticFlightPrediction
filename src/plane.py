import pandas as pd
import datetime

class Plane:

    def __init__(self, data_path):
        columns = set(
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
        self.timetable = pd.DataFrame({column:timetable[column] for column in columns})

    
    def str2time(self, string):
        h, m = [int(i) for i in string.split(":")]
        t = datetime.time(h,m)
        return t


    def time_delta(self, tf, tt):
        if type(tf) is str:
            tf=str2time(tf)
        if type(tt) is str:
            tt=str2time(tt)
        df = datetime.datetime.combine(datetime.date.today(), tf)
        dt = datetime.datetime.combine(datetime.date.today(), tt)

        if df > dt:
            dt += datetime.timedelta(day=1)
        
        return dt-df


    def dis_check(self, p1, p2, threshold):
        """
        2地点間の距離が閾値以下かどうかを判定

        Args:
        p1(tuple(int,int)):1つ目の地点の座標
        p2(tuple(int,int)):2つ目の地点の座標
        Returns:
        res(boolean):2地点間の距離が閾値以下かどうか
        以下ならTrue
        Note:
        地点が片方でもNoneならFalseを返す
        """
        if p1 is None or p2 is None:
            res = False
        else:
            res = (sqrt((p1[0]-p2[0])**2+(p1[1]-p2[1])**2) <= threshold)
        return res


    def position(self, dep_time, arr_time, judge_time, dep_airport, arr_airport):
        """
        飛行機一機の座標を求める。
        線形計算。

        Args:
            dep_time(datetime):出発時刻
            arr_time(datetime):到着時刻
            judge_time(datetime):位置を知りたい時刻
            dep_airport(str):出発空港コード
            arr_airport(str):到着空港コード
        Returns:
            tuple(latitude:int, longitude:int):飛行機のjudge_timeにおける座標
        Note:
            judge_time時に空中にいなければNoneを返す。
        """
        return None
  

    def density(self, judge_time, point):
        """
		csvの全データをposition()で確認していき、中心座標から一定距離内に存在する機体の数を調べる。O(n)でn=200000なので2秒以内に実行可能。
			
		Args:
            judge_time(datetime):密度を知りたい時刻
            point(tuple(latitude:int, longitude:int)):密度を知りたい中心座標
        Returns:
            plane_num(int):中心座標から一定距離内に存在する機体の数
        """

        plane_num = 0

        for row in self.timetable.iterrows():
            plane_num+=1
            if self.dis_check(self.position(0, 0, judge_time, 0, 0), point, 10):
                plane_num+=1

        return plane_num
