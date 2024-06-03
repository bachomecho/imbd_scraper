# this module is intended to be used as a translator for the plot of the movie - under development
import deepl

auth_key = ""
translator = deepl.Translator(auth_key)

plot = "Hello, world!"
result = translator.translate_text(plot, target_lang="BG")
print(result.text)