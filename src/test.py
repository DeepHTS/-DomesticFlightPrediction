from plane import Plane

import time

def main():
	start = time.time()
	plane=Plane("data/OAG.csv")
	mid = time.time()
	print(mid-start, "seconds")
	cnt = plane.density(judge_time=0, point=(0,0))
	end = time.time()
	print(end-mid, "seconds")
	print(cnt)


if __name__ == "__main__":
  	main()
