def main():
    N, M = map(int, input().split())
    arr = [int(arr) for arr in input().split()]
    queries = [int(queries) for queries in input().split()]

    arr_tc = []

    for i in range(0, M):
        total_cost = 0
        for j in range(0, N):
            value = arr[j] - queries[i]
            if value >= 0:
                total_cost += value
            else:
                value *= -1
                total_cost += value
        arr_tc.append(total_cost)
    for value in arr_tc:
        print(value)


if __name__ == "__main__":
    main()