import os
from copy import copy

def draw_prices(rows, prices):
    os.system('clear')

    l = min(prices)
    r = max(prices)
    prices = copy(prices)
    if l == r:
        prices = [rows - 1]*len(prices)
    else:
        for i in range(len(prices)):
            normalized = (prices[i] - l) / (r - l)
            prices[i] = rows - int(min(rows - 1, normalized*rows)) - 1

    for i in range(rows):
        s = ''
        for j in range(len(prices)):
            if prices[j] == i:
                s += '*'
            else:
                s += ' '

        print(f"{str(int(r - i * ((r - l) / rows))).ljust(20, ' ')} {s}")

