import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QFormLayout, QMessageBox, QGridLayout,
    QHBoxLayout
)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QPixmap, QDrag
from pong import PongGame
import random
from database import Database


class PuzzlePiece(QLabel):
    def __init__(self, pixmap, correct_position, parent=None):
        super().__init__(parent)
        self.setPixmap(pixmap)
        self.correct_position = correct_position
        self.setFixedSize(pixmap.size())
        self.setAcceptDrops(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            drag.setMimeData(mime_data)
            drag.setPixmap(self.pixmap())
            drag.setHotSpot(event.position().toPoint())
            drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        source = event.source()
        if isinstance(source, PuzzlePiece):
            source_parent = source.parent()
            target_parent = self.parent()
            source_parent.layout().indexOf(source)
            target_parent.layout().indexOf(self)

            source_parent.layout().replaceWidget(source, self)
            target_parent.layout().replaceWidget(self, source)
            event.acceptProposedAction()
            self.window().check_completion()


class CaptchaWidget(QWidget):
    def __init__(self, image_paths, max_piece_size=150):
        super().__init__()
        self.max_piece_size = max_piece_size
        self.correct_positions = list(range(4))
        self.is_completed = False
        self.initUI(image_paths)

    def initUI(self, image_paths):
        self.setWindowTitle('Проверка капчи')
        self.setFixedSize(700, 500)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("Соберите картинку правильно:")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.setSpacing(15)

        horizontal_container = QWidget()
        horizontal_layout = QHBoxLayout(horizontal_container)
        horizontal_layout.setSpacing(20)

        self.source_widget = QWidget()
        self.source_layout = QGridLayout(self.source_widget)
        self.source_layout.setSpacing(10)

        # Исправление строки 65 - разбиваем вычисление размера
        target_size = self.max_piece_size * 2 + 10
        self.target_widget = QWidget()
        self.target_widget.setFixedSize(target_size, target_size)
        self.target_layout = QGridLayout(self.target_widget)
        self.target_layout.setSpacing(5)

        self.pieces = []
        for i, path in enumerate(image_paths):
            pixmap = QPixmap(path)
            if pixmap.isNull():
                print(f"Ошибка загрузки: {path}")
                pixmap = QPixmap(self.max_piece_size, self.max_piece_size)
                pixmap.fill(Qt.GlobalColor.gray)
            else:
                pixmap = pixmap.scaled(
                    self.max_piece_size,
                    self.max_piece_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

            piece = PuzzlePiece(pixmap, i, self)
            piece.setFixedSize(self.max_piece_size, self.max_piece_size)
            self.pieces.append(piece)

        random.shuffle(self.pieces)
        for i, piece in enumerate(self.pieces):
            self.source_layout.addWidget(
                piece, i, 0, alignment=Qt.AlignmentFlag.AlignCenter
            )

        self.target_labels = []
        for i in range(4):
            placeholder = QLabel(self)
            placeholder.setFixedSize(self.max_piece_size, self.max_piece_size)
            placeholder.setStyleSheet(
                "border: 2px dashed gray; background-color: #f0f0f0;"
            )
            placeholder.setAcceptDrops(True)
            placeholder.dropEvent = (
                lambda event, idx=i: self.handle_target_drop(event, idx)
            )
            placeholder.dragEnterEvent = (
                lambda event: event.acceptProposedAction()
            )
            self.target_labels.append(placeholder)
            row, col = i // 2, i % 2
            self.target_layout.addWidget(
                placeholder, row, col, alignment=Qt.AlignmentFlag.AlignCenter
            )

        horizontal_layout.addWidget(self.source_widget)
        horizontal_layout.addWidget(self.target_widget)

        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)

        self.reset_button = QPushButton("Сброс")
        self.reset_button.setFixedWidth(120)
        self.reset_button.clicked.connect(self.reset_puzzle)

        buttons_layout.addWidget(self.reset_button)

        container_layout.addWidget(horizontal_container)
        container_layout.addWidget(
            buttons_widget, alignment=Qt.AlignmentFlag.AlignCenter
        )

        main_layout.addWidget(container_widget)

    def handle_target_drop(self, event, target_index: int):
        source = event.source()
        if isinstance(source, PuzzlePiece):
            target_label = self.target_labels[target_index]

            if target_label.pixmap() and not target_label.pixmap().isNull():
                for piece in self.pieces:
                    if (piece.pixmap().toImage() ==
                            target_label.pixmap().toImage()):
                        piece.show()
                        self.source_layout.addWidget(
                            piece, self.source_layout.count(), 0,
                            alignment=Qt.AlignmentFlag.AlignCenter
                        )
                        break

            target_label.setPixmap(source.pixmap())
            source.hide()
            event.acceptProposedAction()

            self.check_completion()

    def all_cells_filled(self):
        for label in self.target_labels:
            if label.pixmap() is None or label.pixmap().isNull():
                return False
        return True

    def check_completion(self):
        if not self.all_cells_filled():
            return

        current_order = []
        for i, label in enumerate(self.target_labels):
            for piece in self.pieces:
                if piece.pixmap().toImage() == label.pixmap().toImage():
                    current_order.append(piece.correct_position)
                    break

        self.is_completed = (current_order == self.correct_positions)

        if self.is_completed:
            QMessageBox.information(self, "Успех", "Капча пройдена успешно!")
            self.close()
            if hasattr(self, 'on_success'):
                self.on_success()
        else:
            QMessageBox.warning(
                self, "Ошибка",
                "Капча решена неправильно! Попробуйте еще раз."
            )
            self.reset_puzzle()

    def reset_puzzle(self):
        for label in self.target_labels:
            label.clear()
            label.setStyleSheet(
                "border: 2px dashed gray; background-color: #f0f0f0;"
            )

        for piece in self.pieces:
            piece.show()

        for i in reversed(range(self.source_layout.count())):
            self.source_layout.itemAt(i).widget().setParent(None)

        random.shuffle(self.pieces)
        for i, piece in enumerate(self.pieces):
            self.source_layout.addWidget(
                piece, i, 0, alignment=Qt.AlignmentFlag.AlignCenter
            )

        self.is_completed = False


class GameSelectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Выбор игры")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        title_label = QLabel("Выберите игру")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; margin: 20px;"
        )
        layout.addWidget(title_label)

        pong_button = QPushButton("Pong Game")
        pong_button.setFixedHeight(50)
        pong_button.clicked.connect(self.start_pong)
        layout.addWidget(pong_button)

        game_of_life_button = QPushButton("Game of Life (скоро)")
        game_of_life_button.setFixedHeight(50)
        game_of_life_button.setEnabled(False)
        game_of_life_button.clicked.connect(self.show_coming_soon)
        layout.addWidget(game_of_life_button)

        polish_button = QPushButton("Польская нотация (скоро)")
        polish_button.setFixedHeight(50)
        polish_button.setEnabled(False)
        polish_button.clicked.connect(self.show_coming_soon)
        layout.addWidget(polish_button)

        self.setLayout(layout)

    def start_pong(self):
        self.hide()
        self.game_window = PongGame()
        self.game_window.show()

    def show_coming_soon(self):
        QMessageBox.information(
            self, "В разработке", "Эта игра скоро будет доступна!"
        )


