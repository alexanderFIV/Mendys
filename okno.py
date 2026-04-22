from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout # Importuje potřebné třídy pro GUI a rozvržení
import sys # Importuje systémový modul pro argumenty a ukončení aplikace

app = QApplication(sys.argv) # Vytvoří hlavní instanci aplikace (nutné pro každou Qt aplikaci)

window = QWidget() # Vytvoří základní okno (prázdný kontejner)
window.setWindowTitle("Jednoduché Okno") # Nastaví titulek v záhlaví okna
window.resize(300, 100) # Nastaví počáteční velikost okna (šířka 300, výška 100 pixelů)

layout = QVBoxLayout() # Vytvoří vertikální rozvržení (prvky se budou řadit pod sebe)
label = QLabel("Mendy's Project") # Vytvoří textový popisek s daným textem
layout.addWidget(label) # Přidá tento popisek do připraveného rozvržení

window.setLayout(layout) # Nastaví rozvržení jako hlavní obsah našeho okna
window.show() # Zobrazí okno na obrazovce

sys.exit(app.exec()) # Spustí smyčku událostí aplikace a zajistí správné ukončení při zavření
