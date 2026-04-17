**Tato dokumentace byla vytvořena jako záznam vývoje projektu 3D Card Preview. Cílem je poskytnout přehled o funkcích, technické architektuře a postupu prací. Texty jsou průběžně kontrolovány, aby byla zajištěna jejich přesnost a profesionální úroveň.
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
26.03.2026
Nové a změněné funkce
Přidána podpora importu vlastních textur (obrázků) pro přední i zadní stranu karty.
Uživatel může importovat obrázek z disku a aplikovat jej na kartu.
Po importu obrázku se automaticky nastaví odpovídající textury pro vykreslování.
Přidána podpora pro různé materiálové efekty (Matte, Glossy, Metallic, Scratched, Grainy, Frosted).
Uživatel může přepínat materiály v menu.
Každý materiál má vlastní texturu a parametry pro vykreslování.
Zlepšena stabilita a kompatibilita s různými verzemi OpenGL a ovladačů.
Opraveny chyby související s texturami a vykreslováním.
Zlepšena správa OpenGL kontextu a textur.
29.03.2026
Nové a změněné funkce
Přidána vizuální podpora pro 3D Embossing (plastické písmo) a textové ohraničení (Borders).
Embossing simuluje vyvýšený povrch pomocí stínování a odlesků.
Borders přidávají kontrastní obrys kolem textu pro lepší čitelnost.
Implementovány přísné fyzické hranice pro textové vrstvy.
Text již nelze přesunout mimo plochu karty – program automaticky hlídá okraje podle rozměru textu.
Výrazně kompaktnější a přehlednější sidebar pro správu vrstev.
Sloučení ovládacích prvků do menšího počtu řádků pro lepší přehlednost bez nutnosti scrollování.
Odstraněny nepotřebné posuvníky a prvky pro čistší vzhled aplikace.
28.03.2026
Nové a změněné funkce
Opraven problém s textovými vrstvami, které se nezobrazovaly na zadní straně karty.
**Hurá tohle byla moje osina v zadku už skoro týden ted na něco zábavnějšího :D
03.04.2026
Nové a změněné funkce
Přidána volba kvality embossingu už v úvodním StartMenuDialog (Normal / Realistic / Super Realistic)
Implementován pokročilý "Super Realistic" režim embossingu s reálnou 3D extruzí textu (vrstvené quady + vlastní maskovací textura)
Textury všech prvků (včetně textu) se nyní pečou do jedné fused texture pro každou stranu karty → lepší reakce na osvětlení a materiály
Fyzické embossing objekty (is_physical) se nyní správně chovají na obou stranách (raised na front, indented na back)
Kompletně přepracovaný systém materiálů s realistickými specular a shininess hodnotami pro každý typ (Matte → Frosted)
Přidána podpora pro "physical" embossed layers (tlačítko + Add Embossed Layer) s výchozí stříbrnou barvou
Vylepšená detekce a omezení pohybu textových vrstev (nelze je vytáhnout mimo kartu)
Kompaktnější a přehlednější TextObjectWidget – všechny ovládací prvky sloučeny do 1–2 řádků (Std/Emboss, Border, Color, Font)
Přidána validace textu (pouze ASCII znaky)
**Vlastní embossing (Custom Embossing) je technicky možný, avšak z důvodu vyšší náročnosti na výrobu není standardně zahrnut. Klienti mohou v případě zájmu kontaktovat výrobce přímo pro individuální konzultaci.
Výrazně vylepšené vykreslování emboss efektů v závislosti na zvolené kvalitě
Celkové vylepšení UI/UX sidebaru a dark theme konzistence
Malé optimalizace a úklid kódu

04.04.2026
Nové a změněné funkce
Kompletní katalog čipů podle webu levne-karty.cz (LF, HF, NFC, UHF a kontaktní čipy).
Přidána vizualizace vnitřní antény (X-ray look) pro bezkontaktní karty:
- LF (125 kHz): kruhová cívka.
- HF/NFC (13.56 MHz): obdélníková cívka po obvodu.
- UHF (900 MHz): dipólová anténa ve středu karty.
Rozšířen sidebar o kategorizovaný výběr čipů pro lepší přehlednost.
Vylepšené vykreslování kontaktních plošek pro čipy SLE4442 a Atmel/FM4442.
Stříbrné a zlaté varianty pro standardní ISO kontaktní čipy.
**Aktualizace dokumentace pro dnešní přehled funkcí.
5.04.2026
**Doplněn výběr čipových karet a jejich vizualizace.

