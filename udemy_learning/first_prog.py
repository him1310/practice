#--- double quotes inside the single quote---
print('These are the "quotes" from the famour poet')
print('hello' + ' World!')
greeting = "Hello"
name = "Bruce"
name = input("please enter your name: ")
print(greeting + ' ' + name)
print("He is in my custory \" his name is Himanshu \".")
print("""test " Himanshu " """)
anotherSplitString = """This is 
split \
screen \
""" # "\" it make the string in different line to behave- it just escapes new line
print(anotherSplitString)
print("the Number \t in line 1")
# we can use either \\ or "r" keyword for raw string in front of the string
print('C:\\Users\\hgupta\\test')
print(r"C:\Users\hgupta\test")
_test  = '0000test'
age ='test ' + ' rest ' + _test
print(age)
a = 12
b = 7
print(a // b) # integer division
print(a / b)
text = 'Norwegion Blue'
print(text[-1]) # -1 prints the last character
print(text[0:6]) # slicing the string
print(text[-7:12])
print(text[0:6:2]) # in the setps of 2. 0-6 means Norweg.. and then :2 means N r e - position 0,2,4
print(text[0:6:3]) # in the setps of 3. 0-6 means Norweg.. and then :3 means N w - position 0,3
print(text[-1::-3]) # slcing backword and counting
age = 24
print("my age is {0} years".format(age))
print("""Jan : {2}
Feb : {0}
Mar : {2}
Apr : {1}
""".format(28,30,31))
for i in range(1, 13):
    print("No. {0:2} squared is {1:3} and cube is {2:4}".format(i, i**2, i**3)) # after colon is field width

for i in range(1, 13):
    print("No. {0:2} squared is {1:<3} and cube is {2:<4}".format(i, i**2, i**3)) # greater than sign to left 
    # align it is more of the direction

print("Pi is approximately {0:12}".format(22 / 7))
print("Pi is approximately {0:12f}".format(22 / 7))
print("Pi is approximately {0:12.50f}".format(22 / 7))
print("Pi is approximately {0:52.50f}".format(22 / 7))
print("Pi is approximately {0:62.50f}".format(22 / 7))
print("Pi is approximately {0:72.50f}".format(22 / 7))

# Pi is approximately 3.142857142857143 - 1st line - Python prints 15 decimal points
# Pi is approximately     3.142857 {12f} --> Width = 12, decimals = 6 (default).
                                        # Default precision for f is 6 decimal places
# Pi is approximately 3.14285714285714279370154144999105483293533325195312
                # python3 ignores 12 from 12.50f gives precedence to 50f
# Pi is approximately 3.14285714285714279370154144999105483293533325195312
# Pi is approximately           3.14285714285714279370154144999105483293533325195312
# Pi is approximately                     3.14285714285714279370154144999105483293533325195312
    
# f strings introduces in python 3.6
print(f"Pi is approximately {22 / 7:.50f}") # formatting in f strings
