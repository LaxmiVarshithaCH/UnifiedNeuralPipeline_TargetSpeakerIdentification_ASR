import re

class PunctuateModule:


    def __init__(self):
        pass

    def restore(self, text: str) -> str:
        if not text.strip():
            return ""

        text = re.sub(r"\s+", " ", text).strip()

        parts = re.split(r"( and | but | so | because | then )", text)

        sentences = []
        current = ""

        for p in parts:
            current += p
      
            if len(current.split()) > 8:
                sentences.append(current.strip())
                current = ""

        if current:
            sentences.append(current.strip())


        final_sents = []
        for s in sentences:
         
            if s.lower().startswith(("who", "what", "why", "how", "is", "are", "do", "did", "can", "will")):
                end = "?"
            else:
                end = "."

      
            s = s[0].upper() + s[1:]
            final_sents.append(s + end)

        return " ".join(final_sents)
