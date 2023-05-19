import re

def main():
    # str = 'an example word:cat!!'
    # match = re.search(r'word', str)
    # print(match.group())

    # str = 'purple alice-b@google.com monkey dishwasher'
    # match = re.search(r'\w+@', str)
    # if match:
    #     print(match.group()) 
    # pass
    
    ## Search for pattern 'iii' in string 'piiig'.
    ## All of the pattern must match, but it may appear anywhere.
    ## On success, match.group() is matched text.
    match = re.search(r'iig', 'piiig') # found, 
    print(match.group())
    # match = re.search(r'igs', 'piiig') # not found, match == None
    print(match.group())

    ## . = any char but \n
    match = re.search(r'..g', 'piiig') # found, match.group() == "iig"
    print(match.group())

    ## \d = digit char, \w = word char
    match = re.search(r'\d\d\d', 'p123g') # found, match.group() == "123"
    print(match.group())

    match = re.search(r't+\w', '@@abcd!! itttesttt1tt1t') # found, match.group() == "abc"
    print(match.group())



if __name__ == "__main__":
    main()