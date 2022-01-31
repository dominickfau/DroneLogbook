from PyQt5.QtWidgets import QLineEdit


def clean_text_input(widget: QLineEdit):
    widget.setText(widget.text().strip())