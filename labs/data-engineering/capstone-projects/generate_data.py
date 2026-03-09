"""
Generate all data files for the Capstone Projects module.
Road accident data, multi-format restaurant data, and art gallery catalogues.
"""

import sqlite3
import csv
import json
import random
import os
import math
import re
from datetime import datetime, timedelta

random.seed(42)

BASE_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(BASE_DIR, exist_ok=True)

# ============================================================
# 1. road_accidents_sample.csv (~3000 rows)
#    Based on DfT STATS19 structure
# ============================================================

ROAD_TYPES = [
    "Single carriageway", "Single carriageway", "Single carriageway",
    "Dual carriageway", "Dual carriageway",
    "Roundabout",
    "One way street",
    "Slip road",
    "Motorway",
]

SPEED_LIMITS = [20, 30, 30, 30, 40, 40, 50, 60, 60, 70, 70]

WEATHER_CONDITIONS = [
    "Fine no high winds", "Fine no high winds", "Fine no high winds",
    "Fine no high winds", "Fine no high winds",
    "Raining no high winds", "Raining no high winds",
    "Raining with high winds",
    "Snowing no high winds",
    "Fog or mist",
    "Other",
    "Unknown",
]

LIGHT_CONDITIONS = [
    "Daylight", "Daylight", "Daylight", "Daylight",
    "Darkness - lights lit", "Darkness - lights lit",
    "Darkness - lights unlit",
    "Darkness - no lighting",
    "Darkness - lighting unknown",
]

ROAD_SURFACES = [
    "Dry", "Dry", "Dry", "Dry",
    "Wet or damp", "Wet or damp",
    "Snow", "Frost or ice",
    "Flood over 3cm deep",
]

SEVERITY = ["Slight", "Slight", "Slight", "Slight", "Slight",
            "Slight", "Slight", "Serious", "Serious", "Fatal"]

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday",
                "Friday", "Saturday", "Sunday"]

LOCAL_AUTHORITIES = [
    "Westminster", "Camden", "Islington", "Tower Hamlets", "Hackney",
    "Southwark", "Lambeth", "Wandsworth", "Greenwich", "Lewisham",
    "Birmingham", "Manchester", "Leeds", "Liverpool", "Bristol",
    "Sheffield", "Newcastle upon Tyne", "Nottingham", "Leicester",
    "Coventry", "Bradford", "Cardiff", "Edinburgh", "Glasgow",
    "Swansea", "Oxford", "Cambridge", "York", "Bath",
    "Plymouth", "Southampton", "Portsmouth", "Brighton and Hove",
    "Reading", "Exeter", "Norwich", "Ipswich", "Cheltenham",
    "Wolverhampton", "Derby", "Sunderland",
]

URBAN_RURAL = ["Urban", "Urban", "Urban", "Rural", "Rural"]

# UK lat/lon bounding box (approximate)
UK_LAT_MIN, UK_LAT_MAX = 50.0, 55.8
UK_LON_MIN, UK_LON_MAX = -5.7, 1.8

accidents = []
for i in range(3000):
    acc_id = f"ACC{i+1:05d}"

    # Generate date in 2023
    day_offset = random.randint(0, 364)
    acc_date = datetime(2023, 1, 1) + timedelta(days=day_offset)
    date_str = acc_date.strftime("%Y-%m-%d")

    # Time — weighted towards rush hours
    r = random.random()
    if r < 0.15:
        hour = random.randint(7, 9)   # morning rush
    elif r < 0.30:
        hour = random.randint(16, 18)  # evening rush
    elif r < 0.45:
        hour = random.randint(12, 14)  # lunch
    else:
        hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    time_str = f"{hour:02d}:{minute:02d}"

    day_of_week = DAYS_OF_WEEK[acc_date.weekday()]

    road_type = random.choice(ROAD_TYPES)
    speed_limit = random.choice(SPEED_LIMITS)
    weather = random.choice(WEATHER_CONDITIONS)
    light = random.choice(LIGHT_CONDITIONS)
    surface = random.choice(ROAD_SURFACES)

    num_vehicles = random.choices([1, 2, 3, 4, 5],
                                  weights=[15, 55, 20, 8, 2])[0]
    num_casualties = random.choices([1, 2, 3, 4, 5, 6],
                                    weights=[50, 25, 12, 7, 4, 2])[0]
    severity = random.choice(SEVERITY)

    lat = round(random.uniform(UK_LAT_MIN, UK_LAT_MAX), 6)
    lon = round(random.uniform(UK_LON_MIN, UK_LON_MAX), 6)

    authority = random.choice(LOCAL_AUTHORITIES)
    urban_rural = random.choice(URBAN_RURAL)

    row = {
        "accident_id": acc_id,
        "date": date_str,
        "time": time_str,
        "day_of_week": day_of_week,
        "road_type": road_type,
        "speed_limit": speed_limit,
        "weather_conditions": weather,
        "light_conditions": light,
        "road_surface": surface,
        "number_of_vehicles": num_vehicles,
        "number_of_casualties": num_casualties,
        "severity": severity,
        "latitude": lat,
        "longitude": lon,
        "local_authority": authority,
        "urban_rural": urban_rural,
    }

    # Introduce some messiness
    r = random.random()
    if r < 0.03:
        row["weather_conditions"] = ""
    elif r < 0.05:
        row["light_conditions"] = ""
    elif r < 0.07:
        row["speed_limit"] = ""
    elif r < 0.08:
        row["latitude"] = ""
        row["longitude"] = ""
    elif r < 0.10:
        row["road_surface"] = ""

    # Some inconsistent severity labels
    if random.random() < 0.02:
        row["severity"] = row["severity"].lower()
    if random.random() < 0.015:
        row["severity"] = row["severity"].upper()
    # Some inconsistent road types
    if random.random() < 0.02:
        row["road_type"] = row["road_type"].lower()

    # Occasional wrong date formats
    if random.random() < 0.02:
        row["date"] = acc_date.strftime("%d/%m/%Y")

    # Some negative speed limits (data entry error)
    if random.random() < 0.01:
        row["speed_limit"] = -abs(int(row["speed_limit"])) if row["speed_limit"] else ""

    accidents.append(row)

csv_path = os.path.join(BASE_DIR, "road_accidents_sample.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "accident_id", "date", "time", "day_of_week", "road_type",
        "speed_limit", "weather_conditions", "light_conditions",
        "road_surface", "number_of_vehicles", "number_of_casualties",
        "severity", "latitude", "longitude", "local_authority", "urban_rural",
    ])
    writer.writeheader()
    writer.writerows(accidents)

print(f"Generated {len(accidents)} rows in {csv_path}")


# ============================================================
# 2. restaurant_north.csv (~800 rows)
#    UK date format, GBP, traditional British pub grub
# ============================================================

NORTH_ITEMS = [
    ("Fish and Chips", 12.50),
    ("Pie and Mash", 11.00),
    ("Sunday Roast", 14.50),
    ("Bangers and Mash", 10.50),
    ("Shepherd's Pie", 10.00),
    ("Steak and Ale Pie", 13.50),
    ("Ploughman's Lunch", 9.50),
    ("Chips and Gravy", 5.50),
    ("Mushy Peas (side)", 2.50),
    ("Sticky Toffee Pudding", 6.50),
    ("Yorkshire Pudding Wrap", 8.50),
    ("Scampi and Chips", 11.50),
    ("Gammon and Eggs", 11.00),
    ("Black Pudding Starter", 6.00),
    ("Pint of Bitter", 4.80),
    ("Glass of House Wine", 5.50),
    ("Soft Drink", 2.50),
    ("Tea or Coffee", 2.80),
]

NORTH_SERVERS = ["Dave", "Sarah", "Mike", "Jenny", "Tom", "Lisa", "Paul", "Emma"]
PAYMENT_METHODS = ["cash", "card", "card", "card", "card", "contactless", "contactless"]

north_rows = []
order_id = 1
# Orders span 2024-01-01 to 2024-06-30
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 6, 30)
span_days = (end_date - start_date).days

for _ in range(800):
    oid = f"N-{order_id:04d}"
    order_id += 1

    order_date = start_date + timedelta(days=random.randint(0, span_days))
    date_str = order_date.strftime("%d/%m/%Y")

    item_name, base_price = random.choice(NORTH_ITEMS)
    # Small price variation
    unit_price = round(base_price + random.uniform(-0.50, 0.50), 2)
    quantity = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
    total = round(unit_price * quantity, 2)
    payment = random.choice(PAYMENT_METHODS)
    server = random.choice(NORTH_SERVERS)

    north_rows.append({
        "order_id": oid,
        "order_date": date_str,
        "item_name": item_name,
        "quantity": quantity,
        "unit_price": unit_price,
        "total": total,
        "payment_method": payment,
        "server_name": server,
    })

csv_path = os.path.join(BASE_DIR, "restaurant_north.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "order_id", "order_date", "item_name", "quantity",
        "unit_price", "total", "payment_method", "server_name",
    ])
    writer.writeheader()
    writer.writerows(north_rows)

