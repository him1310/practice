# from video 54
# f = 3.3453456542334523434563465464534
# print(f.round(2))

IP = "117.131.208.10"
IP_reversed = ".".join(reversed(IP.split(".")))
print(IP_reversed)

dd = {
    "1" : 1,
    "2" : 2
}
c = None
try: 
    print(dd[c])
except KeyError:
    print("Key_error")
except Exception:
    print("test")
