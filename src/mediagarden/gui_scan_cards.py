from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel


# TODO: использовать эти карточки

class ScanTaskDeletedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        lbl_title = QLabel('Удалён с диска')
        layout.addWidget(lbl_title)

        self.lbl_existed_path = QLabel()
        layout.addWidget(self.lbl_existed_path)

        btn_delete = QPushButton('Удалить из базы')
        layout.addWidget(btn_delete)


class ScanTaskDuplicateWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        lbl_title = QLabel('Дубликат')
        layout.addWidget(lbl_title)

        self.lbl_inserted_path = QLabel()
        layout.addWidget(self.lbl_existed_path)

        btn_delete_from_disk = QPushButton('Удалить')
        lbl_on_disk = QLabel('Есть на диске')
        layout_inserted = QHBoxLayout()
        layout_inserted.addWidget(btn_delete_from_disk)
        layout_inserted.addWidget(lbl_on_disk)
        layout.addLayout(layout_inserted)

        self.lbl_existed_path = QLabel()
        layout.addWidget(self.lbl_existed_path)

        btn_delete = QPushButton('Удалить')
        lbl_on_both = QLabel('Есть на диске и в базе')
        layout_existed = QHBoxLayout()
        layout_existed.addWidget(btn_delete)
        layout_existed.addWidget(lbl_on_both)
        layout.addLayout(layout_existed)


class ScanTaskMovedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel('Перемещён')
        layout.addWidget(lbl_title)

        self.lbl_existed_path = QLabel()
        layout.addWidget(self.lbl_existed_path)

        self.lbl_inserted_path = QLabel()
        layout.addWidget(self.lbl_existed_path)

        btn_cancel = QPushButton('Отменить')
        btn_cancel.setDisabled(True)  # TODO: реализовать функционал и удалить эту строку
        btn_accept = QPushButton('Подтвердить')
        btn_accept.setDisabled(True)  # TODO: реализовать функционал и удалить эту строку
        layout_btns = QHBoxLayout()
        layout_btns.addWidget(btn_cancel)
        layout_btns.addWidget(btn_accept)
        layout.addLayout(layout_btns)


class ScanTaskNewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        lbl_title = QLabel('Новый')
        layout.addWidget(lbl_title)

        self.lbl_inserted_path = QLabel()
        layout.addWidget(self.lbl_inserted_path)

        btn_delete = QPushButton('Удалить')
        layout.addWidget(btn_delete)


class ScanTaskUntouchedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        lbl_title = QLabel('Неизменён')
        layout.addWidget(lbl_title)

        self.lbl_existed_path = QLabel()
        layout.addWidget(self.lbl_existed_path)


class ScanTaskItem(QWidget):
    pass
