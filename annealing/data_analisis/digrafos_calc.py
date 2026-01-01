with open("files/clean_list.txt") as file:
    sentences = file.read().split(";")

frecuency_digrafos = {}
total_digraphs = 0
digrafo = ""

for sentence in sentences:
    num_chars = len(sentence)
    for char in range(num_chars):
        if char + 1 != num_chars:
            digrafo = sentence[char] + sentence[char + 1]


        if digrafo not in frecuency_digrafos:
            frecuency_digrafos.update({digrafo : 0})
        frecuency_digrafos[digrafo] += 1
        total_digraphs += 1

val_based = {k: v for k, v in sorted(frecuency_digrafos.items(), key=lambda item: item[1], reverse=True)}

for kv_pair in val_based:
    val_based[kv_pair] /= total_digraphs

final_frequency = open("files/digraphs_prob.txt", "x")
final_frequency.write(f"{val_based}")

<<<<<<< HEAD
print("Finished process")
=======
print("Finished process")
>>>>>>> refs/remotes/origin/main
