from plane import Plane
import datetime

import time

def main():
	start = time.time()
	plane=Plane("data/OAG.csv", "data/airports.csv")
	mid = time.time()
	print(mid-start, "seconds")
	judge_datetime = datetime.datetime(2019, 5, 1, 12, 0)
	cnt = plane.density(judge_datetime, point=(0,0))
	end = time.time()
	print(end-mid, "seconds")
	print(cnt)


if __name__ == "__main__":
  	main()