07.04.2026
Nové a změněné funkce
Přidána podpora pro magnetické proužky (Magstripe) v konfiguraci karty.
Možnost volby mezi HiCo (černý, vysoká koercivita) a LoCo (hnědý, nízká koercivita) proužkem.
Realistické vykreslování na zadní straně karty s metalickým odleskem:
- Implementovány diagonální světelné přechody (shine effect) simulující odraz světla od magnetických částic.
- Přidána jemná mikrotextura pro autentičtější vzhled materiálu.
- Umístění odpovídá standardu ISO 7811 (šířka 12.7 mm, horní okraj 2.92 mm).
Rozšířen sidebar o sekci "Magnetic Stripe" pro rychlou změnu typu proužku.

08.04.2026
Nové a změněné funkce
Kompletní rework interakce s 3D modelem a textovými vrstvami pro profesionální "CAD-like" feel.
Implementován 3D Picking Systém:
- Uživatel může nyní kliknutím (LMB) přímo na libovolnou textovou vrstvu na kartě tuto vrstvu vybrat.
- Systém používá souřadnicovou projekci (gluProject) a automaticky detekuje viditelnou stranu karty.
- Přidán vizuální highlight (modré čárkované ohraničení) pro aktuálně vybraný objekt.
Vylepšená fyzika rotace (Inertia Engine):
- Přidána setrvačnost (momentum) – při rychlém "švihnutí" myší se karta dál plynule otáčí a plynule zastavuje (friction decay 0.96).
- Rotace se okamžitě "chytí" a zastaví při dalším kliknutí pro přesné polohování vrstev.
- Optimalizována citlivost rotace na hodnotu 0.15 pro lepší kontrolu.
Přidán Navigation HUD (Minimap):
- Panel v pravém horním rohu pro bleskovou navigaci mezi standardními pohledy.
- Obsahuje 6 presetů (Center, Top 45°, Bottom -45°) pro přední i zadní stranu.
- Implementována hladká filmová interpolace (Lerp) při přechodu mezi kamerovými pohledy.
- HUD je stylován jako semi-transparentní overlay nekolidující s hlavním zobrazením.
Integrovaný systém grafických vrstev (Graphics & Codes):
- Přidána podpora pro import externích grafik (QR kódy, čárové kódy, loga).
- Specializovaná tlačítka pro import QR kódů (čtvercový poměr) a čárových kódů (obdélníkový poměr) s přednastaveným škálováním.
- Grafiky jsou plně interaktivní, lze je přesouvat a vybírat pomocí 3D Pickingu stejně jako textové vrstvy.
- Odstraněn systém generování placeholderů ve prospěch importu reálných podkladů.

11.04.2026
Nové a změněné funkce
Kompletní redesign navigačního panelu na styl AutoCAD ViewCube:
- Původní seznam tlačítek nahrazen interaktivní maticí pohledů v pravém horním rohu.
- Podpora pro přímou navigaci na stěny (Face), hrany (Edges) a rohy (Corners - Isometrické pohledy).
- Přidán přepínač stran (Front/Back) integrovaný přímo v HUD panelu.
- Vylepšený vizuální styl s poloprůhledným pozadím a barevným zvýrazněním aktivních prvků.
- Zachována plynulá animace kamery při přepínání mezi pohledy.
14.04.2026
- Implementace klávesových zkratek pro správu vrstev:
    - Přidána podpora pro klávesy Delete a Backspace.
    - Uživatel může nyní okamžitě odstranit vybranou textovou nebo grafickou vrstvu přímo v 3D náhledu.
    **Díky implementaci klávesových zkratek byla zjednodušena správa vrstev – vybrané objekty lze nyní mazat přímo v 3D pohledu bez nutnosti vyhledávání v sidebaru.



16.04.2026
Opravy a technická stabilizace (Code Fixes)
- Opraveny chyby, které způsobovaly pád aplikace při interakci s grafickými vrstvami.
- Implementována chybějící metoda set_card_type(), která nyní korektně zajišťuje dynamickou změnu rozměrů karty během běhu bez nutnosti restartu.
- Opraveno škálování grafických objektů (loga, QR kódy) při pečení do textur – nyní se zobrazují ve správném poměru stran nezávisle na rozlišení textury.
- Opraveno seskupení tlačítek v navigačním HUD panelu (ViewCube) – oprava indexování v mřížce (Grid Layout).
- Přidáno ukládání aktuálního typu karty do instance GLWidgetu pro lepší konzistenci při správě projektů.

Technické detaily a architektura
Ukládání projektů probíhá pomocí formátu JSON, kde jsou serializovány veškeré parametry karty (barva, materiál, čip). Textové a grafické vrstvy mají vlastní metody `to_dict()`, přičemž importované obrázky jsou pro zachování integrity projektu převáděny na Base64 řetězce a ukládány přímo do JSONu. Pro efektivní práci s datovými poli a matematické výpočty je využíván `numpy`, zatímco modul `base64` slouží k hladké integraci externích grafických podkladů do uložených projektů. Tato kombinace technologií umožňuje vysoký výkon při 3D náhledu a zároveň snadnou přenositelnost uložených návrhů.

