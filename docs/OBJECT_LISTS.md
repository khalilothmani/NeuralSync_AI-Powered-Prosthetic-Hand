# 📦 NeuralSync — Object Classification Lists

Each detected object is matched to a **grab category** that determines  
which grip the hand performs. Below are the complete object lists per category,  
as defined in `src/object_classifier.py`.

---

## Category → Grab Mapping

| Category | Grab ID | Description |
|----------|:-------:|-------------|
| **SENSITIVE** | 2 | Fragile / crushable — soft partial grip |
| **LIGHT** | 3 | Lightweight — gentle cylindrical |
| **MEDIUM** | 1 | Medium weight — power grasp |
| **HEAVY** | 1 | Heavy — full power grasp |
| **PINCH** | 4 | Small / flat — two-finger thumb+index |

---

## 🥚 SENSITIVE Objects (Grab 2 — Soft Grip)

Objects that are fragile, crushable, or extremely delicate:

| Object | Notes |
|--------|-------|
| egg | Classic test case |
| wine_glass | Standard stemware |
| champagne_glass | Thin glass |
| glass | Generic drinking glass |
| light_bulb / lightbulb | Fragile bulb |
| christmas_ornament / ornament | Decorative ball |
| snowglobe / snow globe | Heavy+fragile |
| soap_bubble / bubble | Purely decorative |
| balloon | Very fragile |
| paper_cup | Crushable |
| styrofoam_cup | Crushable |
| thin_glass / crystal_glass | Fragile |
| porcelain_cup | Brittle |
| cracker / biscuit | Brittle food |
| chip / potato_chip / tortilla_chip | Brittle food |
| wafer | Thin + brittle |
| strawberry / cherry / blueberry / raspberry / grape | Soft fruit |
| flower / rose / tulip / daisy / petal | Biological material |
| soap / soap_bar | Slippery + soft |
| ice_cream_cone / cone | Fragile + food |
| cupcake / macaron / meringue / marshmallow | Soft food |
| cotton_ball / cotton_pad | Compressible |
| pill / tablet / capsule | Medical — critical |
| contact_lens_case / lens_case | Small + fragile |
| test_tube / petri_dish | Lab equipment |
| microchip / sim_card / sd_card | Electronics |
| watch / wristwatch / pocket_watch | Delicate mechanics |
| reading_glasses / eyeglasses / sunglasses | Fragile frames |
| vase | Ceramic + fragile |
| ceramic_bowl / porcelain_plate / fine_china | Tableware |
| ornamental_egg | Decorative |
| plastic_bag / sandwich_bag | Deformable |

---

## 🍃 LIGHT Objects (Grab 3 — Gentle Grip)

Objects lighter than ~300g that need secure but non-crushing grip:

| Object | Notes |
|--------|-------|
| cup / mug / coffee_mug / tea_cup | Everyday containers |
| plastic_cup / paper_cup | Disposable cups |
| fork / spoon / teaspoon / chopsticks / straw | Cutlery |
| pen / pencil / marker / highlighter / crayon / chalk | Writing tools |
| eraser / ruler | Stationery |
| paper / notebook / notepad / sticky_note | Stationery |
| envelope / letter / card / postcard / index_card | Mail |
| tissue / napkin / paper_towel / toilet_paper | Soft paper |
| empty_bottle / plastic_bottle_empty | Empty containers |
| orange / apple / pear / peach / plum / kiwi / mango | Medium fruit |
| lemon / lime / tangerine / nectarine / apricot | Citrus / stone fruit |
| small_tomato / cherry_tomato / avocado | Small vegetables |
| bread_roll / croissant / muffin / bagel / donut | Baked goods |
| cookie / brownie | Baked goods |
| remote_control / tv_remote / game_controller | Electronics |
| mouse / computer_mouse | Computer peripheral |
| small_toy | Generic toy |
| hairbrush / comb / toothbrush / razor | Personal hygiene |
| lipstick / mascara / eyeliner / makeup_brush | Cosmetics |
| candle / small_candle | Wax object |
| sponge / scrubber | Cleaning tool |
| headphones / earbuds / earphone | Audio device |
| small_book / paperback | Light reading |
| banana / carrot / celery_stalk / cucumber_small | Vegetables |
| glove / sock / handkerchief | Clothing items |
| USB_drive / flash_drive / memory_stick | Storage devices |
| key / keys / keychain / lanyard | Fasteners |

---

## 🧴 MEDIUM Objects (Grab 1 — Power Grasp)

Objects between ~300g–1kg needing a firm cylindrical grip:

