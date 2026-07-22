#!/usr/bin/env python3
"""Reclassify alimentos_usfq.json with priority-based keyword matching."""

import json
import re
from collections import Counter
from pathlib import Path

JSON_PATH = Path(__file__).parent / "alimentos_usfq.json"


def normalize_accents(text):
    """Remove accent marks for accent-insensitive matching."""
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def word_match(keyword, text):
    pattern = r'\b' + re.escape(keyword) + r'(?![\wáéíóúñ])'
    if bool(re.search(pattern, text, re.IGNORECASE)):
        return True
    return bool(re.search(pattern, normalize_accents(text), re.IGNORECASE))


def check_keyword(kw, text_es, text_en):
    if kw.startswith("w:"):
        real_kw = kw[2:]
        return word_match(real_kw, text_es) or word_match(real_kw, text_en)
    else:
        if kw in text_es or kw in text_en:
            return True
        return normalize_accents(kw) in normalize_accents(text_es) or normalize_accents(kw) in normalize_accents(text_en)


CATEGORIES = [
    (
        "Huevos",
        ["huevo"],
        ["egg"],
    ),
    (
        "Lácteos y derivados",
        [
            "leche", "queso", "yogurt", "yogur", "helado",
            "manjar", "natilla", "kumis",
            "w:crema", "w:suero",
        ],
        [
            "milk", "cheese", "yogurt", "sour cream", "ice cream", "whey",
        ],
    ),
    (
        "Carnes y aves",
        [
            "carne", "chuleta", "lomo", "costilla", "bistec", "filete",
            "jamón", "tocino", "panceta", "salchicha", "chorizo",
            "longaniza", "embutido", "cecina", "trompa", "rabo",
            "machín", "cuy",
            "vaca", "vacuno", "ternera", "buey",
            "pollo", "gallina",
            "cerdo", "chancho", "puerco", "cochino",
            "borrego", "cordero", "oveja",
            "conejo", "pavo",
            "hígado", "corazón", "riñón", "panza", "mondongo",
            "tripas", "molleja", "lengua", "ubre",
            "w:ave ", "w:aves",
            "w:res ",
            "chontacuro", "gusano",
        ],
        [
            "beef", "veal", "lamb", "mutton", "pork", "chicken", "turkey",
            "rabbit", "heart", "liver", "kidney", "tripe", "stomach",
            "meat", "steak", "chop", "bacon", "ham",
            "sausage", "frankfurter", "offal", "tongue", "gizzard",
        ],
    ),
    (
        "Pescados y mariscos",
        [
            "pescado", "atún", "salmón", "camarón", "langostino",
            "almeja", "sardina", "anchoa", "cangrejo", "pulpo",
            "calamar", "ostra", "mejillón", "corvina", "mojarra",
            "trucha", "bacalao", "merluza", "robalo", "jurel",
            "bagre", "tilapia", "cazón", "pez", "marisco",
            "concha", "ostión", "congrio", "mero",
            "bonito", "caballa", "pargo", "sierra", "toyo",
            "w:caracol", "caracoles", "pampanito",
        ],
        [
            "fish", "tuna", "salmon", "shrimp", "prawn", "clam", "sardine",
            "anchovy", "crab", "octopus", "squid", "oyster", "mussel",
            "cod", "trout", "herring", "sole", "flounder", "seafood",
            "lobster", "snapper", "mackerel", "shark",
        ],
    ),
    (
        "Grasas y aceites",
        ["aceite", "margarina", "grasa"],
        ["oil", "margarine", "fat"],
    ),
    (
        "Cereales y derivados",
        [
            "arroz", "quinoa", "quinua", "trigo",
            "espagueti", "macarrón", "fideo",
            "harina", "tortilla",
            "maíz", "maiz", "cebada", "centeno", "milo",
            "sorgo", "amaranto", "tapioca",
            "cereal", "granola", "trigo sarraceno",
            "cuscús", "muesli", "cornflake", "hojuelas",
            "arepa", "choclo", "elote", "maicena", "fécula", "almidón",
            "torta", "queque", "bizcocho",
            "w:avena", "w:avenas",
            "w:pasta",
            "w:cous",
            "w:pan ",
            "w:pan,",
            "w:galleta",
        ],
        [
            "rice", "oat", "oats", "wheat", "pasta", "spaghetti", "macaroni",
            "noodle", "flour", "tortilla", "corn", "barley", "rye",
            "cereal", "granola", "bran", "buckwheat", "couscous", "muesli",
            "cornflake", "cracker", "toast", "biscuit", "cake", "muffin",
            "bagel", "croissant", "pancake", "waffle", "pastry",
        ],
    ),
    (
        "Legumbres y derivados",
        [
            "frijol", "fréjol", "poroto", "arveja", "chícharo", "guisante",
            "lenteja", "haba", "garbanzo", "legumbre", "soya", "soja",
            "lupino", "almorta", "guandul", "chocho",
        ],
        [
            "bean", "pea", "lentil", "chickpea", "broadbean", "fava",
            "legume", "soybean", "lupini", "pigeon pea",
        ],
    ),
    (
        "Frutos secos y semillas",
        [
            "w:nuez", "w:almendra", "maní", "w:cashew", "cacahuete",
            "girasol", "w:chía", "linaza", "ajonjolí", "sesamo",
            "pistacho", "avellana", "piñón", "marañón", "tahini",
            "pepita", "w:semillas", "hinojo",
        ],
        [
            "walnut", "almond", "peanut", "cashew", "sunflower",
            "chia", "linseed", "sesame", "pistachio", "hazelnut",
            "pine nut", "macadamia", "pecan",
        ],
    ),
    (
        "Azúcares y dulces",
        [
            "azúcar", "mermelada",
            "arrope", "panela", "alfajor", "caramelo",
            "jalea", "bocadillo", "golosina", "confite",
            "turrón", "mazapán", "espumilla", "penela",
            "edulzante", "endulzante",
        ],
        [
            "sugar", "honey", "chocolate", "candy", "marmalade", "syrup",
            "fudge", "toffee", "jam", "preserves", "confection",
            "marshmallow", "sweetener", "sweetner",
        ],
    ),
    (
        "Plátanos y tubérculos",
        [
            "plátano", "platano", "papa", "yuca", "mandioca", "camote",
            "boniato", "achira", "oca", "mashua", "ulluco",
        ],
        [
            "plantain", "potato", "cassava", "yam", "taro", "sweet potato",
        ],
    ),
    (
        "Frutas",
        [
            "manzana", "banana", "naranja", "pera", "uva", "fresa",
            "frutilla", "mango", "papaya", "piña", "aguacate", "coco",
            "limón", "sandía", "melón", "ciruela", "guayaba", "guanábana",
            "guanabana", "maracuyá", "lulo", "naranjilla",
            "tomate de árbol", "mora", "zarzamora",
            "cas", "curuba", "pitahaya", "granadilla", "mandarina",
            "lima", "durazno", "cereza", "higo", "membrillo",
            "cherimoya", "chirimoya",
            "tumbo", "taxo", "babaco", "feijoa", "kiwi", "pomelo",
            "toronja", "cidra", "limón sutil", "limón verde",
            "arañón", "grosella", "aronia", "arándano",
            "frambuesa", "mora azul",
            "datil", "hacó", "jocote", "mamey", "mangostino",
            "noni", "tamarindo", "aceituna", "oliva",
            "uvilla", "arazá", "capulí", "capulin", "guaba", "níspero",
            "cushin", "paterna", "pasas",
        ],
        [
            "apple", "banana", "orange", "pear", "grape", "strawberry",
            "mango", "papaya", "pineapple", "avocado", "coconut", "lemon",
            "watermelon", "melon", "plum", "gooseberry", "guava",
            "passion fruit", "lulo", "naranjilla", "tree tomato",
            "blackberry", "raspberry", "berry", "fig", "peach",
            "cherry", "apricot", "pomegranate", "persimmon", "kiwi",
            "date", "lime", "citrus", "fruit", "soursop", "loquat",
            "golden", "jinicuil", "araza",
        ],
    ),
    (
        "Verduras y hortalizas",
        [
            "tomate", "cebolla", "cebollín", "lechuga", "zanahoria",
            "repollo", "acelga", "espinaca", "brócoli", "brocoli",
            "rúcula", "rucula",
            "pimiento", "pepino", "apio",
            "coliflor", "remolacha", "calabacín", "zapallo", "calabaza",
            "champiñón", "hongo", "seta", "espárrago", "esparrago",
            "palmito", "berenjena", "nabo", "rábano",
            "verdura", "hortaliza", "ensalada",
            "w:chile", "w:ají", "w:aji", "w:ajo",
            "w:col", "alcachofa", "bruselas",
            "sambo", "chilacayote", "chiverre", "achogcha",
            "alfalfa", "paico",
        ],
        [
            "tomato", "onion", "lettuce", "carrot", "cabbage", "chard",
            "spinach", "broccoli", "arugula", "pepper", "cucumber",
            "celery", "eggplant", "cauliflower", "beet", "zucchini",
            "pumpkin", "squash", "mushroom", "asparagus", "garlic",
            "vegetable", "salad", "artichoke", "gourd",
        ],
    ),
    (
        "Condimentos y especias",
        [
            "pimienta", "comino", "orégano", "oregano", "cilantro",
            "especias", "salsa", "vinagre", "mostaza", "ketchup",
            "mayonesa", "aderezo", "sazonador", "sazon",
            "w:laurel", "w:perejil", "w:albahaca", "w:tomillo", "w:romero",
            "curry", "cúrcuma", "turmeric", "paprika", "achiote",
            "consomé", "caldo", "recado",
            "w:sal ",
            "w:sal,",
        ],
        [
            "salt", "pepper", "cumin", "oregano", "cilantro", "spice",
            "sauce", "vinegar", "mustard", "ketchup", "mayonnaise",
            "dressing", "seasoning", "bay", "parsley", "basil",
            "thyme", "rosemary", "curry", "turmeric", "paprika",
            "annatto", "bouillon", "broth",
        ],
    ),
    (
        "Bebidas",
        [
            "gaseosa", "jugo", "bebida", "cerveza", "vino",
            "té", "refresco", "licor", "ron", "pisco",
            "aguardiente", "cóctel", "batido", "licuado",
            "smoothie", "colada",
            "w:café", "w:cafe",
            "w:agua",
        ],
        [
            "soda", "juice", "beverage", "beer", "wine", "coffee",
            "water", "drink", "liquor", "rum", "brandy", "whiskey",
            "vodka", "cocktail", "smoothie", "milkshake", "tea",
        ],
    ),
    (
        "Snacks y dulces",
        [
            "papa frita", "papita frita", "palomitas",
            "cracker", "snack", "bocaditos", "aros de cebolla", "chifles",
            "tostado", "nachos", "w:pretzel",
            "maíz canguil", "w:chip",
        ],
        [
            "chip", "popcorn", "cookie", "cracker", "snack", "pretzel",
            "nacho",
        ],
    ),
    (
        "Preparados y comidas rápidas",
        [
            "pizza", "hamburguesa", "sándwich", "sandwich", "empanada",
            "ceviche", "encurtido",
            "lasaña", "ravioli", "taco", "burrito",
            "albóndiga", "albondiga", "guiso", "estofado",
            "cazuela", "seco de",
            "tamal", "mote",
        ],
        [
            "pizza", "hamburger", "sandwich", "empanada", "lasagna",
            "ravioli", "taco", "burrito", "stew", "soup", "casserole",
        ],
    ),
]


def classify(nombre, nombre_ingles):
    text_es = nombre.lower()
    text_en = nombre_ingles.lower()

    for cat_name, kw_es, kw_en in CATEGORIES:
        for kw in kw_es:
            if check_keyword(kw, text_es, text_en):
                return cat_name
        for kw in kw_en:
            if check_keyword(kw, text_es, text_en):
                return cat_name

    return "Otros"


def main():
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    before = Counter(item.get("categoria", "") for item in data)

    for item in data:
        nombre = item.get("nombre", "")
        nombre_en = item.get("nombre_ingles", "")
        item["categoria"] = classify(nombre, nombre_en)

    after = Counter(item.get("categoria", "") for item in data)

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("=== BEFORE ===")
    for cat, count in sorted(before.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    print(f"  TOTAL: {sum(before.values())}")

    print("\n=== AFTER ===")
    for cat, count in sorted(after.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    print(f"  TOTAL: {sum(after.values())}")

    print(f"\nReclassified {len(data)} items. File saved to {JSON_PATH}")


if __name__ == "__main__":
    main()
