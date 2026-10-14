#encoding: utf-8
"""Машина логічного виведення для розширення Foam редактора VS Code.
Тріплети фактів бази знань (Subject, Property, Object) подаються як посилання, приблизно так, як це робиться в Semantic MediaWiki:
# Subject
[Property](Object.md)
де Subject - заголовок документу
"""

import os, re

def parse(filename, properties=[], base_path=None):
    """Шукає усі посилання у файлі filename в форматі [property](object.md)
та додає в базу знань KB факт (filename, property, object)"""
    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()
    KB = set()
    for mo in re.finditer(r'\[(.*?)\]\((.*?\.md)\)', text):
        if base_path:
            s = os.path.relpath(filename, base_path).replace("\\", "/")
        else:
            s = os.path.basename(filename)
        p = mo.group(1)
        if properties and p not in properties:
            continue
        o = mo.group(2).replace("\\", "/")
        KB.add((s, p, o))
    return KB

def foam2KB(path, properties=[]):
    """Повертає множину фактів шляхом синтаксичного аналізу файлів .md каталогу path"""
    KB = set()
    for root, dirs, files in os.walk(path):
        for f in files:
            if os.path.splitext(f)[1] == '.md':
                K = parse(os.path.join(root, f), properties, base_path=path)
                KB.update(K)
    return KB

def reasoner(KB, property='isCause'):
    """Найпростіша машина логічного виведення для інверсної властивості property.
    Повертає множину виведених фактів"""
    K = set()
    for s, p, o in KB:
        if p == property:
            K.add((o, 'isEffect', s))
    return K

def facts2foam(KB, path="."):
    """Дописує виведені факти в кінець відповідних файлів .md. Обережно!"""
    for s, p, o in KB:
        fn = os.path.join(path, s)
        if os.path.exists(fn):
            with open(fn, 'a', encoding="utf-8") as f:
                ref = '\n[' + p + ']' + '(' + o + ')\n'
                f.write(ref)

def facts2mermaid(KB, properties=[], path="."):
    """Створює у файлі .md Mermaid-граф з фактами KB."""
    tmp = """# Inferred Facts Graph

```mermaid
graph TD;
%s
```
"""
    facts = ""
    for s, p, o in sorted(KB):
        if properties and p not in properties:
            continue
        clean_s = s.replace(".md", "").replace("/", "_")
        clean_o = o.replace(".md", "").replace("/", "_")
        facts += f"    {clean_s} -->|{p}| {clean_o};\n"
    if not facts:
        return
    with open(os.path.join(path, 'Infered.md'), 'w', encoding="utf-8") as f:
        f.write(tmp % facts)

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(current_dir, "FoamTest")
    if not os.path.exists(path):
        path = "c:\\FoamTest"

    if os.path.exists(path):
        KB = foam2KB(path, ['isCause', 'isEffect'])
        print("Базові факти FoamTest:", KB)
        K = reasoner(KB)
        print("Виведені факти (isEffect):", K)
        facts2mermaid(KB.union(K), path=path)
        print("Mermaid-граф згенеровано в Infered.md")
    else:
        print(f"Каталог {path} не знайдено.")