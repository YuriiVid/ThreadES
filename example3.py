#encoding: utf-8
"""
Механізм логічного виведення "а-ля RETE" з правилами прямого та зворотного ходу.
Для пришвидшення алгоритму створюється дерево триплетів за предикатами.
Підтримуються правила:
- rule1: транзитивність (x, p, y) & (y, p, z) -> (x, p, z)
- rule2: симетрія / реверсивність (x, p, y) -> (y, p, x)
- rule_inverse: інверсні властивості (x, p1, y) -> (y, p2, x)
- rule_chain: ланцюгове виведення (x, p1, y) & (y, p2, z) -> (x, p3, z)
- backward_chaining: зворотне логічне виведення (goal-driven)
"""

def kb2tree(F):
    """Створює дерево з множини триплетів (словник, де ключі - предикати p)"""
    k = {t[1] for t in F}
    d = {i: set() for i in k}
    for t in F:
        d[t[1]].add(t)
    return d

def tree2kb(d):
    """Створює множину триплетів з дерева"""
    F = set()
    for k in d:
        F.update(d[k])
    return F

def rule1(d, p):
    """Правило для транзитивної властивості p:
    (x, p, y) & (y, p, z) -> (x, p, z)"""
    if p not in d:
        return False
    l = len(d[p])
    branch_copy = d[p].copy()
    for t in branch_copy:
        for r in branch_copy:
            if t[2] == r[0]:
                d[p].add((t[0], p, r[2]))
    return len(d[p]) != l

def rule2(d, p):
    """Правило для симетричної / реверсивної властивості p:
    (x, p, y) -> (y, p, x)"""
    if p not in d:
        return False
    l = len(d[p])
    for t in d[p].copy():
        d[p].add((t[2], p, t[0]))
    return len(d[p]) != l

def rule_inverse(d, p1, p2):
    """Правило для інверсних властивостей p1 та p2:
    (x, p1, y) -> (y, p2, x)
    Наприклад: (дефект, isCause, причина) -> (причина, isEffect, дефект)"""
    if p1 not in d:
        return False
    if p2 not in d:
        d[p2] = set()
    l = len(d[p2])
    for t in d[p1].copy():
        d[p2].add((t[2], p2, t[0]))
    return len(d[p2]) != l

def rule_chain(d, p1, p2, p3):
    """Правило композиційного (ланцюгового) виведення:
    (x, p1, y) & (y, p2, z) -> (x, p3, z)
    Наприклад: (дефект, isCause, причина) & (причина, усувається_через, захід)
    -> (дефект, рекомендація, захід)"""
    if p1 not in d or p2 not in d:
        return False
    if p3 not in d:
        d[p3] = set()
    l = len(d[p3])
    for t in d[p1].copy():
        for r in d[p2].copy():
            if t[2] == r[0]:
                d[p3].add((t[0], p3, r[2]))
    return len(d[p3]) != l

def reasoner(F, rules, *args):
    """Виводить нові факти з множини триплетів F шляхом застосування правил rules.
    Цикл застосування усіх правил повторюється, поки виводяться нові факти.
    Повертає множину зі старими і новими фактами."""
    d = kb2tree(F)
    n = 1
    while n:
        n = 0
        for r, a in zip(rules, args):
            # а передається як кортеж аргументів для правила r
            if isinstance(a, tuple):
                n += int(r(d, *a))
            else:
                n += int(r(d, a))
    return tree2kb(d)

def backward_chaining(kb, query):
    """Найпростіша машина зворотного виведення (backward chaining - bc).
    Перевіряє, чи підтверджується цільовий триплет query=(s, p, o)
    наявними фактами та правилами логіки.
    Якщо в query передано None як змінну, повертає множину значень, які задовольняють умову."""
    target_s, target_p, target_o = query

    # 1. Пряма перевірка у фактах
    direct_matches = set()
    for s, p, o in kb:
        match_s = (target_s is None or s == target_s)
        match_p = (target_p is None or p == target_p)
        match_o = (target_o is None or o == target_o)
        if match_s and match_p and match_o:
            direct_matches.add((s, p, o))

    if direct_matches and None not in query:
        return True
    elif direct_matches:
        return direct_matches

    # 2. Зворотне виведення через інверсію
    if target_p == "isEffect":
        # Перевіряємо гіпотезу через isCause(o, s)
        for s, p, o in kb:
            if p == "isCause" and (target_o is None or s == target_o) and (target_s is None or o == target_s):
                direct_matches.add((o, "isEffect", s))

    # 3. Зворотне виведення через ланцюг: рекомендація -> (дефект, isCause, X) & (X, усувається_через, Y)
    if target_p == "рекомендація":
        for s, p, o in kb:
            if p == "isCause" and (target_s is None or s == target_s):
                for s2, p2, o2 in kb:
                    if s2 == o and p2 == "усувається_через" and (target_o is None or o2 == target_o):
                        direct_matches.add((s, "рекомендація", o2))

    if None not in query:
        return len(direct_matches) > 0
    return direct_matches

if __name__ == "__main__":
    # Базовий приклад з методички:
    F = {(1, 2, 3), (3, 2, 4), (5, 2, 6), (1, 0, 7), (8, 0, 9)}
    A = reasoner(F, [rule1, rule2], (2,), (0,))
    print("Всі факти (rule1, rule2):", A)
    print("Виведені факти:", A - F)

    # Тест нових правил:
    F_demo = {
        ("дефект_шорсткість", "isCause", "зношений_різець"),
        ("зношений_різець", "усувається_через", "заміна_пластини")
    }
    A_demo = reasoner(
        F_demo,
        [rule_inverse, rule_chain],
        ("isCause", "isEffect"),
        ("isCause", "усувається_через", "рекомендація")
    )
    print("\nТест розширених правил:")
    print("Всі факти:", A_demo)
    print("Нові виведені факти:", A_demo - F_demo)
    print("\nТест зворотного виведення (backward_chaining):")
    print("Чи є дефект_шорсткість наслідком зношеного різця?",
          backward_chaining(F_demo, ("зношений_різець", "isEffect", "дефект_шорсткість")))
    print("Яка рекомендація для дефект_шорсткість?",
          backward_chaining(F_demo, ("дефект_шорсткість", "рекомендація", None)))