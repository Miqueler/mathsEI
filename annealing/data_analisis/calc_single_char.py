with open("files/clean_list.txt") as file:
    sentences = file.read().split(";")

frequency = {"a": 0,"b": 0,"c": 0,"d": 0,"e": 0,"f": 0,"g": 0,"h": 0,"i": 0,"j": 0,"k": 0,"l": 0,"m": 0,"n": 0,"o": 0,"p": 0,"q": 0,"r": 0,"s": 0,"t": 0,"u": 0,"v": 0,"w": 0,"x": 0,"y": 0,"z": 0,"ñ" : 0}
total_characters = 0

for sentence in sentences:
    for char in sentence:
        frequency[char] += 1
        total_characters +=1

for kv_pair in frequency:
    frequency[kv_pair] /= total_characters

final_frequency = open("files/single_char_prob.txt", "x")
final_frequency.write(f"{frequency}")

<<<<<<< HEAD
print("Finished process")
=======
print("Finished process")
>>>>>>> refs/remotes/origin/main