| Object | Notes |
|--------|-------|
| bottle / plastic_bottle / water_bottle_small | Filled containers |
| can / soda_can / beer_can / tin_can | Canned goods |
| book / hardcover / textbook / binder | Reading material |
| wallet / purse / clutch / small_handbag | Accessories |
| apple_large / tomato / bell_pepper / potato / onion | Vegetables |
| corn / zucchini / broccoli / cauliflower / eggplant | Vegetables |
| butternut_squash / grapefruit | Large fruit/veg |
| sandwich / burger / hot_dog / taco / burrito / wrap | Food items |
| plate / bowl / dish | Tableware (empty) |
| hammer / screwdriver / wrench / pliers | Tools |
| knife / kitchen_knife / bread_knife / scissors | Cutting tools |
| smartphone / mobile_phone / cell_phone | Electronics |
| camera / digital_camera / compact_camera | Imaging device |
| tablet / ipad | Tablet computer |
| jar / mason_jar / jam_jar / peanut_butter_jar | Storage jars |
| thermos / flask / travel_mug | Insulated containers |
| shoe / sneaker / boot | Footwear |
| helmet / hat / cap | Headwear |
| toy / action_figure / lego | Toys |
| stapler / tape_dispenser | Office tools |
| deodorant / cologne_bottle / perfume_bottle | Personal care |
| shampoo_bottle / conditioner_bottle | Bathroom items |
| flashlight / torch | Lighting tool |
| binoculars / magnifying_glass | Optical devices |
| clock / alarm_clock | Timepiece |

---

## 🏋️ HEAVY Objects (Grab 1 — Full Power Grasp)

Objects >~1kg requiring maximum grip force:

| Object | Notes |
|--------|-------|
| water_bottle / water bottle / 1kg_bottle | 1L+ water bottle |
| large_bottle / bottle_of_water / gallon_jug / milk_jug | Large containers |
| juice_jug / wine_bottle / beer_bottle / whiskey_bottle | Beverage bottles |
| paint_can / bucket | Large containers |
| pot / cooking_pot / saucepan / skillet / frying_pan | Cookware |
| cast_iron / dutch_oven | Heavy cookware |
| brick / rock / stone | Dense materials |
| dumbbell / weight_plate / kettlebell | Exercise equipment |
| toolbox / power_drill / electric_drill | Heavy tools |
| laptop / notebook_computer | Computers |
| dictionary / encyclopedia | Heavy books |
| large_jar / pickle_jar | Large glass jars |
| pumpkin / watermelon / melon / cabbage | Large produce |
| iron / clothes_iron | Appliance |
| blender_jar / food_processor | Kitchen appliance |
| bag_of_sugar / bag_of_flour | Grocery bags |
| suitcase_handle / briefcase | Luggage |

---

## 🤌 PINCH Objects (Grab 4 — Two-Finger)

Small, flat, or thin objects requiring precision pinch:

| Object | Notes |
|--------|-------|
| coin / penny / nickel / dime / quarter | Currency |
| screw / bolt / nut / washer / nail | Fasteners |
| button / sewing_button / pin / safety_pin | Sewing |
| needle / sewing_needle | Sharp — handle carefully |
| chip / microchip / resistor / capacitor / transistor | Electronics |
| USB_connector / cable_end / plug | Connector |
| ring / earring / stud_earring / bead / pearl | Jewelry |
| gem / gemstone / jewel | Precious stones |
| stamp / postage_stamp | Postal |
| playing_card / business_card / credit_card | Cards |
| id_card / loyalty_card / sim_card | Cards |
| micro_sim / nano_sim / memory_card / microsd | Small electronics |
| battery_aa / battery_aaa / battery_9v / battery | Batteries |
| clip / paper_clip / binder_clip / hairclip / hairpin | Clips |
| toothpick / match / matchstick | Thin sticks |
| sugar_packet / salt_packet | Food packets |
| band_aid / plaster / adhesive_bandage | Medical |
| thumb_drive / nano_usb | Tiny USB |
| key_fob / car_key | Keys |
| dice / die / small_pebble | Small objects |

---

## Adding Custom Objects

To add a new object to a category, edit `src/object_classifier.py`:

```python
SENSITIVE_OBJECTS: list[str] = [
    ...
    "my_new_fragile_object",   # ← Add here
]
```

Use the **exact YOLO class name** (lowercase, spaces replaced with `_`).  
Check all labels your model knows:

```bash
python3 yolo.py --labels
```

Query a specific label's category:

```bash
python3 yolo.py --categories egg water_bottle coin
```
