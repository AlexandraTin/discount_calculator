import sys
import sqlite3
import csv
import logging
from datetime import datetime
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._setup_db()
        self._bind_signals()
        self.load_history()
        logger.info("Приложение запущено")

    def _setup_ui(self):
        uic.loadUi("discount_calculator.ui", self)
        self.discounts = []
        self.current_image_path = ""
        self.statusBar().showMessage("Готов к работе")

    def _setup_db(self):
        self.conn = sqlite3.connect("discounts.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                price REAL NOT NULL,
                discount TEXT NOT NULL,
                final_price REAL NOT NULL,
                saved REAL NOT NULL,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
        logger.info("База данных инициализирована")

    def _bind_signals(self):
        self.calc_btn.clicked.connect(self.calculate_discount)
        self.add_discount_btn.clicked.connect(self.add_discount)
        self.clear_discount_btn.clicked.connect(self.clear_discounts)
        self.load_image_btn.clicked.connect(self.load_image)
        self.clear_image_btn.clicked.connect(self.clear_image)
        self.save_btn.clicked.connect(self.save_record)
        self.refresh_btn.clicked.connect(self.load_history)
        self.export_btn.clicked.connect(self.export_csv)
        self.clear_history_btn.clicked.connect(self.clear_history)

    def save_to_db(self, price, discount_str, final_price, saved, image_path):
        self.cursor.execute("""
            INSERT INTO history (price, discount, final_price, saved, image_path)
            VALUES (?, ?, ?, ?, ?)
        """, (price, discount_str, final_price, saved, image_path))
        self.conn.commit()

    def load_history(self):
        self.cursor.execute("SELECT * FROM history ORDER BY created_at DESC")
        rows = self.cursor.fetchall()
        self.history_table.setRowCount(0)
        for row in rows:
            row_position = self.history_table.rowCount()
            self.history_table.insertRow(row_position)
            self.history_table.setItem(row_position, 0, QTableWidgetItem(str(row[0])))
            self.history_table.setItem(row_position, 1, QTableWidgetItem(f"{row[1]:.2f} ₽"))
            self.history_table.setItem(row_position, 2, QTableWidgetItem(row[2]))
            self.history_table.setItem(row_position, 3, QTableWidgetItem(f"{row[3]:.2f} ₽"))
            self.history_table.setItem(row_position, 4, QTableWidgetItem(f"{row[4]:.2f} ₽"))
            self.history_table.setItem(row_position, 5, QTableWidgetItem(row[6]))
        logger.info(f"Загружено записей: {len(rows)}")

    def calculate_discount(self):
        try:
            price = self.price_input.value()
            discount = self.discount_input.value()

            if price <= 0:
                QMessageBox.warning(self, "Ошибка", "Цена должна быть больше 0")
                logger.warning("Попытка расчёта с ценой <= 0")
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
            logger.info(f"Расчёт выполнен: цена={price}, скидка={discount}%, итог={final_price:.2f}")

        except Exception as e:
            logger.error(f"Ошибка расчёта: {e}")
            QMessageBox.critical(self, "Ошибка", f"Что-то пошло не так:\n{e}")

    def add_discount(self):
        discount = self.discount_input.value()
        if discount > 0:
            self.discounts.append(discount)
            self.discount_list.addItem(f"{discount}%")
            self.discount_input.setValue(0)
            logger.info(f"Добавлена скидка: {discount}%")

    def clear_discounts(self):
        self.discounts.clear()
        self.discount_list.clear()
        logger.info("Список скидок очищен")

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото", "", "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            try:
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    self.image_label.setPixmap(pixmap.scaled(
                        150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    ))
                    self.image_label.setScaledContents(True)
                    self.current_image_path = file_path
                    logger.info(f"Фото загружено: {file_path}")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение")
            except Exception as e:
                logger.error(f"Ошибка загрузки фото: {e}")

    def clear_image(self):
        self.image_label.clear()
        self.image_label.setText("Нет фото")
        self.current_image_path = ""
        logger.info("Фото удалено")

    def save_record(self):
        try:
            price = self.price_input.value()
            
            if self.discounts:
                discount_str = " + ".join([f"{d}%" for d in self.discounts])
            else:
                discount_str = f"{self.discount_input.value()}%"
            
            final_price = float(self.final_price_label.text().replace(" ₽", ""))
            saved = float(self.saved_label.text().replace(" ₽", ""))
            image_path = self.current_image_path

            if final_price == 0 and saved == 0:
                QMessageBox.warning(self, "Ошибка", "Сначала выполните расчёт")
                return

            self.save_to_db(price, discount_str, final_price, saved, image_path)
            self.load_history()
            QMessageBox.information(self, "Сохранено", "Расчёт сохранён в историю")
            self.statusBar().showMessage("Запись сохранена")
            logger.info(f"Запись сохранена: цена={price}, скидка={discount_str}")

        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")

    def export_csv(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM history")
            count = self.cursor.fetchone()[0]
            if count == 0:
                QMessageBox.warning(self, "Экспорт", "История пуста")
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить CSV", "history.csv", "CSV файлы (*.csv)"
            )
            if not file_path:
                return

            self.cursor.execute("SELECT * FROM history ORDER BY created_at DESC")
            rows = self.cursor.fetchall()

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["ID", "Цена", "Скидка", "Итог", "Экономия", "Дата"])
                for row in rows:
                    writer.writerow([
                        row[0], row[1], row[2], 
                        f"{row[3]:.2f}", f"{row[4]:.2f}", row[6]
                    ])

            QMessageBox.information(self, "Экспорт", f"Данные сохранены в {file_path}")
            self.statusBar().showMessage("Экспорт выполнен")
            logger.info(f"Экспорт CSV: {file_path}")

        except Exception as e:
            logger.error(f"Ошибка экспорта: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать:\n{e}")

    def clear_history(self):
        reply = QMessageBox.question(
            self, "Подтверждение", "Очистить всю историю?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.cursor.execute("DELETE FROM history")
            self.conn.commit()
            self.load_history()
            self.statusBar().showMessage("История очищена")
            logger.info("История очищена")

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Подтверждение выхода",
            "Вы уверены, что хотите выйти?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.conn.close()
            logger.info("Приложение завершено")
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
