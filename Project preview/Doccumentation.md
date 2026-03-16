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
Technická část
Program je napsán v jazyce Python.
Grafické rozhraní je vytvořeno pomocí knihovny PySide6.
3D vykreslování zajišťuje knihovna OpenGL.
OpenGL je integrováno do aplikace pomocí widgetu QOpenGLWidget.
Perspektivní projekce kamery je nastavena funkcí gluPerspective.
Model karty je vytvořen pomocí polygonů a čtyřúhelníků (GL_POLYGON, GL_QUADS).
Zaoblené rohy jsou vytvořeny výpočtem bodů kruhového oblouku.
Program obsahuje základní interakci s uživatelem pomocí myši (rotace objektu a zoom kamery).
Struktura programu
StartMenuDialog – dialogové okno pro výběr režimu okna a typu karty.
GLWidget – OpenGL widget zodpovědný za vykreslování 3D modelu karty.
MainWindow – hlavní okno aplikace obsahující OpenGL widget.
Hlavní část programu inicializuje aplikaci, zobrazí dialog a po potvrzení otevře hlavní okno.