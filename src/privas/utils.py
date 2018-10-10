def find_language(languages, language):
    lower_languages = list(x.lower() for x in languages)
    language = language.lower()
    for i, each in enumerate(lower_languages):
        if each == language:
            return i, languages[i]
    for i, each in enumerate(lower_languages):
        if each.startswith(language):
            return i, languages[i]
    return -1, None
