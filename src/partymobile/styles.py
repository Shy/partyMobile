from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER, LEFT


class Heading:
    style = Pack(direction=ROW, text_align=CENTER, padding=5, font_size=32)


class SubBox:
    style = Pack(flex=1, direction=COLUMN)


class label:
    style = Pack(text_align=CENTER)


class question_label:
    style = Pack(text_align=LEFT, padding=5)


class question:
    style = Pack(text_align=LEFT, padding=5)


class number_label:
    style = Pack(text_align=CENTER, font_size=32)
