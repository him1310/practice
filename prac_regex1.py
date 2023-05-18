# "." --> matches any character
# "^" -> circumflex --> beginning of the line
# "$" --> indicates the end of line
# "*" --> matches any character repeated as many times as possible including zero.
# "+" --> matches one or more occurrences of the character before it. (from left side)
# "?" --> either zero or one occurrence of the character before it (from left side)
# "\w" --> matches any alphanumeric character and underscore with left most first
# "\d" --> matches any numeric with left most first
# "\s" --> matches any whitespace like space, tab, newline
# "\b" --> matches word boundaries


import re
result = re.search(r"aza", "plaza")
print(result)
result = re.search(r"aza", "bazaar")
print(result)
result = re.search(r"aza", "maze")
print(result)
print(re.search(r"^x", "xenox"))
print(re.search(r"p.ng", "penguin"))
print(re.search(r"a.a.e", "academia"))
print(re.search(r"p.ng", "Pangea", re.IGNORECASE))
########################################################################

# Lec Wildcards 2nd lecture
# usage of character classes - inside brackets
print(re.search(r"[pP]ython", "Python"))
print(re.search(r"[a-zA-Z0-9]loudy", "cloudy"))

print(re.search(r"[^a-zA-Z ]", "sentence with space.")) # Not a letter search
print(re.search(r"cat|dog", "I like cats and dogs")) # sentence with either cat or dog
print(re.findall(r"cat|dog", "I like cats and dogs")) # to find all the matches
####################################################################################

# Lec 3 Repition qualifiers

print(re.search(r"Py.*n", "Pygmalin"))
print(re.search(r"Py.*n", "Python Programming")) # greedy qualifier
# In the above it should have stopped at Python but * takes as many character as possible
print(re.search(r"Py[a-z]*n", "Python Programming")) # restrict greediness
print(re.search(r"Py[a-z]*n", "Pyn")) # restrict greediness
print(re.search(r"o+l+", "goldfish"))
print(re.search(r"o+l+", "woolly"))
print(re.search(r"o+l+", "boil")) # it has search pattern but it has "i" in between o & l

# The repeating_letter_a function checks if the text passed includes the letter "a" 
#(lowercase or uppercase) at least twice. For example, repeating_letter_a("banana") is True
# while repeating_letter_a("pineapple") is False"""
def repeating_letter_a(text):
  result = re.search(r"[aA].*[Aa]", text) # --> code within inverted commas
  return result != None

print(repeating_letter_a("banana")) # True
print(repeating_letter_a("pineapple")) # False
print(repeating_letter_a("Animal Kingdom")) # True
print(repeating_letter_a("A is for apple")) # True


print(re.search(r"p?each", "To each their own")) 
# even if p is present it becomes optional see the definition of "?" above
print(re.search(r"p?each", "I like peaches"))
####################################################################################

# Lec 4 Escaping Characters
import re
def check_character_groups(text):
  result = re.search(r"\w+\s+\w+", text)
  return result != None

print(check_character_groups("One")) # False
print(check_character_groups("123  Ready Set GO")) # True
print(check_character_groups("username user_01")) # True
print(check_character_groups("shopping_list: milk, bread, eggs.")) # False



print(re.search("\w+\s+\w+", "123  Ready Set GO" ))


###################################################################################

# Lec 5 Regex in action
print(re.search(r"A.*a", "Argnetina"))
print(re.search(r"A.*a", "Azerbaijan")) # it matches bcoz search string not stricter
print(re.search(r"^A.*a$", "Ajerbaijan"))

pattern = r"^[a-zA-z_][a-zA-Z0-9_]*$"
print(re.search(pattern, "this_is_valid_variable_name"))

print(re.search(pattern, "2myvarialble1"))

import re
def check_sentence(text):
  result = re.search(r"^[A-Z][a-z ]*[\.\?\!]$", text)
  return result

print(check_sentence("Is this is a sentence?")) # True
print(check_sentence("is this is a sentence?")) # False
print(check_sentence("Hello")) # False
print(check_sentence("1-2-3-GO!")) # False
print(check_sentence("A star is born.")) # True


