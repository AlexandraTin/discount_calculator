import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("discount_calculator.ui", self)

        self.discounts = []
        self.current_image_path = ""
        self.history = []

        self.calc_btn.clicked.connect(self.calculate_discount)
        self.add_discount_btn.clicked.connect(self.add_discount)
        self.clear_discount_btn.clicked.connect(self.clear_discounts)
        self.load_image_btn.clicked.connect(self.load_image)
        self.clear_image_btn.clicked.connect(self.clear_image)
        self.save_btn.clicked.connect(self.save_record)

        self.refresh_btn.clicked.connect(self.refresh_history)
        self.clear_history_btn.clicked.connect(self.clear_history)
        self.export_btn.clicked.connect(self.export_csv)

        self.statusBar().showMessage("Готов к работе")

    def calculate_discount(self):
        try:
            price = self.price_input.value()
            discount = self.discount_input.value()

            if price <= 0:
                QMessageBox.warning(self, "Ошибка", "Цена должна быть больше 0")
                return

            if self.discounts:
                final_price = price
                for d in self.discounts:
                    final_price *= (1 - d / 100)
            else:
                final_price = price * (1 - discount / 100)

            saved = price - final_price
            self.final_price_label.setText(f"{final_price:.2f} ₽")
            self.saved_label.setText(f"{saved:.2f} ₽")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Что-то пошло не так:\n{e}")

    def add_discount(self):
        discount = self.discount_input.value()
        if discount > 0:
            self.discounts.append(discount)
            self.discount_list.addItem(f"{discount}%")
            self.discount_input.setValue(0)

    def clear_discounts(self):
        self.discounts.clear()
        self.discount_list.clear()

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото", "", "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(
                    150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation
                ))
                self.image_label.setScaledContents(True)
                self.current_image_path = file_path
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение")

    def clear_image(self):
        self.image_label.clear()
        self.image_label.setText("Нет фото")
        self.current_image_path = ""

    def save_record(self):
        try:
            price = self.price_input.value()
            if self.discounts:
                discount_str = " + ".join([f"{d}%" for d in self.discounts])
            else:
                discount_str = f"{self.discount_input.value()}%"
            
            final_price = float(self.final_price_label.text().replace(" ₽", ""))
            saved = float(self.saved_label.text().replace(" ₽", ""))

            if final_price == 0 and saved == 0:
                QMessageBox.warning(self, "Ошибка", "Сначала выполните расчёт!")
                return

            record = {
                "price": price,
                "discount": discount_str,
                "final_price": final_price,
                "saved": saved
            }
            self.history.append(record)
            QMessageBox.information(self, "Сохранено", f"Расчёт сохранён!\nВсего записей: {len(self.history)}")
            self.statusBar().showMessage(f"Сохранено! Всего записей: {len(self.history)}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")

    def refresh_history(self):
        if self.history:
            QMessageBox.information(self, "История", f"В истории {len(self.history)} записей.")
        else:
            QMessageBox.information(self, "История", "История пока пуста.")
        self.statusBar().showMessage(f"Записей в истории: {len(self.history)}")

    def clear_history(self):
        if not self.history:
            QMessageBox.information(self, "Информация", "История уже пуста.")
            return
        reply = QMessageBox.question(
            self, "Подтверждение", "Очистить всю историю?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.history.clear()
            self.statusBar().showMessage("История очищена")

    def export_csv(self):
        QMessageBox.information(self, "Экспорт")
        self.statusBar().showMessage("Экспорт CSV ")

    def closeEvent(self, event):
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
