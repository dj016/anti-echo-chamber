# This is to merge all the files into a single file.

import json

with open('C:/Users/dhagarw/projects/aec/ParsedDataSet/news.json') as f:
  data=json.load(f)
  # print(data[0].get('title'))
  print(data[0].get('body'))
  # print(data[0].get('source'))
  # print(data[0].get('published_at'))
