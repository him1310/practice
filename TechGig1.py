import sys

def main():
    N, X = input().split()
    arr = [int(arr) for arr in input().split()]
    if int(X) < int (N):
        arr.sort()
        if arr[int(N)-int(X)] == arr[int(N)-int(X) - 1]:
            print(-1)
        else:
            print(arr[int(N)-int(X)])
    else:
        print(-1)
    # x = [int(x) for x in input().split(" ")]
    # print("Number of list is: ", x)
    

if __name__ == "__main__":
    main()