print(f"Generated {len(north_rows)} rows in {csv_path}")


# ============================================================
# 3. restaurant_south.json (~600 orders)
#    ISO dates, nested items, GBP, upmarket Mediterranean
# ============================================================

SOUTH_ITEMS = [
    ("Grilled Sea Bass", 18.50),
    ("Lamb Kofta", 15.00),
    ("Halloumi Salad", 12.50),
    ("Moussaka", 14.00),
    ("Prawn Linguine", 16.50),
    ("Chicken Souvlaki", 13.50),
    ("Hummus and Flatbread", 7.50),
    ("Mezze Platter", 11.00),
    ("Baklava", 6.50),
    ("Tiramisu", 7.00),
    ("Espresso", 3.00),
    ("Fresh Lemonade", 4.00),
    ("Glass of Prosecco", 7.50),
    ("Bottle of House Red", 22.00),
    ("Feta and Watermelon Salad", 10.50),
    ("Chargrilled Aubergine", 9.50),
]

SOUTH_SERVERS = ["Maria", "Nikos", "Priya", "James", "Sofia", "Alex"]

south_orders = []
for i in range(600):
    oid = f"S-{i+1:04d}"
    order_dt = start_date + timedelta(
        days=random.randint(0, span_days),
        hours=random.randint(11, 22),
        minutes=random.choice([0, 15, 30, 45]),
    )
    timestamp = order_dt.strftime("%Y-%m-%dT%H:%M:%S")

    # 1-4 items per order
    num_items = random.choices([1, 2, 3, 4], weights=[20, 40, 30, 10])[0]
    items = []
    for _ in range(num_items):
        item_name, base_price = random.choice(SOUTH_ITEMS)
        qty = random.choices([1, 2], weights=[85, 15])[0]
        price = round(base_price + random.uniform(-1.0, 1.0), 2)
        items.append({"name": item_name, "qty": qty, "price": price})

    payment = random.choice(["card", "card", "card", "cash", "contactless"])
    server = random.choice(SOUTH_SERVERS)

    south_orders.append({
        "order_id": oid,
        "timestamp": timestamp,
        "items": items,
        "payment": payment,
        "server": server,
    })

json_path = os.path.join(BASE_DIR, "restaurant_south.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(south_orders, f, indent=2)

print(f"Generated {len(south_orders)} orders in {json_path}")


# ============================================================
# 4. restaurant_west.sqlite (~500 orders)
#    Mix of GBP/EUR, some duplicates, Welsh border gastropub
# ============================================================

WEST_ITEMS = [
    ("Welsh Rarebit", 9.50),
    ("Cawl (Lamb Broth)", 8.50),
    ("Bara Brith", 5.00),
    ("Leek and Stilton Soup", 7.50),
    ("Roast Lamb", 16.00),
    ("Confit Duck Leg", 17.50),
    ("Wild Mushroom Risotto", 13.00),
    ("Smoked Salmon Starter", 9.00),
    ("Bread and Butter Pudding", 6.50),
    ("Cheese Board", 10.50),
    ("Pint of Craft Ale", 5.50),
    ("Glass of Sauvignon Blanc", 6.50),
    ("Sparkling Water", 3.00),
    ("Pot of Tea", 3.50),
    ("Pan-Fried Trout", 15.50),
    ("Beetroot and Goat Cheese Salad", 11.00),
]

WEST_SERVERS = ["Rhys", "Carys", "Owen", "Ffion", "Gethin", "Nia"]

db_path = os.path.join(BASE_DIR, "restaurant_west.sqlite")
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.executescript("""
CREATE TABLE orders (
    order_id TEXT,
    date TEXT,
    total REAL,
    currency TEXT,
    payment_method TEXT
);

CREATE TABLE order_items (
    order_id TEXT,
    item_name TEXT,
    quantity INTEGER,
    price REAL
);
""")

west_order_ids = []
for i in range(500):
    oid = f"W-{i+1:04d}"
    west_order_ids.append(oid)

    order_date = start_date + timedelta(days=random.randint(0, span_days))

    # Mix date formats
    r = random.random()
    if r < 0.6:
        date_str = order_date.strftime("%Y-%m-%d")
    elif r < 0.85:
        date_str = order_date.strftime("%d/%m/%Y")
    else:
        date_str = order_date.strftime("%d-%m-%Y")

    # 1-4 items
    num_items = random.choices([1, 2, 3, 4], weights=[20, 40, 30, 10])[0]
    order_total = 0.0
    for _ in range(num_items):
        item_name, base_price = random.choice(WEST_ITEMS)
        qty = random.choices([1, 2], weights=[80, 20])[0]
        price = round(base_price + random.uniform(-0.50, 0.50), 2)
        order_total += price * qty
        cur.execute("INSERT INTO order_items VALUES (?, ?, ?, ?)",
                    (oid, item_name, qty, price))

    # 85% GBP, 15% EUR (border confusion)
    currency = "GBP" if random.random() < 0.85 else "EUR"
    payment = random.choice(["card", "card", "card", "cash", "contactless"])

    order_total = round(order_total, 2)
    cur.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?)",
                (oid, date_str, order_total, currency, payment))

# Insert some duplicates (about 25 duplicate orders)
for _ in range(25):
    dup_oid = random.choice(west_order_ids[:400])
    # Fetch original
    orig = cur.execute("SELECT * FROM orders WHERE order_id = ?",
                       (dup_oid,)).fetchone()
    if orig:
        cur.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orig)
        # Also duplicate order items
        items = cur.execute("SELECT * FROM order_items WHERE order_id = ?",
                            (dup_oid,)).fetchall()
        for item in items:
            cur.execute("INSERT INTO order_items VALUES (?, ?, ?, ?)", item)

conn.commit()

order_count = cur.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
item_count = cur.execute("SELECT COUNT(*) FROM order_items").fetchone()[0]
conn.close()

print(f"Generated {order_count} orders, {item_count} items in {db_path}")


# ============================================================
# 5. gallery_catalogues.json
#    ~30 exhibition/artist entries with rich searchable text
# ============================================================

