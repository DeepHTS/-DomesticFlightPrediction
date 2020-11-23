from plane import Plane

def main():
  plane=Plane("data/OAG.csv")
  cnt = plane.density(judge_time=0, point=(0,0))
  print(cnt)

if __name__ == "__main__":
  main()
