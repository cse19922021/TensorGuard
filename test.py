def getMaxAdditionalDinersCount(N, K , M , S) -> int:
  # Write your code here
  counter = 0
  row = [0] * N
  for seats in S:
    row[seats-1] = 1
  for i, idx in enumerate(row):
    if row[i] == 1 and K <  i < len(row)-1-K:
      row[i-K] = 2
      row[i-K+1] = 2
      row[i+K] = 2
      row[i+K-1] = 2
    if row[i] == 1 and i <= K:
      row[i-K] = 2
      row[i+K] = 2
    if row[i] == 1 and i > len(row)-1-K:
      row[i-K] = 2
      row[i-K+1] = 2
      row[i+K-1] = 2

getMaxAdditionalDinersCount(10, 1, 2, [2, 6])