gallery_entries = [
    {
        "id": "EXH-001",
        "type": "exhibition",
        "title": "Echoes of Light: Abstract Expressionism in Britain",
        "year": 2023,
        "text": (
            "Echoes of Light brings together forty works spanning six decades of abstract expressionism "
            "in the British Isles. The exhibition traces a lineage from the St Ives painters of the 1950s "
            "through the New British Painting movement of the 1980s to the present day. Central to the "
            "show is the tension between gestural spontaneity and deliberate composition, a dialogue that "
            "has defined abstract expressionism since its American origins yet takes on a distinctly "
            "different character when filtered through British sensibilities. Patrick Heron's luminous "
            "colour fields open the ground-floor galleries, their saturated pigments humming against "
            "whitewashed walls. The influence of the Cornish landscape is unmistakable in these works: "
            "the Atlantic light, the granite headlands, the restless movement of the sea. Upstairs, "
            "Sarah Chen's monumental canvases command an entire room. Chen, who studied under Terry "
            "Frost at the Royal Academy Schools, has developed a vocabulary of sweeping arcs and pooled "
            "pigment that simultaneously references landscape and the human body. Her 2019 triptych "
            "'Tide Memory' anchors the second gallery, its five-metre span capturing the cyclical pull "
            "of the ocean through layers of translucent acrylic. The middle galleries present work by "
            "younger artists who have absorbed the abstract expressionist tradition without being bound "
            "by it. Notable among these is James Okonkwo, whose practice merges West African textile "
            "patterns with the gestural mark-making of post-war abstraction. His piece 'Crossings' "
            "was shortlisted for the Turner Prize in 2022 and is shown here alongside preparatory "
            "studies that reveal his meticulous working process. The exhibition also features a room "
            "dedicated to sculptural responses to abstract expressionism. Rachel Lim's suspended steel "
            "forms catch and redistribute natural light, creating shadow paintings on the gallery floor "
            "that shift throughout the day. Her work draws on both minimalist sculpture and the colour "
            "theory that underpins abstract expressionist painting. A companion publication by Dr Eleanor "
            "Bright explores the contested relationship between American Abstract Expressionism and its "
            "British counterpart, arguing that the British tradition is characterised by a deeper "
            "connection to place and natural phenomena. The catalogue includes previously unpublished "
            "correspondence between Patrick Heron and Mark Rothko that sheds new light on the "
            "transatlantic exchange of ideas. Echoes of Light runs until March 2024 and is accompanied "
            "by a programme of artist talks, workshops, and guided tours."
        ),
    },
    {
        "id": "ART-001",
        "type": "artist_biography",
        "title": "Sarah Chen: A Retrospective",
        "text": (
            "Sarah Chen (born 1971, Hong Kong; based in London and St Ives) is one of the most "
            "significant abstract painters working in Britain today. After emigrating to the UK at the "
            "age of twelve, Chen studied Fine Art at Goldsmiths before completing her MA at the Royal "
            "Academy Schools under Terry Frost. Her early work drew heavily on Chinese ink painting "
            "traditions, but by the late 1990s she had begun to develop the large-scale gestural "
            "abstraction for which she is now known. Chen's practice is rooted in direct observation "
            "of the natural world, particularly the Cornish coastline where she maintains a studio "
            "overlooking Porthmeor Beach. She works on unstretched canvas laid flat on the floor, "
            "pouring and dragging acrylic paint in rhythmic, bodily movements that she describes as "
            "'painting with the whole self.' The resulting works often measure three to five metres "
            "across and are characterised by luminous, layered colour and a sense of expansive space. "
            "Major exhibitions include 'Tide Memory' at the Whitmore Gallery (2019), 'Between Two "
            "Shores' at the Tate St Ives (2020), and 'Horizon Line' at the Hayward Gallery (2022). "
            "Her work is held in the collections of the Tate, the Arts Council, the British Museum, "
            "and the Hong Kong Museum of Art. Chen was elected a Royal Academician in 2021 and received "
            "a CBE in the 2023 New Year Honours for services to art. She has spoken extensively about "
            "the experience of cultural duality in her work, describing her paintings as 'a conversation "
            "between two traditions, two landscapes, two ways of seeing.' Her collaboration with "
            "composer Thomas Ades on the multimedia installation 'Resonance' (2023) marked a new "
            "direction in her practice, integrating sound and projected light with her painted surfaces."
        ),
    },
    {
        "id": "EXH-002",
        "type": "exhibition",
        "title": "Terrain: New Landscape Photography",
        "year": 2023,
        "text": (
            "Terrain presents the work of eight photographers who are reimagining the tradition of "
            "British landscape photography for the twenty-first century. Moving beyond the picturesque "
            "conventions that have dominated the genre, these artists engage with the land as a site of "
            "ecological crisis, social history, and contested memory. The exhibition opens with Amara "
            "Osei's aerial studies of post-industrial landscapes in South Wales, shot from a drone "
            "fitted with infrared sensors. Her images reveal the invisible legacy of coal mining: "
            "thermal anomalies that mark the locations of buried shafts, contaminated waterways that "
            "glow an unearthly violet in false colour. The beauty of these images is inseparable from "
            "their documentary function, raising questions about the aestheticisation of environmental "
            "damage. In the adjacent gallery, David Park's long-exposure seascapes reduce the coastline "
            "of North Yorkshire to its essential elements: stone, water, light, and time. Park uses "
            "exposures of up to thirty minutes, smoothing the North Sea into a silvery plane that "
            "contrasts with the brutal solidity of the cliffs. His work sits in conversation with the "
            "Romantic sublime, but with a contemporary awareness of coastal erosion and rising sea "
            "levels. The central gallery is given over to Fatima Khalil's project 'Borderlands,' a "
            "three-year documentation of the landscapes along the English-Scottish border. Working "
            "exclusively with a large-format film camera, Khalil captures the empty moorlands and "
            "quiet valleys where centuries of conflict have left traces visible only to the attentive "
            "eye. Her accompanying texts draw on oral histories gathered from farming communities whose "
            "relationship with the land predates national boundaries. Other highlights include Tom "
            "Walsh's documentation of urban rewilding projects in East London, and Mei Lin's composite "
            "photographs that overlay historical maps onto contemporary landscapes, creating palimpsest "
            "images of changing land use over centuries. A programme of talks pairs each photographer "
            "with a scientist, historian, or writer, fostering dialogue between artistic and analytical "
            "ways of understanding the land."
        ),
    },
    {
        "id": "ART-002",
        "type": "artist_biography",
        "title": "James Okonkwo: Between Worlds",
        "text": (
            "James Okonkwo (born 1985, Lagos; based in London) works across painting, textile, and "
            "installation to explore the intersections of West African and European artistic traditions. "
            "He moved to the UK in 2003 to study at Central Saint Martins, where he initially focused "
            "on fashion textiles before turning to fine art. This training in pattern, repetition, and "
            "material culture continues to inform his practice. Okonkwo's paintings are large-scale "
            "works on raw linen that combine the gestural mark-making of post-war European abstraction "
            "with motifs drawn from Yoruba adire cloth. He mixes his own pigments from natural sources, "
            "including indigo, camwood, and laterite earth, connecting his materials to specific "
            "geographies and cultural practices. His 2022 piece 'Crossings' was shortlisted for the "
            "Turner Prize. The work consists of a seven-metre canvas divided into panels that reference "
            "both the Middle Passage and the artist's own experience of migration, rendered in deep "
            "indigo and burnt sienna. 'Crossings' is accompanied by a soundscape of field recordings "
            "from Lagos markets and London Underground stations. Recent solo exhibitions include "
            "'Thread Lines' at the Serpentine (2023) and 'Indigo Territories' at the Contemporary "
            "Art Museum, Lagos (2022). Group exhibitions include the 59th Venice Biennale and "
            "'Abstract Territories' at the Whitmore Gallery (2021). Okonkwo is also a visiting "
            "lecturer at the Royal College of Art, where he leads workshops on cross-cultural "
            "approaches to abstraction. His work is held in the collections of the Tate, the "
            "Smithsonian, and the Zeitz Museum of Contemporary Art Africa."
        ),
    },
    {
        "id": "EXH-003",
        "type": "exhibition",
        "title": "Material Worlds: Sculpture and Installation 2020-2023",
        "year": 2023,
        "text": (
            "Material Worlds surveys the vitality and diversity of contemporary sculpture and "
            "installation practice in Britain. The exhibition brings together fifteen artists whose "
            "work interrogates the physical, cultural, and political properties of materials, from "
            "reclaimed industrial steel to hand-foraged clay. The ground-floor galleries are dominated "
            "by Rachel Lim's 'Canopy,' a suspended installation of over two hundred polished steel "
            "leaves that rotate slowly in the gallery's air currents. Natural light reflects off "
            "their surfaces, projecting a constantly shifting pattern of light and shadow onto the "
            "floor below. Lim, who trained as an engineer before attending the Slade, brings a "
            "structural precision to her work that is complemented by an acute sensitivity to the "
            "behaviour of light. In the project space, Marcus Fletcher presents 'Erosion Studies,' "
            "a series of concrete casts taken from eroding coastal formations in Dorset. The casts "
            "are displayed alongside the moulds used to create them, drawing attention to the process "
            "of reproduction and the paradox of preserving something defined by its impermanence. "
            "Fletcher's work references both Land Art and the geological sciences, and he has "
            "collaborated with researchers at the British Geological Survey on a parallel project "
            "mapping rates of coastal change. The first-floor galleries feature Yuki Tanaka's "
            "ceramic installation 'Garden of Earthly Delights,' an immersive environment of over "
            "three hundred hand-built stoneware forms that range from delicate flowers to grotesque, "
            "surreal hybrid creatures. Tanaka draws on the traditions of Japanese ceramics, European "
            "porcelain figurines, and the Garden of Eden imagery of Hieronymus Bosch. The installation "
            "is lit by a programmed sequence of coloured spotlights that shift the mood from pastoral "
            "tranquillity to unsettling theatricality over the course of each hour. Other notable "
            "works include Priya Kapoor's woven steel tapestries, inspired by Mughal textile patterns "
            "and fabricated using industrial chain-link fencing, and Callum Murray's kinetic "
            "sculptures powered by wind and water, installed in the gallery's courtyard."
        ),
    },
    {
        "id": "ART-003",
        "type": "artist_biography",
        "title": "Rachel Lim: Light and Structure",
        "text": (
            "Rachel Lim (born 1979, Singapore; based in London) creates sculptures and installations "
            "that explore the interaction between light, form, and architectural space. Before pursuing "
            "art, Lim completed a degree in structural engineering at Imperial College London, an "
            "experience that profoundly shaped her understanding of materials and spatial relationships. "
            "She went on to study sculpture at the Slade School of Fine Art, graduating in 2008. "
            "Lim's work typically employs polished or brushed metals, primarily stainless steel and "
            "aluminium, which she manipulates into geometric and organic forms designed to catch, "
            "redirect, and fragment light. Her sculptures function as instruments for making light "
            "visible, casting complex shadow patterns that become integral parts of the work. She has "
            "described her practice as 'drawing with light in three dimensions.' Major commissions "
            "include 'Meridian' for the atrium of the Francis Crick Institute (2019), 'Solar Return' "
            "for the Singapore National Gallery (2020), and 'Canopy' for the Whitmore Gallery (2023). "
            "Her work has been exhibited at the Hayward Gallery, the Yorkshire Sculpture Park, the "
            "Venice Architecture Biennale, and the Sharjah Biennial. Lim was awarded the Jerwood "
            "Sculpture Prize in 2017 and was selected for the Fourth Plinth commission in 2024. "
            "She is a fellow of the Royal Society of Sculptors and sits on the advisory board of the "
            "Contemporary Art Society. In recent work, Lim has begun incorporating responsive "
            "technologies, embedding sensors in her sculptures so that they react to the movement "
            "and proximity of viewers, creating an evolving, participatory experience of light and form."
        ),
    },
    {
        "id": "EXH-004",
        "type": "exhibition",
        "title": "Code and Canvas: Digital Art in the Age of AI",
        "year": 2024,
        "text": (
            "Code and Canvas is the Whitmore Gallery's first major exhibition dedicated to digital "
            "and computational art. The show brings together works that use algorithms, machine "
            "learning, and generative processes as creative tools, raising urgent questions about "
            "authorship, creativity, and the role of human intention in art-making. The exhibition "
            "opens with a historical section tracing the lineage of computer art from its origins "
            "in the 1960s, featuring early plotter drawings by Harold Cohen and Vera Molnar alongside "
            "video synthesis works by Nam June Paik. This context is essential, the curators argue, "
            "for understanding the current moment not as a rupture but as the continuation of a "
            "decades-long conversation between artists and machines. The main galleries present "
            "contemporary works that engage directly with artificial intelligence. Helena Voss's "
            "installation 'Ghost Writer' uses a language model fine-tuned on the collected writings "
            "of Virginia Woolf to generate new prose in real time, projected onto the gallery walls "
            "in a continuous scroll. Voss has trained the model not to imitate Woolf but to respond "
            "to her, creating a speculative literary dialogue across time. The ethical dimensions of "
            "this practice, appropriation, consent, and the rights of the dead, are addressed in an "
            "accompanying essay by literary critic Maya Patel. Daniel Okoro's 'Latent Landscapes' "
            "series uses generative adversarial networks trained on satellite imagery to produce "
            "images of places that do not exist but could. These fictional topographies are printed "
            "at large scale on aluminium panels, their hyperreal surfaces both seductive and "
            "disquieting. Okoro describes the work as 'mapping the space between observation and "
            "hallucination.' The most immersive piece is 'Symbiosis' by collective FIELD, an "
            "interactive environment where visitors' movements are tracked and translated into "
            "evolving visual and sonic landscapes projected across all surfaces of a darkened room. "
            "The system learns from collective behaviour over the course of the exhibition, meaning "
            "the experience changes as more people interact with it."
        ),
    },
    {
        "id": "ART-004",
        "type": "artist_biography",
        "title": "Amara Osei: Unseen Landscapes",
        "text": (
            "Amara Osei (born 1990, Accra; based in Cardiff) is a photographer and filmmaker whose "
            "work investigates the intersection of landscape, technology, and environmental justice. "
            "She studied Documentary Photography at the University of South Wales before completing "
            "an MA in Environmental Humanities at the University of Bristol. This interdisciplinary "
            "training is evident in work that combines rigorous visual documentation with scientific "
            "data and community testimony. Osei's best-known project, 'Afterglow,' uses drone-mounted "
            "infrared and multispectral cameras to photograph post-industrial landscapes in South "
            "Wales, revealing environmental contamination invisible to the naked eye. The series has "
            "been exhibited at the National Museum Cardiff, the Barbican, and the Rencontres d'Arles "
            "photography festival. It was accompanied by a community engagement programme in which "
            "residents of former mining villages contributed oral histories that contextualise the "
            "images. Her subsequent project, 'Thermal Bodies,' applies similar imaging technology to "
            "urban heat mapping, documenting the unequal distribution of green space and shade in "
            "British cities. The work has been cited in parliamentary reports on environmental racism "
            "and urban planning. Osei is a recipient of the Deutsche Borse Photography Foundation "
            "Prize (2023) and was named in the British Journal of Photography's annual Ones to Watch "
            "list. She is currently developing a new project examining the landscapes of rare earth "
            "mineral extraction, tracing the material supply chains of the technologies used in her "
            "own photographic equipment."
        ),
    },
    {
        "id": "EXH-005",
        "type": "exhibition",
        "title": "Still Life, Still Living: Objects and Meaning",
        "year": 2022,
        "text": (
            "Still Life, Still Living revisits one of art's oldest genres through the lens of "
            "contemporary practice. The exhibition argues that still life painting, far from being "
            "a quaint tradition, remains a vital mode of addressing questions about consumer culture, "
            "mortality, ecological collapse, and the emotional lives of objects. The show opens with "
            "a small selection of seventeenth-century Dutch vanitas paintings on loan from the "
            "National Gallery, their meticulously rendered skulls, hourglasses, and rotting fruit "
            "establishing the thematic ground for what follows. In the adjacent gallery, Nadia "
            "Petrov's hyperrealist oil paintings of supermarket shelves update the vanitas tradition "
            "for the age of mass consumption. Her canvases depict plastic-wrapped ready meals, "
            "energy drinks, and processed snacks with the same devotional attention that Dutch "
            "masters brought to lobsters and Venetian glassware. The effect is both comic and "
            "devastating: these objects are our still life, the material culture through which "
            "future archaeologists will know us. The central gallery presents Hassan Ali's "
            "'Displaced Objects,' a series of large-scale photographs of personal possessions "
            "belonging to refugees and asylum seekers, each item carefully arranged against a "
            "neutral background and accompanied by a first-person account of its significance. "
            "Ali's work transforms the still life genre into a vehicle for testimony and empathy, "
            "insisting on the human presence implied by every object. The exhibition also features "
            "work by Emma Whitfield, whose paintings of wildflowers found growing in urban waste "
            "ground address themes of resilience and regeneration. Her palette is deliberately "
            "restricted to greys and greens, with occasional flashes of colour that draw the eye "
            "like the flowers themselves draw the gaze of passers-by in neglected city spaces. "
            "A programme of events includes a drawing workshop with Emma Whitfield and a panel "
            "discussion on the politics of objects chaired by curator Dr Farah Khan."
        ),
    },
    {
        "id": "ART-005",
        "type": "artist_biography",
        "title": "David Park: Slow Seeing",
        "text": (
            "David Park (born 1967, Whitby; based in North Yorkshire) is a photographer known for "
            "his meditative, long-exposure seascapes and studies of the Yorkshire coastline. He began "
            "photographing the sea in 1998 after leaving a career in commercial photography, seeking "
            "what he describes as 'a way of looking that has nothing to do with capturing a moment "
            "and everything to do with experiencing duration.' Park works exclusively with a large-"
            "format 5x4 film camera and exposures that range from several minutes to over an hour. "
            "The resulting images reduce the turbulent North Sea to a luminous, ethereal plane, "
            "creating compositions of radical simplicity in which sea, sky, and horizon become "
            "abstract fields of tone. His printing process is equally painstaking: each image is "
            "produced as a platinum-palladium print, a nineteenth-century technique that yields "
            "an extraordinary tonal range and a surface quality impossible to achieve with digital "
            "printing. Park's work has been exhibited at the Victoria and Albert Museum, the "
            "Photographers' Gallery, the Foam Museum in Amsterdam, and the Centre for Contemporary "
            "Photography in Melbourne. His monograph 'Littoral' was published by Thames and Hudson "
            "in 2018 and was named Photography Book of the Year by the British Journal of Photography. "
            "He has completed artist residencies at Hospitalfield in Arbroath and the Josef and Anni "
            "Albers Foundation in Connecticut. Park's more recent work has expanded to include the "
            "coastlines of Iceland and Norway, exploring the visual similarities and geological "
            "connections between North Atlantic landscapes."
        ),
    },
    {
        "id": "EXH-006",
        "type": "exhibition",
        "title": "Woven Histories: Textile as Art",
        "year": 2024,
        "text": (
            "Woven Histories celebrates the resurgence of textile-based practice in contemporary "
            "art, bringing together twelve artists who use weaving, embroidery, dyeing, and other "
            "fibre techniques to address themes of identity, labour, and cultural heritage. The "
            "exhibition challenges the persistent hierarchy that relegates textile to 'craft' and "
            "elevates painting and sculpture to 'art,' arguing that this distinction is rooted in "
            "gendered and colonial assumptions about value. The opening gallery features Priya "
            "Kapoor's monumental woven steel tapestries, which translate Mughal geometric patterns "
            "into industrial chain-link fencing. Kapoor, who grew up in Birmingham surrounded by "
            "her grandmother's embroidery, describes her work as 'an act of translation between "
            "domestic intimacy and public infrastructure.' The scale and weight of her pieces demand "
            "attention, their shadows on the gallery walls creating a secondary layer of pattern that "
            "shifts with the light. In the next gallery, Oluwaseun Adeyemi's tapestries woven from "
            "recycled plastic bags collected from markets in Lagos and London address the global "
            "circulation of waste and the informal economies of reuse. The colours of the bags, "
            "striped reds, blues, and greens familiar from corner shops worldwide, create a visual "
            "language that is immediately recognisable across cultures. The show also includes Megan "
            "Hughes's embroidered maps of Welsh mining communities, each stitch representing a "
            "household that was present in the 1920 census but had disappeared by 1990. The works "
            "function simultaneously as data visualisation and memorial, their labour-intensive "
            "creation mirroring the manual labour they commemorate. A companion exhibition in the "
            "gallery's studio space presents work by students from the Royal College of Art's "
            "Textiles programme, establishing a dialogue between established and emerging practitioners."
        ),
    },
    {
        "id": "ART-006",
        "type": "artist_biography",
        "title": "Marcus Fletcher: Casting Time",
        "text": (
            "Marcus Fletcher (born 1982, Dorchester; based in Dorset) is a sculptor who works "
            "primarily with concrete, plaster, and found geological materials to explore themes of "
            "erosion, entropy, and the deep time of landscape. He studied Fine Art at the University "
            "of the Arts London before completing an MFA at the Glasgow School of Art, where his "
            "work took a decisive turn towards site-specific and process-based practice. Fletcher's "
            "best-known project, 'Erosion Studies,' involves taking plaster and concrete casts from "
            "eroding coastal formations along the Jurassic Coast. He returns to the same sites "
            "annually, documenting the incremental loss of cliff face through sequential casts that "
            "function as physical records of geological time. The resulting works are displayed "
            "alongside their moulds and photographic documentation, emphasising the paradox of "
            "preserving something defined by its disappearance. His work has been exhibited at the "
            "Whitmore Gallery, the Jerwood Space, the Henry Moore Institute, and the Yorkshire "
            "Sculpture Park. He has collaborated with researchers at the British Geological Survey "
            "and the National Oceanography Centre on projects mapping rates of coastal erosion. "
            "Fletcher was awarded the Jerwood Makers Prize in 2020 and has completed residencies "
            "at the Cill Rialaig Project in Ireland and Artangel's laboratory programme. He is "
            "currently working on a commission for the Lyme Regis Museum that will combine cast "
            "coastal forms with fossil specimens, drawing parallels between geological and cultural "
            "processes of preservation and loss."
        ),
    },
    {
        "id": "EXH-007",
        "type": "exhibition",
        "title": "Portraits of Power: Faces of Modern Britain",
        "year": 2022,
        "text": (
            "Portraits of Power brings together fifty portraits created over the past decade that "
            "collectively redefine who is visible in British portraiture and how power is represented. "
            "The exhibition challenges the conventions of a genre historically dominated by images of "
            "white, male authority, presenting instead a diverse cross-section of contemporary British "
            "life. The show opens with a room of official portraits, but not the kind typically found "
            "in boardrooms and college halls. These are portraits of community leaders, activists, and "
            "public servants commissioned specifically for this exhibition: a head teacher from "
            "Tottenham, a youth worker from Glasgow, a lifeboat volunteer from Anglesey. Each subject "
            "was given a choice of artist and contributed to decisions about setting and pose, "
            "redistributing the power dynamics of the portrait commission. The largest gallery "
            "presents Kehinde Okafor's series 'The Custodians,' oil paintings of night-shift cleaners "
            "in the Houses of Parliament. Painted with the scale, richness, and compositional "
            "authority of state portraiture, these works confront the invisibility of essential "
            "workers within the very institution that legislates their working conditions. The "
            "exhibition also features photography by Suki Dhanda, whose intimate portraits of "
            "British Sikh families combine formal studio techniques with the visual language of "
            "family snapshots. Her images are displayed alongside personal objects and handwritten "
            "notes contributed by her subjects, creating a multilayered portrait that extends "
            "beyond the photographic frame. A dedicated room presents self-portraits by artists "
            "with disabilities, curated by the artist collective Shape Arts, challenging the "
            "narrow range of bodies historically represented in portraiture. The accompanying "
            "publication includes essays by cultural historian David Olusoga and curator Lubaina "
            "Himid, placing the exhibition in the context of ongoing debates about representation "
            "and institutional power in British art."
        ),
    },
    {
        "id": "ART-007",
        "type": "artist_biography",
        "title": "Helena Voss: Language Machines",
        "text": (
            "Helena Voss (born 1988, Berlin; based in London) is a digital artist and writer whose "
            "work explores the boundaries between human and machine language, creativity, and "
            "consciousness. She studied Computational Linguistics at University College London "
            "before completing an MA in Computational Arts at Goldsmiths. This dual training in "
            "the sciences and arts of language gives her work a technical rigour unusual in the "
            "digital art world. Voss's installations typically involve custom-built language models "
            "that she trains on specific literary corpora. Her breakthrough work, 'Ghost Writer' "
            "(2023), used a model fine-tuned on Virginia Woolf's complete writings to generate new "
            "prose in real time, displayed as a continuous scroll of projected text. The installation, "
            "shown at the Whitmore Gallery's 'Code and Canvas' exhibition, provoked heated debate "
            "about authorship, appropriation, and the nature of literary style. Her subsequent piece, "
            "'Babel,' presented at the Serpentine, consisted of multiple language models trained on "
            "different religious texts engaging in an automated theological dialogue, their generated "
            "texts displayed on facing screens in a darkened room. Critical responses have been "
            "polarised. Art critic Adrian Searle described Voss's work as 'the most intellectually "
            "ambitious art being made with AI today,' while others have questioned whether the "
            "outputs of her models constitute art or merely sophisticated pastiche. Voss herself "
            "rejects this binary, arguing that all language is generative and that her models make "
            "visible the processes of pattern, imitation, and recombination that underlie human "
            "creativity. She has published extensively on the ethics of AI-generated text and sits "
            "on the advisory board of the Ada Lovelace Institute."
        ),
    },
    {
        "id": "EXH-008",
        "type": "exhibition",
        "title": "After Nature: Art and the Anthropocene",
        "year": 2023,
        "text": (
            "After Nature gathers work by twenty artists responding to the ecological and existential "
            "challenges of the Anthropocene. The exhibition resists both the despair of environmental "
            "catastrophism and the false comfort of techno-optimism, seeking instead a more complex "
            "and emotionally honest artistic engagement with our changing planet. The opening "
            "installation, 'Requiem for a Glacier' by Icelandic-British artist Bjork Halldorsdottir, "
            "fills the entrance hall with the sound of melting ice, recorded over twelve months at "
            "the Vatnajokull glacier. Speakers are arranged at varying heights, and the audio is "
            "spatialised so that visitors experience the sounds as coming from above, below, and "
            "around them. The effect is at once mournful and strangely beautiful. The main galleries "
            "are organised thematically: Water, Earth, Air, and Fire. In the Water section, Amara "
            "Osei's infrared photographs of contaminated waterways in South Wales are shown alongside "
            "Tom Walsh's video documentation of wetland restoration in the Thames estuary, creating "
            "a dialogue between degradation and repair. The Earth section features Marcus Fletcher's "
            "coastal erosion casts and a new commission by ceramicist Yuki Tanaka, who has created "
            "a series of vessels using clay gathered from sites of environmental significance, each "
            "piece carrying the literal substance of the place it represents. The Air section "
            "presents data-driven artworks, including a real-time visualisation of air quality "
            "data from sensors placed around London, translated into colour and sound by artist-"
            "programmer Kai Yeung. The Fire section concludes the exhibition with images and objects "
            "relating to wildfire, deforestation, and the combustion of fossil fuels. The overall "
            "effect is neither didactic nor nihilistic but deeply felt and rigorously made, offering "
            "art as a space for processing the emotional reality of environmental change."
        ),
    },
    {
        "id": "ART-008",
        "type": "artist_biography",
        "title": "Yuki Tanaka: Earth and Form",
        "text": (
            "Yuki Tanaka (born 1975, Kyoto; based in London and Kyoto) is a ceramicist and "
            "installation artist whose work bridges Japanese and European ceramic traditions. She "
            "trained at Kyoto City University of Arts before moving to London in 2002 to study at "
            "the Royal College of Art. Her work ranges from intimate, hand-built vessels to immersive "
            "installations comprising hundreds of individual forms. Tanaka's practice is grounded in "
            "a deep knowledge of materials: she mixes her own clay bodies from locally sourced earths "
            "and develops her own glazes from wood ash and mineral oxite. She fires her work in a "
            "wood-burning anagama kiln that she built herself in the Kent countryside, a process that "
            "takes up to five days and produces effects of colour and surface that are impossible to "
            "replicate in electric or gas kilns. Her major installation, 'Garden of Earthly Delights' "
            "(2023), shown at the Whitmore Gallery's 'Material Worlds' exhibition, comprised over "
            "three hundred stoneware forms ranging from delicate flowers to surreal hybrid creatures. "
            "The work drew on Japanese ceramic traditions, European porcelain figurines, and the "
            "imagery of Hieronymus Bosch to create an immersive environment that oscillated between "
            "beauty and grotesquerie. Her more recent work for the 'After Nature' exhibition at the "
            "Whitmore Gallery uses clay gathered from sites of environmental significance, including "
            "eroding riverbanks, contaminated former industrial sites, and ancient woodlands under "
            "threat from development. These 'site vessels' carry the literal substance of the places "
            "they represent, functioning as both artworks and archives. Tanaka has exhibited at the "
            "Victoria and Albert Museum, the Crafts Council Gallery, MOMA Kyoto, and the International "
            "Ceramics Festival in Mino. She received the Loewe Foundation Craft Prize in 2022."
        ),
    },
    {
        "id": "EXH-009",
        "type": "exhibition",
        "title": "Abstract Territories: Painting Beyond the Frame",
        "year": 2021,
        "text": (
            "Abstract Territories brings together nine painters who are pushing the boundaries of "
            "abstract painting through expanded approaches to scale, material, and spatial "
            "installation. The exhibition argues that abstract painting is far from exhausted as a "
            "medium, and that a new generation of artists is finding fresh possibilities within a "
            "tradition often declared dead. The show opens with James Okonkwo's 'Indigo Field,' "
            "a twelve-metre canvas that wraps around three walls of the gallery, immersing the "
            "viewer in a deep blue space punctuated by gestural marks in burnt sienna and gold. "
            "Okonkwo's use of natural pigments, hand-ground indigo and camwood, gives the surface "
            "a luminosity and depth that synthetic paints cannot achieve. The physical scale of the "
            "work transforms the act of looking from observation into inhabitation. Sarah Chen's "
            "contribution, 'Estuary,' consists of six unstretched canvases hung from the ceiling at "
            "varying heights, their translucent acrylic washes creating overlapping layers of colour "
            "that shift as the viewer moves through the space. The work is both painting and "
            "installation, collapsing the boundary between the two categories. In the project space, "
            "emerging artist Zara Mahmood presents paintings made with crushed stone and powdered "
            "brick mixed into acrylic medium, their rough, granular surfaces referencing the "
            "demolished buildings from which the materials were salvaged. Her work connects abstract "
            "painting to themes of demolition, memory, and urban regeneration. The exhibition also "
            "features painters who bring digital processes into conversation with traditional media. "
            "Kai Yeung's algorithmically generated compositions are transferred to canvas through a "
            "laborious process of hand-painting guided by a projected digital template, each work "
            "taking several weeks to complete. The tension between computational precision and the "
            "inevitable imperfections of the hand creates surfaces that vibrate with a paradoxical "
            "energy. A catalogue essay by critic Martin Herbert argues that these artists share not "
            "a style but an attitude: a refusal to accept that painting's possibilities are finite."
        ),
    },
    {
        "id": "ART-009",
        "type": "artist_biography",
        "title": "Fatima Khalil: Documenting Borders",
        "text": (
            "Fatima Khalil (born 1983, Lahore; based in Edinburgh) is a photographer whose work "
            "examines the relationship between landscape, borders, and belonging. She studied "
            "Photography at Edinburgh College of Art before completing a practice-based PhD at the "
            "University of Edinburgh, where her research focused on the photographic representation "
            "of contested territories. Khalil's best-known project, 'Borderlands,' is a three-year "
            "documentation of the landscapes along the English-Scottish border, created using a "
            "large-format 10x8 film camera. Her images capture the empty moorlands, quiet valleys, "
            "and ruined fortifications where centuries of conflict have inscribed themselves into the "
            "land. The series is accompanied by oral histories gathered from farming communities "
            "whose connection to the land predates the national boundary itself. 'Borderlands' has "
            "been exhibited at the Scottish National Gallery of Modern Art, the Whitmore Gallery's "
            "'Terrain' exhibition, and the Impressions Gallery in Bradford. It was published as a "
            "monograph by MACK Books in 2023. Her earlier project, 'Partition Lines,' documented "
            "the landscapes of the India-Pakistan border region, drawing parallels between the "
            "division of the subcontinent and the historical Anglo-Scottish border. This work was "
            "shown at the Lahore Biennale and the Photographers' Gallery in London. Khalil is a "
            "senior lecturer in Photography at Edinburgh College of Art and a regular contributor "
            "to Source Photographic Review. She was awarded the Paul Hamlyn Foundation Award for "
            "Artists in 2022, supporting the development of a new project photographing the "
            "landscapes of the Irish border in the context of post-Brexit political realignment."
        ),
    },
    {
        "id": "EXH-010",
        "type": "exhibition",
        "title": "The Garden Imagined: Plants in Art and Culture",
        "year": 2024,
        "text": (
            "The Garden Imagined explores the enduring presence of plants, gardens, and botanical "
            "imagery in art from the Renaissance to the present day. The exhibition moves beyond "
            "the decorative to examine how artists have used the garden as a site for exploring "
            "ideas of paradise, power, science, empire, and ecological responsibility. The opening "
            "gallery presents botanical illustrations from the Natural History Museum's collection "
            "alongside contemporary photographic studies by Anna Atkins Prize winner Rina Sugiyama, "
            "whose cyanotype prints continue a tradition of botanical image-making that stretches "
            "back to the origins of photography. The main galleries feature a chronological journey "
            "through artistic engagements with the garden. A room dedicated to the Arts and Crafts "
            "movement includes tapestry designs by William Morris and ceramics by William De Morgan, "
            "their intricate floral patterns reflecting a vision of the garden as a refuge from "
            "industrial modernity. This is contrasted in the adjacent gallery by photographs from "
            "Derek Jarman's Prospect Cottage garden in Dungeness, where the filmmaker cultivated "
            "plants in the shadow of a nuclear power station, creating a space of beauty in an "
            "apparently inhospitable landscape. The contemporary section is anchored by Emma "
            "Whitfield's paintings of wildflowers growing in urban waste ground, their quiet "
            "persistence a metaphor for resilience in neglected spaces. Whitfield's work is shown "
            "alongside Yuki Tanaka's ceramic flowers, which range from botanically precise to "
            "fantastically inventive, blurring the line between observation and imagination. The "
            "exhibition concludes with a living installation by garden designer Dan Pearson, a "
            "miniature woodland planted in the gallery's courtyard that will be tended throughout "
            "the exhibition's run, its growth and seasonal change becoming part of the artwork."
        ),
    },
    {
        "id": "ART-010",
        "type": "artist_biography",
        "title": "Priya Kapoor: Weaving Resistance",
        "text": (
            "Priya Kapoor (born 1986, Birmingham; based in London) is a sculptor and textile artist "
            "whose work explores the intersection of craft traditions, industrial materials, and "
            "postcolonial identity. She studied Three-Dimensional Design at the University of "
            "Brighton before completing an MA in Sculpture at the Royal College of Art. Growing up "
            "in a family of textile workers in Birmingham's jewellery quarter, Kapoor developed an "
            "early understanding of the relationship between handcraft and industrial production. "
            "Her signature works are large-scale woven tapestries made from industrial chain-link "
            "fencing, stainless steel wire, and copper mesh. These pieces translate the geometric "
            "patterns of Mughal architecture and South Asian textiles into materials associated with "
            "security, boundaries, and exclusion. The resulting works are visually striking, their "
            "metallic surfaces catching and reflecting light, but they also carry a conceptual weight "
            "that addresses themes of migration, belonging, and cultural translation. Major "
            "exhibitions include 'Woven Histories' at the Whitmore Gallery (2024), 'Border Patterns' "
            "at the Ikon Gallery, Birmingham (2022), and 'Material Identities' at the Whitechapel "
            "Gallery (2021). Her work was included in the British Art Show 9 and the Dhaka Art "
            "Summit. Kapoor has completed residencies at the Delfina Foundation in London and the "
            "Textile Museum in Tilburg. She was awarded the Crafts Council Spark Plug Prize in 2019 "
            "and was nominated for the Max Mara Art Prize for Women in 2023. She is currently "
            "working on a major public commission for Birmingham New Street station, a suspended "
            "textile sculpture that will reference the city's industrial heritage and its diverse "
            "communities."
        ),
    },
    {
        "id": "EXH-011",
        "type": "exhibition",
        "title": "Colour Field: Immersive Painting Experiences",
        "year": 2024,
        "text": (
            "Colour Field takes its name from the mid-twentieth-century painting movement but "
            "extends the concept into three-dimensional, immersive territory. Five artists have been "
            "invited to create room-scale colour environments that envelop the viewer, transforming "
            "the act of looking at a painting into the experience of being inside one. The exhibition "
            "opens with Sarah Chen's 'Chamber,' a room whose walls, ceiling, and floor are covered "
            "with unstretched canvases painted in layered washes of cerulean blue and viridian green. "
            "Soft natural light filters through a translucent ceiling panel, and the painted surfaces "
            "seem to breathe with colour, creating an effect that Chen describes as 'being inside "
            "the sea without the cold.' The second room features a new work by emerging painter "
            "Zara Mahmood, who has covered every surface with a dense, tactile layer of crushed "
            "sandstone mixed into deep red pigment. The room smells of earth and mineral, and "
            "the rough walls invite touch, engaging senses that painting normally excludes. "
            "The effect is of entering a cave or an ancient built structure, connecting the "
            "experience of colour to deep geological and architectural time. James Okonkwo's "
            "contribution fills a room with suspended lengths of indigo-dyed linen, creating a "
            "maze-like space that references both the textile dyeing traditions of West Africa and "
            "the colour field paintings of Morris Louis. Visitors navigate through the hanging "
            "fabrics, their movement creating shifting compositions of light and shadow. "
            "The most technologically complex piece is by Kai Yeung, whose room uses "
            "programmable LED panels behind translucent screens to create slowly evolving colour "
            "gradients that respond to the collective movement of visitors, tracked by overhead "
            "sensors. The installation references both Mark Rothko's chapel paintings and the "
            "responsive digital environments of teamLab, seeking a synthesis of painterly "
            "contemplation and technological interactivity."
        ),
    },
    {
        "id": "ART-011",
        "type": "artist_biography",
        "title": "Tom Walsh: Urban Ecologies",
        "text": (
            "Tom Walsh (born 1984, Deptford; based in East London) is a filmmaker and photographer "
            "whose work documents the intersection of urban development, ecology, and community in "
            "post-industrial London. He studied Film at the London College of Communication before "
            "completing an MA in Visual Sociology at Goldsmiths. His practice combines documentary "
            "filmmaking with participatory methods, often collaborating with local communities over "
            "extended periods. Walsh's best-known project, 'Wild City,' is a five-year documentation "
            "of urban rewilding initiatives in East London, from community gardens in former "
            "industrial yards to the managed retreat of flood defences along the Thames estuary. "
            "The work includes film, photography, sound recordings, and a community archive of "
            "residents' memories of the changing landscape. 'Wild City' was exhibited at the "
            "Whitmore Gallery's 'Terrain' exhibition and at the Barbican's 'Our Time on Earth' "
            "show. It was also screened at the Sheffield Documentary Festival and the London "
            "Short Film Festival. His subsequent project, 'Common Ground,' examines the contested "
            "future of London's allotment sites, many of which are under threat from housing "
            "development. The work combines aerial photography with interviews and soil analysis, "
            "building a case for allotments as sites of ecological and social significance. Walsh "
            "is a visiting lecturer at the London College of Communication and a trustee of the "
            "London Wildlife Trust. He was awarded the Jerwood/FVU Award in 2021 and was "
            "shortlisted for the Artes Mundi prize in 2023."
        ),
    },
    {
        "id": "EXH-012",
        "type": "exhibition",
        "title": "Migration Patterns: Art and Movement",
        "year": 2023,
        "text": (
            "Migration Patterns brings together artists whose work addresses the experience of "
            "movement, displacement, and resettlement in the contemporary world. The exhibition "
            "avoids a singular narrative of migration, instead presenting a plurality of "
            "perspectives that reflect the complexity and diversity of migrant experience. The "
            "opening installation, by James Okonkwo, presents a room-sized floor piece made from "
            "hundreds of individually dyed indigo cloth squares, each one representing a stage in "
            "a journey. Visitors are invited to walk across the surface, their footprints leaving "
            "temporary traces that fade as the fabric recovers, a metaphor for the transient marks "
            "of passage. The photographic section includes Fatima Khalil's 'Partition Lines,' "
            "which documents the landscapes of the India-Pakistan border, and Hassan Ali's "
            "'Displaced Objects,' portraits of personal belongings carried by refugees. Together "
            "these works address migration at scales ranging from the geopolitical to the intimately "
            "personal. The exhibition also features Mei Lin's composite photographs overlaying "
            "historical maps of migration routes onto contemporary satellite imagery, and a "
            "sound installation by composer and artist Aisha Devi that layers recordings of "
            "border crossings, arrival halls, and language lessons into an immersive sonic "
            "environment. A programme of events includes storytelling workshops facilitated "
            "by the Migration Museum and a reading group exploring literary responses to "
            "displacement."
        ),
    },
    {
        "id": "ART-012",
        "type": "artist_biography",
        "title": "Nadia Petrov: The Weight of Things",
        "text": (
            "Nadia Petrov (born 1980, Moscow; based in London) is a painter whose hyperrealist "
            "oil paintings explore the cultural significance of everyday objects. She studied at "
            "the Moscow Academy of Fine Art before moving to London in 2005 to complete an MFA "
            "at the Slade School of Fine Art. Her early training in Russian academic realism gave "
            "her a technical command of oil painting that she has directed towards subject matter "
            "drawn from the mundane and overlooked. Petrov's best-known series, 'Supermarket "
            "Vanitas,' consists of large-scale oil paintings of supermarket shelves, depicting "
            "plastic-wrapped ready meals, energy drinks, and processed snacks with the same "
            "devotional attention that seventeenth-century Dutch masters brought to their "
            "arrangements of fruit, flowers, and silver. The paintings are technically "
            "extraordinary, their surfaces achieving a trompe l'oeil quality that initially "
            "delights before the satirical intent becomes apparent. The series was the centrepiece "
            "of the Whitmore Gallery's 'Still Life, Still Living' exhibition (2022) and has since "
            "been shown at the Saatchi Gallery and the Museum of Contemporary Art, Krakow. Her "
            "more recent work, 'Inventory,' turns the same hyperrealist attention to the contents "
            "of domestic cupboards and drawers, revealing the intimate material archaeology of "
            "everyday life. Each painting takes between three and six months to complete. "
            "Petrov has been awarded the BP Portrait Award (Visitor's Choice, 2019) and was "
            "elected a member of the New English Art Club in 2021. Her work is in the collections "
            "of the Victoria and Albert Museum, the Government Art Collection, and the "
            "Museum of Modern Art, Moscow."
        ),
    },
    {
        "id": "EXH-013",
        "type": "exhibition",
        "title": "Print/Process: Contemporary Printmaking",
        "year": 2022,
        "text": (
            "Print/Process celebrates the vitality of contemporary printmaking, showcasing work "
            "by fifteen artists who are expanding the technical and conceptual possibilities of the "
            "medium. The exhibition covers the full spectrum of printmaking techniques, from woodcut "
            "and etching to screenprint, risograph, and digital laser cutting, demonstrating that "
            "print remains one of the most versatile and innovative areas of contemporary art. "
            "The opening gallery features a suite of large-scale woodcuts by Kenyan-British artist "
            "Grace Ndiritu, carved from single sheets of birch plywood and printed on handmade "
            "Japanese washi paper. The images depict hybrid figures that combine human and animal "
            "forms, drawing on East African folk traditions and the European grotesque. Their scale "
            "and the visible physicality of the carving process give the prints a monumental "
            "presence usually associated with painting. In the next room, Daniel Okoro presents "
            "prints generated by feeding his GAN-produced images through a risograph printer, "
            "the mechanical imperfections of the cheap printing process introducing an element "
            "of chance and materiality to otherwise immaterial digital images. The show also "
            "includes Anna Fitzgerald's photopolymer etchings of architectural details from "
            "demolished London buildings, and Hiro Sato's screenprints that layer neon ink over "
            "recycled newsprint to create works about media saturation and information overload. "
            "A print studio has been set up in the gallery's education space, where visitors "
            "can try their hand at basic printmaking techniques during drop-in workshops "
            "throughout the exhibition's run."
        ),
    },
    {
        "id": "ART-013",
        "type": "artist_biography",
        "title": "Kai Yeung: Data as Pigment",
        "text": (
            "Kai Yeung (born 1992, Hong Kong; based in London) is an artist and programmer whose "
            "work translates data into visual and sonic experience. He studied Computer Science "
            "at the University of Cambridge before completing an MA in Computational Arts at "
            "Goldsmiths, where he developed the algorithmic tools that underpin his practice. "
            "Yeung's work occupies the intersection of data visualisation, generative art, and "
            "environmental science. His best-known piece, 'Breathe,' is a real-time installation "
            "that translates air quality data from a network of sensors placed around London into "
            "slowly evolving colour fields and ambient sound. The work was shown at the Whitmore "
            "Gallery's 'After Nature' exhibition and at the Barbican's Digital Revolution show. "
            "Its beauty is uncomfortable: the most visually striking moments correspond to the "
            "worst air quality readings, forcing viewers to confront the aestheticisation of "
            "pollution. His painted works begin as algorithmically generated compositions, "
            "designed using custom software that he has developed over several years. These "
            "digital templates are then painstakingly transferred to canvas by hand, a process "
            "that takes several weeks per painting. The tension between computational precision "
            "and the inevitable imperfections of manual execution is central to Yeung's interest: "
            "the hand introduces warmth, error, and humanity into the mathematical sublime. "
            "These paintings were featured in the Whitmore Gallery's 'Abstract Territories' "
            "exhibition and have been acquired by the Arts Council Collection. Yeung has been "
            "awarded the Lumen Prize for Digital Art (2022) and was artist-in-residence at the "
            "Alan Turing Institute in 2023. He teaches creative coding at Goldsmiths and has "
            "published research on the use of machine learning in artistic practice."
        ),
    },
    {
        "id": "EXH-014",
        "type": "exhibition",
        "title": "Sound and Vision: Art that Listens",
        "year": 2024,
        "text": (
            "Sound and Vision explores the growing importance of sound in contemporary visual art "
            "practice. The exhibition brings together installations, sculptures, and multimedia works "
            "that use sound not as accompaniment but as a primary material, equal in importance to "
            "visual form. The opening gallery presents a new commission by Janet Cardiff and George "
            "Bures Miller, the celebrated Canadian duo whose 'audio walks' have redefined the "
            "relationship between sound, space, and narrative. Their piece for the Whitmore Gallery "
            "guides visitors through the building using binaural audio played through headphones, "
            "layering fictional narratives and historical sounds over the actual spaces of the "
            "gallery, creating a disorienting and poetic double reality. The main galleries feature "
            "Rachel Lim's sound-responsive sculptures, which incorporate embedded sensors that "
            "translate ambient noise into subtle movements, causing the polished steel surfaces to "
            "shift and catch light in response to visitors' conversations and footsteps. Lim's "
            "work transforms the viewer into an unwitting performer, their presence literally shaping "
            "the artwork. The exhibition also includes James Okonkwo's collaboration with musicians "
            "from the London Philharmonia, a series of paintings created in live response to "
            "musical performances, their gestural marks recording the rhythm and dynamics of the "
            "music. The paintings are displayed alongside recordings of the performances, allowing "
            "visitors to see and hear the works simultaneously. Helena Voss contributes 'Babel,' "
            "her installation of multiple language models engaged in automated theological dialogue, "
            "their generated texts read aloud by synthetic voices in a darkened room. The experience "
            "is simultaneously meditative and unsettling, the machine voices occupying an uncanny "
            "space between human speech and algorithmic generation."
        ),
    },
    {
        "id": "ART-014",
        "type": "artist_biography",
        "title": "Emma Whitfield: Flowers from Rubble",
        "text": (
            "Emma Whitfield (born 1977, Sheffield; based in London) is a painter whose work "
            "celebrates the resilience of nature in urban environments. She studied Painting at "
            "Sheffield Hallam University before completing a Postgraduate Diploma at the Royal "
            "Academy Schools. Whitfield's practice centres on the wildflowers, grasses, and "
            "self-seeded trees that colonise the forgotten spaces of cities: building sites, "
            "demolished lots, railway embankments, and cracks in pavements. Her palette is "
            "deliberately muted, predominantly greys, ochres, and olive greens, with occasional "
            "accents of vivid colour where a flower catches the light. This restrained approach "
            "mirrors the experience of noticing these plants in situ, the flash of colour that "
            "draws the eye to something easily overlooked. Whitfield paints from direct observation, "
            "spending extended periods sitting and drawing in the waste grounds and liminal spaces "
            "that provide her subjects. She has described her practice as 'portraiture of plants,' "
            "bringing the same attention and respect to a dandelion growing through concrete as a "
            "traditional portrait painter would bring to a human sitter. Major exhibitions include "
            "'Still Life, Still Living' at the Whitmore Gallery (2022), 'Urban Flora' at the "
            "Flowers Gallery (2023), and 'The Garden Imagined' at the Whitmore Gallery (2024). "
            "Her work is in the collections of the Arts Council, the Contemporary Art Society, "
            "and the Sheffield Graves Gallery. She was awarded the Jerwood Painting Fellowship "
            "in 2018 and was shortlisted for the John Moores Painting Prize in 2020. Whitfield "
            "is also a co-founder of the Wild City drawing group, which organises plein air "
            "drawing sessions in overlooked urban green spaces across London."
        ),
    },
    {
        "id": "EXH-015",
        "type": "exhibition",
        "title": "Ceramics Now: Earth, Fire, and Meaning",
        "year": 2023,
        "text": (
            "Ceramics Now surveys the extraordinary renaissance of ceramics in contemporary art, "
            "presenting work by twenty artists who are using clay as a medium for conceptual "
            "ambition, political commentary, and formal innovation. The exhibition challenges the "
            "persistent boundary between art and craft, arguing that ceramics' current moment of "
            "prominence is not a trend but a recognition of the medium's unique expressive "
            "possibilities. The opening gallery features a retrospective of Edmund de Waal's "
            "porcelain installations, their serene rows of thrown vessels arranged in vitrines "
            "that reference both museum display and minimalist sculpture. De Waal's influence on "
            "the current generation of ceramic artists is acknowledged throughout the show. The "
            "main galleries present Yuki Tanaka's 'Garden of Earthly Delights' alongside newer "
            "works that push her practice in more explicitly political directions. Her series "
            "'Toxic Blooms,' created from clay gathered at contaminated industrial sites, combines "
            "the formal beauty of flower-like forms with the disturbing knowledge that the material "
            "itself carries traces of environmental pollution. The exhibition also features the "
            "functional ceramics of Florian Gadsby, whose wheel-thrown stoneware demonstrates that "
            "the everyday pot remains a valid and vital form of artistic expression. His work is "
            "presented alongside a video installation documenting his throwing process, the rhythm "
            "of the wheel and the quiet concentration of the maker offering a counterpoint to the "
            "more spectacular installations elsewhere in the show. Other highlights include Halima "
            "Cassell's geometric carved vessels, inspired by Moroccan zellige tilework, and Phoebe "
            "Cummings's unfired clay installations that are designed to slowly deteriorate over the "
            "course of the exhibition, their impermanence a meditation on the fragility of form."
        ),
    },
    {
        "id": "ART-015",
        "type": "artist_biography",
        "title": "Daniel Okoro: Synthetic Geographies",
        "text": (
            "Daniel Okoro (born 1991, London; based in London and Lagos) is a digital artist whose "
            "work uses generative adversarial networks and other machine learning tools to explore "
            "the nature of place, memory, and representation. He studied Geography at King's College "
            "London before completing an MA in Art and Science at Central Saint Martins, a trajectory "
            "that reflects his interest in the territory between scientific observation and artistic "
            "imagination. Okoro's best-known series, 'Latent Landscapes,' uses GANs trained on "
            "satellite imagery to generate images of places that do not exist but could. These "
            "fictional topographies are printed at large scale on aluminium panels, their hyperreal "
            "surfaces both seductive and unsettling. The series was shown at the Whitmore Gallery's "
            "'Code and Canvas' exhibition and at the Photographers' Gallery's 'All I Know Is What's "
            "On The Internet' show. It was accompanied by an essay by geographer Doreen Massey Prize "
            "winner Dr Leila Dawson, who described the works as 'maps of probability rather than "
            "actuality.' His subsequent project, 'Memory Palace,' uses the same generative tools "
            "to create images based on verbal descriptions of remembered places gathered through "
            "interviews with diasporic communities. The resulting images, which approximate but "
            "never quite replicate the described locations, become visual metaphors for the "
            "distortions and idealisations of nostalgic memory. Okoro has exhibited at the "
            "Whitechapel Gallery, the Science Gallery London, and the Lagos Biennial. He was "
            "awarded the Aesthetica Art Prize in 2023 and is currently a research fellow at the "
            "Creative Computing Institute, University of the Arts London."
        ),
    },
]

