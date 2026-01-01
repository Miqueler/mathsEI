from unidecode import unidecode


with open("files/spa_news_2024_1M-sentences.txt") as file_sentences:
    sentences = file_sentences.readlines()

clean_sentences = []

for sentence in sentences:
    clean_sentence = ""
    for character in sentence:
        if character.lower() == "ñ":
            clean_sentence += character.lower()
        elif unidecode(character.lower()) in "abcdefghijklmnopqrstuvwxyz":
            clean_sentence += unidecode(character.lower())
    clean_sentences.append(clean_sentence)

cleaned_list = open("files/clean_list.txt", "w")
for i in clean_sentences:
    cleaned_list.write(i + ";")
cleaned_list.close()

print("Process compleated")
