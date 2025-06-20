from random import choice, randint
import string


def random_word():
    n = randint(1, 10) + randint(0, 5)
    return "".join([choice(string.printable) for _ in range(n)])


def random_word_list():
    n = randint(1, 10) + randint(0, 5)
    return [random_word() for _ in range(n)]


def random_text(m):
    n = randint(1, m)
    return " ".join([random_word() for _ in range(n)])


def random_property():
    if randint(1, 10) < 5:
        return random_single_property()
    n = randint(1, 4)
    return [random_single_property() for _ in range(n)]


def random_single_property():
    return choice([random_word(), random_object()])


def random_object():
    return choice([{random_word(): random_word()}, {random_word(): random_word_list()}])