json_path = os.path.join(BASE_DIR, "gallery_catalogues.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(gallery_entries, f, indent=2)

print(f"Generated {len(gallery_entries)} gallery entries in {json_path}")


# ============================================================
# 6. gallery_embeddings.npy
#    TF-IDF embeddings for chunked gallery text
# ============================================================

# We need to chunk the gallery texts and compute TF-IDF
# Since this runs outside Pyodide, we can use sklearn

def chunk_text(text, chunk_size=300, overlap=50):
    """Split text into overlapping word-based chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# Collect all chunks with metadata
all_chunks = []
chunk_metadata = []
for entry in gallery_entries:
    text = entry["text"]
    entry_chunks = chunk_text(text, chunk_size=200, overlap=40)
    for i, chunk in enumerate(entry_chunks):
        all_chunks.append(chunk)
        chunk_metadata.append({
            "source_id": entry["id"],
            "source_title": entry["title"],
            "chunk_index": i,
        })

print(f"\nTotal chunks: {len(all_chunks)}")

# Save chunk metadata alongside
chunk_meta_path = os.path.join(BASE_DIR, "gallery_chunk_metadata.json")
with open(chunk_meta_path, "w", encoding="utf-8") as f:
    json.dump(chunk_metadata, f, indent=2)

print(f"Saved chunk metadata to {chunk_meta_path}")

# Now compute TF-IDF embeddings
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np

    vectorizer = TfidfVectorizer(max_features=384)
    embeddings = vectorizer.fit_transform(all_chunks).toarray().astype(np.float32)

    npy_path = os.path.join(BASE_DIR, "gallery_embeddings.npy")
    np.save(npy_path, embeddings)

    # Also save the chunks themselves for use in notebooks
    chunks_path = os.path.join(BASE_DIR, "gallery_chunks.json")
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)

    print(f"Embeddings shape: {embeddings.shape}")
    print(f"Saved embeddings to {npy_path}")
    print(f"Saved chunks to {chunks_path}")

except ImportError:
    print("WARNING: scikit-learn not available. Skipping embedding generation.")
    print("Run: pip install scikit-learn numpy")

print("\nDone! All data files generated.")
