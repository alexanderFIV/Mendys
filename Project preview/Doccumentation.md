**This was written by AI I only fix the thiings I do not like personally tho I am not sure If this dommuntetion is supposed to be uniformed or if  a more of a datum based input is preffered/wanted. For the time being I am will use the latter.
16.03.2026 
3D Card Preview
Popis a cíl projektu

Aplikace slouží k jednoduchému 3D náhledu plastových karet různých standardních rozměrů (např. CR80, CR79, CR100). Program umožňuje uživateli zvolit typ karty a režim okna před spuštěním náhledu. Cílem projektu je vytvořit jednoduchý nástroj pro vizuální kontrolu velikosti a tvaru karty v prostoru pomocí 3D grafiky.

Funkcionalita programu
Aplikace obsahuje startovací dialog, ve kterém si uživatel zvolí režim okna (windowed, fullscreen nebo borderless).
Uživatel si také vybere typ karty ze seznamu dostupných rozměrů.
Po potvrzení volby se otevře hlavní okno s 3D náhledem karty.
3D model karty je vykreslen pomocí OpenGL.
Karta má zaoblené rohy, které jsou generovány pomocí matematických funkcí (sin, cos).
Uživatel může kartu otáčet pomocí pohybu myši.
Pomocí kolečka myši lze přibližovat nebo oddalovat kameru.
Nově byl přidán postranní panel (sidebar) s možností změny typu karty za běhu aplikace.
Uživatel může program ukončit klávesou ESC.

Technická část
Program je napsán v jazyce Python.
Grafické rozhraní je vytvořeno pomocí knihovny PySide6.
3D vykreslování zajišťuje knihovna OpenGL.
OpenGL je integrováno do aplikace pomocí widgetu QOpenGLWidget.
Perspektivní projekce kamery je nastavena funkcí gluPerspective.
Model karty je vytvořen pomocí polygonů a čtyřúhelníků (GL_POLYGON, GL_QUADS).
Zaoblené rohy jsou vytvořeny výpočtem bodů kruhového oblouku.
Program obsahuje základní interakci s uživatelem pomocí myši (rotace objektu a zoom kamery).
Nově byla přidána metoda set_card_type(), která umožňuje dynamickou změnu rozměrů karty.
Sidebar obsahuje QComboBox pro výběr typu karty a je stylován pomocí CSS (setStyleSheet). Změna hodnoty v comboboxu je napojena na funkci on_card_type_changed(), která aktualizuje OpenGL scénu. Přidána obsluha klávesnice (keyPressEvent) pro zavření aplikace klávesou ESC.

Struktura programu
StartMenuDialog – dialogové okno pro výběr režimu okna a typu karty.
GLWidget – OpenGL widget zodpovědný za vykreslování 3D modelu karty.
MainWindow – hlavní okno aplikace obsahující OpenGL widget.
Hlavní část programu inicializuje aplikaci, zobrazí dialog a po potvrzení otevře hlavní okno.
Sidebar – nová komponenta umožňující změnu typu karty během běhu programu.
18.03.2026
Nové a změněné funkce
Přidána podpora více textových objektů (text layers) na kartě.
Vytvořena třída TextObject pro ukládání textu, pozice, barvy a strany (front/back).
Možnost přidávat nové texty během běhu aplikace.
Texty lze přesouvat myší přímo na kartě (drag & drop).
Přidána detekce kliknutí na text (screen_rect pro interakci).
Text lze zobrazit na přední i zadní straně karty.
Automatická viditelnost textu podle natočení karty.
Přidána možnost změny barvy textu pomocí QColorDialog.
Přidána možnost mazání jednotlivých textových vrstev.

Přidán sidebar s pokročilým UI pro správu textů.
Vytvořena komponenta TextObjectWidget pro editaci textu (obsah, strana, barva, smazání).
Přidán scrollovací seznam textových vrstev (QScrollArea).

Přidána změna barvy karty (barevná paleta + vlastní výběr).
Vytvořena komponenta ColorSwatch pro výběr barvy.
Přidána podpora vlastního výběru barvy přes dialog.

Vylepšené vykreslování:
- přidáno OpenGL osvětlení (GL_LIGHTING)
- přidány normály pro správné stínování
- hladké stínování (GL_SMOOTH)
- multisampling a anti-aliasing

Přidán override paintEvent pro kombinaci OpenGL + QPainter (vykreslení textu nad 3D scénou).

Zvýšen počet kroků pro zaoblení rohů (hladší křivky).
Změněn výchozí úhel kamery pro lepší vizuální prezentaci.
Upravena citlivost zoomu a pohybu.

Přidán tmavý vzhled aplikace (dark theme pomocí stylesheetu).
Upraven sidebar pro lepší UX a přehlednost.