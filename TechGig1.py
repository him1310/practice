import sys

def main():
    N, X = input().split()
    arr = [int(arr) for arr in input().split()]
    if len(arr) != int(N):
        sys.exit
    arr = sorted(arr)

    print(arr[int(N)-int(X)])
    # x = [int(x) for x in input().split(" ")]
    # print("Number of list is: ", x)

if __name__ == "__main__":
    main()