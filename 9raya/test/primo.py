from PyQt5 import uic, QtWidgets
import sys

class PrimogemApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("primo.ui", self)  # Load your .ui file
        self.sendBtn.clicked.connect(self.deliver)

    def deliver(self):
        name = self.nameInput.text().strip()
        player_id = self.idInput.text().strip()
        region = self.regionBox.currentText()
        gems = self.gemsInput.value()

        if not name or not player_id:
            QtWidgets.QMessageBox.warning(self, "Error", "Please fill in Name and ID!")
            return

        QtWidgets.QMessageBox.information(
            self, "Delivery Success",
            f"{gems} Primogems delivered to ID {player_id} in {region}! ✨"
        )

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = PrimogemApp()
    window.show()
    sys.exit(app.exec_())