class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.max_attempts = 3
        self.current_email = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Вход и Регистрация")
        self.resize(400, 350)

        self.layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.login_tab = QWidget()
        self.login_layout = QFormLayout()

        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Введите ваш email")

        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Введите ваш пароль")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.handle_login)

        self.login_layout.addRow("Email:", self.login_email)
        self.login_layout.addRow("Пароль:", self.login_password)
        self.login_layout.addRow(self.login_button)

        self.login_tab.setLayout(self.login_layout)

        self.register_tab = QWidget()
        self.register_layout = QFormLayout()

        self.reg_name = QLineEdit()
        self.reg_name.setPlaceholderText("Введите ваше имя")

        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("Введите ваш email")

        self.reg_password = QLineEdit()
        self.reg_password.setPlaceholderText(
            "Придумайте пароль (минимум 6 символов)"
        )
        self.reg_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.register_button = QPushButton("Зарегистрироваться")
        self.register_button.clicked.connect(self.handle_register)

        self.register_layout.addRow("Имя:", self.reg_name)
        self.register_layout.addRow("Email:", self.reg_email)
        self.register_layout.addRow("Пароль:", self.reg_password)
        self.register_layout.addRow(self.register_button)

        self.register_tab.setLayout(self.register_layout)

        self.tabs.addTab(self.login_tab, "Вход")
        self.tabs.addTab(self.register_tab, "Регистрация")

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    def handle_login(self):
        email = self.login_email.text().strip()
        password = self.login_password.text().strip()

        if not email or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        if not self.db.user_exists(email):
            QMessageBox.warning(
                self, "Ошибка", "Пользователь с таким email не найден!"
            )
            return

        login_attempts = self.db.get_login_attempts(email)

        if login_attempts >= self.max_attempts:
            QMessageBox.warning(
                self, "Превышено количество попыток",
                "Вы превысили количество попыток входа."
                " Требуется проверка капчи."
            )
            self.current_email = email
            self.show_captcha()
            return

        user = self.db.check_user(email, password)

        if user:
            self.db.update_login_attempts(email, True)
            QMessageBox.information(
                self, "Успех", f"Вход выполнен успешно, {user[1]}!"
            )
            self.open_game_selection()
        else:
            self.db.update_login_attempts(email, False)
            remaining_attempts = self.max_attempts - (login_attempts + 1)

            if remaining_attempts > 0:
                QMessageBox.warning(
                    self, "Ошибка входа",
                    f"Неверный пароль. Осталось попыток: {remaining_attempts}"
                )
            else:
                QMessageBox.warning(
                    self, "Превышено количество попыток",
                    "Вы превысили количество попыток входа."
                    " Требуется проверка капчи."
                )
                self.current_email = email
                self.show_captcha()

    def show_captcha(self):
        image_paths = ['1.png', '2.png', '3.png', '4.png']
        self.captcha_window = CaptchaWidget(image_paths)
        self.captcha_window.on_success = self.on_captcha_success
        self.captcha_window.show()

    def on_captcha_success(self):
        if self.current_email:
            self.db.update_login_attempts(self.current_email, True)
            QMessageBox.information(
                self, "Доступ восстановлен",
                "Капча пройдена успешно! Вы можете продолжить попытки входа."
            )
            self.current_email = None

    def handle_register(self):
        name = self.reg_name.text().strip()
        email = self.reg_email.text().strip()
        password = self.reg_password.text().strip()

        if not name or not email or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        if len(password) < 6:
            QMessageBox.warning(
                self, "Ошибка", "Пароль должен содержать минимум 6 символов!"
            )
            return

        if not self.is_valid_email(email):
            QMessageBox.warning(
                self, "Ошибка", "Введите корректный email адрес!"
            )
            return

        if self.db.register_user(name, email, password):
            QMessageBox.information(
                self, "Успех", "Регистрация выполнена успешно!"
            )
            self.reg_name.clear()
            self.reg_email.clear()
            self.reg_password.clear()
            self.tabs.setCurrentIndex(0)
            self.open_game_selection()
        else:
            QMessageBox.warning(
                self, "Ошибка",
                "Пользователь с таким email уже существует!"
            )

    def is_valid_email(self, email):
        return '@' in email and '.' in email and len(email) > 5

    def open_game_selection(self):
        self.hide()
        self.game_selection_window = GameSelectionWindow()
        self.game_selection_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AuthWindow()
    window.show()
    sys.exit(app.exec())
C:\Users\top20\pyqt\main.py