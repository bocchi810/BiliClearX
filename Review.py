import urwid

status_text = "按 q 退出\t"
content_text = "这是待审核内容"

status_bar = urwid.Text(status_text, align='center')
content_area = urwid.Text(content_text, align='center')

def on_comply(button):
    update_content("合规")

def on_skip(button):
    update_content("跳过")

def on_report(button):
    update_content("举报")

def update_status(new_status):
    global status_bar
    status_bar.set_text(f"按 q 退出\t{new_status}")

def update_content(new_content):
    global content_area
    content_area.set_text(new_content)

comply_button = urwid.Button("合规(c)", on_comply)
skip_button = urwid.Button("跳过(s)", on_skip)
report_button = urwid.Button("举报(r)", on_report)

# 定义每个按钮的样式
palette = [
    ('header', 'white', 'dark blue'),
    ('footer', 'white', 'dark red'),
    ('comply_button', 'white',  "", "","", "#55a7ff"),
    ('skip_button', 'white',  "", "","", "g38"),
    ('report_button', 'white',  "", "","black", "#a2e0ff"),
]



comply_button = urwid.AttrMap(comply_button, 'comply_button')
skip_button = urwid.AttrMap(skip_button, 'skip_button')
report_button = urwid.AttrMap(report_button, 'report_button')

comply_button = urwid.Padding(comply_button, width=('relative', 100), align='center')
skip_button = urwid.Padding(skip_button, width=('relative', 100), align='center')
report_button = urwid.Padding(report_button, width=('relative', 100), align='center')

button_list = [comply_button, skip_button, report_button]

button_column = urwid.Columns(button_list, dividechars=1)

layout = urwid.Frame(
    body=urwid.Filler(content_area, 'middle'),
    header=urwid.AttrMap(status_bar, 'header'),
    footer=urwid.AttrMap(button_column, 'footer')
)

def handle_input(key):
    if isinstance(key, tuple):
        key = key[0]
    key = key.lower()
    if key == 'q':
        raise urwid.ExitMainLoop()
    elif key == 'c':
        on_comply(comply_button)
    elif key == 's':
        on_skip(skip_button)
    elif key == 'r':
        on_report(report_button)

screen = urwid.display.raw.Screen()
screen.set_terminal_properties(colors=256)
loop = urwid.MainLoop(layout, palette, unhandled_input=handle_input, screen=screen)
loop.run()