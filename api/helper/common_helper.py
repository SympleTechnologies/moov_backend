import math


# common helper functions

def get_distance(lat1, lon1, lat2, lon2, unit):
  """Get Distance
  This method gets two distance between 2 latitude and longitude in 
  both kilometers and nautical miles
  """
  radlat1 = math.pi * lat1/180
  radlat2 = math.pi * lat2/180
  theta = lon1 - lon2
  radtheta = math.pi * theta/180
  dist = (math.sin(radlat1) * math.sin(radlat2)) + \
          (math.cos(radlat1) * math.cos(radlat2) * math.cos(radtheta))
  dist = math.acos(dist)
  dist = dist * 180/math.pi
  dist = dist * 60 * 1.1515
  
  if unit.lower() == "k":
    dist = dist * 1.609344
    
  if unit.lower() == "n":
    dist = dist * 0.8684
    
  return int(round(dist, 0))
