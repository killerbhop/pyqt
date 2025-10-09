import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QFont, QKeyEvent


class PongGame(QWidget):
    score_updated = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pong Game - PyQt6")
        self.setFixedSize(800, 600)

        self.paddle_width = 15
        self.paddle_height = 100
        self.ball_size = 15
        self.paddle_speed = 8
        self.ball_speed_x = 5
        self.ball_speed_y = 5
        self.max_ball_speed = 15

        self.player1_y = 250
        self.player2_y = 250

        self.ball_x = 400
        self.ball_y = 300

        self.score1 = 0
        self.score2 = 0

        self.keys_pressed = {
            Qt.Key.Key_W: False,
            Qt.Key.Key_S: False,
            Qt.Key.Key_Up: False,
            Qt.Key.Key_Down: False,
        }

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(16)  # ~60 FPS

        self.font = QFont("Arial", 24, QFont.Weight.Bold)

        self.background_color = QColor(0, 0, 0)
        self.flash_timer = QTimer()
        self.flash_timer.setSingleShot(True)
        self.flash_timer.timeout.connect(self.reset_background)

        self.init_ui()

    def init_ui(self):
        pass

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key in self.keys_pressed:
            self.keys_pressed[key] = True

        if key == Qt.Key.Key_R and (self.score1 >= 5 or self.score2 >= 5):
            self.score1 = 0
            self.score2 = 0
            self.reset_ball()
            self.ball_speed_x = 5
            self.ball_speed_y = 5

        event.accept()

    def keyReleaseEvent(self, event: QKeyEvent):
        key = event.key()
        if key in self.keys_pressed:
            self.keys_pressed[key] = False
        event.accept()

    def update_game(self):
        if self.score1 >= 5 or self.score2 >= 5:
            return

        if self.keys_pressed[Qt.Key.Key_W] and self.player1_y > 0:
            self.player1_y -= self.paddle_speed
        if (
            self.keys_pressed[Qt.Key.Key_S]
            and self.player1_y < self.height() - self.paddle_height
        ):
            self.player1_y += self.paddle_speed
        if self.keys_pressed[Qt.Key.Key_Up] and self.player2_y > 0:
            self.player2_y -= self.paddle_speed
        if (
            self.keys_pressed[Qt.Key.Key_Down]
            and self.player2_y < self.height() - self.paddle_height
        ):
            self.player2_y += self.paddle_speed

        self.ball_x += self.ball_speed_x
        self.ball_y += self.ball_speed_y

        if self.ball_y <= 0 or self.ball_y >= self.height() - self.ball_size:
            self.ball_speed_y = -self.ball_speed_y

        paddle1_rect = QRectF(
            20, self.player1_y, self.paddle_width, self.paddle_height
        )
        paddle2_rect = QRectF(
            self.width() - 20 - self.paddle_width,
            self.player2_y,
            self.paddle_width,
            self.paddle_height,
        )
        ball_rect = QRectF(
            self.ball_x, self.ball_y, self.ball_size, self.ball_size
        )

        if ball_rect.intersects(paddle1_rect) and self.ball_speed_x < 0:
            self.ball_speed_x = -self.ball_speed_x
            self.ball_speed_x = min(
                self.ball_speed_x * 1.1, self.max_ball_speed
            )
            speed_y_abs = min(
                abs(self.ball_speed_y * 1.1), self.max_ball_speed
            )
            self.ball_speed_y = speed_y_abs * (
                1 if self.ball_speed_y > 0 else -1
            )

        if ball_rect.intersects(paddle2_rect) and self.ball_speed_x > 0:
            self.ball_speed_x = -self.ball_speed_x
            self.ball_speed_x = max(
                self.ball_speed_x * 1.1, -self.max_ball_speed
            )
            speed_y_abs = min(
                abs(self.ball_speed_y * 1.1), self.max_ball_speed
            )
            self.ball_speed_y = speed_y_abs * (
                1 if self.ball_speed_y > 0 else -1
            )

        if self.ball_x < 0:
            self.score2 += 1
            self.flash_background()
            self.reset_ball()
        elif self.ball_x > self.width():
            self.score1 += 1
            self.flash_background()
            self.reset_ball()

        self.update()

    def reset_ball(self):
        self.ball_x = self.width() / 2 - self.ball_size / 2
        self.ball_y = self.height() / 2 - self.ball_size / 2

        self.ball_speed_x = 5 if self.ball_speed_x > 0 else -5
        self.ball_speed_y = 5 if self.ball_speed_y > 0 else -5

        self.ball_speed_y += random.uniform(-1, 1)

    def flash_background(self):
        self.background_color = QColor(100, 100, 100)
        self.flash_timer.start(200)

    def reset_background(self):
        self.background_color = QColor(0, 0, 0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), self.background_color)

        painter.setPen(QColor(255, 255, 255))
        for i in range(0, self.height(), 20):
            painter.drawRect(int(self.width() / 2 - 1), i, 2, 10)

        painter.fillRect(
            20,
            int(self.player1_y),
            self.paddle_width,
            self.paddle_height,
            QColor(255, 255, 255),
        )
        painter.fillRect(
            self.width() - 20 - self.paddle_width,
            int(self.player2_y),
            self.paddle_width,
            self.paddle_height,
            QColor(255, 255, 255),
        )
        painter.fillRect(
            int(self.ball_x),
            int(self.ball_y),
            self.ball_size,
            self.ball_size,
            QColor(255, 255, 255),
        )

        painter.setFont(self.font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(int(self.width() / 4), 50, str(self.score1))
        painter.drawText(int(3 * self.width() / 4), 50, str(self.score2))

        if self.score1 >= 5 or self.score2 >= 5:
            winner = "Игрок 1" if self.score1 >= 5 else "Игрок 2"
            painter.drawText(
                int(self.width() / 2 - 100),
                int(self.height() / 2),
                f"{winner} победил!",
            )
            painter.drawText(
                int(self.width() / 2 - 150),
                int(self.height() / 2 + 40),
                "Нажмите R для рестарта",
            )


def main():
    app = QApplication(sys.argv)

    game = PongGame()
    game.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
