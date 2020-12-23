from plane import Plane
import datetime

import time

def main():
	start = time.time()
	plane=Plane("data/OAG.csv", "data/airports.csv")
	mid = time.time()
	print(mid-start, "seconds")
	# 2019年5月1日12時10分
	judge_datetime = datetime.datetime(2019, 5, 1, 12, 10)
	# 成田空港
	point = (35.764702, 140.386002)
	cnt = plane.density(judge_datetime, point)
	end = time.time()
	print(end-mid, "seconds")
	print(cnt)


if __name__ == "__main__":
  	main()
