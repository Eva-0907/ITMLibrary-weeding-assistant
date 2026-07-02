"""Historical titles, outbreak events, and keyword data for weeding decisions."""

# Historical landmark works in tropical medicine and related fields
HISTORICAL_TITLES = [
    # ── Natural science & general science ──────────────────────────────────────
    ("on the origin of species", "darwin"),
    ("micrographia", "hooke"),
    ("an introduction to the study of experimental medicine", "bernard"),
    ("the double helix", "watson"),
    ("molecular biology of the gene", "watson"),

    # ── History of medicine ────────────────────────────────────────────────────
    ("a history of medicine", "porter"),
    ("the greatest benefit to mankind", "porter"),

    # ── Epidemiology & public health ───────────────────────────────────────────
    ("snow on cholera", "snow"),
    ("report on the sanitary condition of the labouring population", "chadwick"),
    ("modern epidemiology", "rothman"),
    ("epidemiology an introduction", "rothman"),
    ("epidemiology in medicine", "hennekels buring"),
    ("public health administration", "winslow"),
    ("oxford textbook of public health", "detels"),

    # ── Tropical medicine ──────────────────────────────────────────────────────
    ("mansons tropical diseases", "manson cook"),
    ("manson s tropical diseases", "manson cook"),
    ("tropical diseases a practical guide", "cook zumla"),
    ("the prevention of malaria", "ross"),
    ("tropical medicine and hygiene", None),
    ("foundations of tropical medicine", "jawetz"),
    ("manual of tropical medicine", "hunter swartzwelder clyde"),
    ("essential malariology", "bruce chwatt gilles warhurst"),

    # ── Parasitology ───────────────────────────────────────────────────────────
    ("foundations of parasitology", "roberts janovy nadler"),
    ("medical parasitology", "markell"),
    ("human parasitology", "bogitsh"),
    ("parasitic diseases", "despommier"),
    ("atlas of human parasitology", "ash orihel"),
    ("medical helminthology", None),
    ("medical entomology for students", "service"),
    ("vectors of human disease", "busvine"),
    ("mosquitoes of the world", "darsie ward"),
    ("biology of disease vectors", "marquardt"),

    # ── Bacteriology ──────────────────────────────────────────────────────────
    ("the germ theory of disease", "pasteur koch"),
    ("principles of bacteriology", "mackie mccartney topley wilson"),
    ("medical microbiology", "murray"),
    ("bacteriology and immunity", "topley wilson"),
    ("the bacteria", "gunsalus stanier"),

    # ── Virology ──────────────────────────────────────────────────────────────
    ("medical virology", "white fenner"),
    ("the pathogenesis of viral infections", "galasso merigan buchanan"),
    ("fields virology", "fields howley knipe"),
    ("an inquiry into the causes and effects of the variolae vaccinae", "jenner"),

    # ── Immunology ────────────────────────────────────────────────────────────
    ("cellular and molecular immunology", "abbas lichtman pillai"),
    ("the immune system", "parham"),

    # ── Narrative / social medicine ───────────────────────────────────────────
    ("and the band played on", "shilts"),

    # ── Internal medicine & clinical ──────────────────────────────────────────
    ("harrisons principles of internal medicine", "harrison loscalzo"),
    ("harrison s principles of internal medicine", "harrison loscalzo"),
    ("cecil textbook of medicine", "cecil goldman schafer"),
    ("principles and practice of medicine", "osler"),
    ("grays anatomy", "gray standring"),
    ("gray s anatomy", "gray standring"),
    ("atlas of human anatomy", "netter"),
    ("robbins pathologic basis of disease", "robbins kumar"),
    ("oxford handbook of clinical medicine", "longmore"),
    ("clinical examination", "macleod"),

    # ── Pathology ─────────────────────────────────────────────────────────────
    ("molecular pathology", "coleman tsongalis"),
    ("diagnostic pathology", "coulibaly"),

    # ── Ethics ────────────────────────────────────────────────────────────────
    ("principles of biomedical ethics", "beauchamp childress"),
    ("ethics and professionalism in medicine", None),
]

# Outbreak timeline events with keywords and Barnard classification gates
OUTBREAK_TIMELINE = [
    {
        "event": "First smallpox vaccination (Jenner)",
        "keywords": ["jenner", "variolae vaccinae", "smallpox vaccination", "cowpox inoculation"],
        "barnard_prefixes": ["KI"],
    },
    {
        "event": "Broad Street cholera outbreak / Cholera",
        "keywords": ["cholera", "john snow", "broad street", "vibrio cholerae", "el tor"],
        "barnard_prefixes": ["JK"],
    },
    {
        "event": "Discovery of TB bacteria (Koch) / Tuberculosis",
        "keywords": ["tuberculosis", "tubercle bacillus", "robert koch", "koch's bacillus", "mycobacterium tuberculosis"],
        "barnard_prefixes": ["JC"],
    },
    {
        "event": "Mosquito transmission of Malaria (Ross) / Malaria",
        "keywords": ["malaria", "ronald ross", "anopheles", "mosquito transmission of malaria", "plasmodium"],
        "barnard_prefixes": ["LF", "NO", "N", "ND", "NC"],
    },
    {
        "event": "Yellow fever transmission (Walter Reed) / Yellow fever",
        "keywords": ["yellow fever", "walter reed", "fievre jaune", "fiebre amarilla"],
        "barnard_prefixes": ["KPA"],
    },
    {
        "event": "Discovery of Chagas disease",
        "keywords": ["chagas", "trypanosoma cruzi", "doenca de chagas", "enfermedad de chagas"],
        "barnard_prefixes": ["LP", "LN"],
    },
    {
        "event": "1918 Influenza pandemic / Influenza",
        "keywords": ["influenza", "spanish flu", "1918 pandemic", "grippe"],
        "barnard_prefixes": ["KL"],
    },
    {
        "event": "Malaria eradication campaigns",
        "keywords": ["malaria eradication", "global malaria eradication", "eradication of malaria", "ddt malaria", "malaria campaign"],
        "barnard_prefixes": ["LF", "NO", "N", "ND", "NC"],
    },
    {
        "event": "Global smallpox eradication programme / Smallpox",
        "keywords": ["smallpox", "variola", "smallpox eradication", "pocken"],
        "barnard_prefixes": ["KI"],
    },
    {
        "event": "HIV/AIDS",
        "keywords": ["hiv", "aids", "sida", "human immunodeficiency virus", "acquired immunodeficiency", "acquired immune deficiency", "virus de l'immunodeficience"],
        "barnard_prefixes": ["KRC", "KR"],
    },
    {
        "event": "Global expansion of Dengue",
        "keywords": ["dengue"],
        "barnard_prefixes": ["KPD", "KP"],
    },
    {
        "event": "Mpox outbreaks",
        "keywords": ["mpox", "monkeypox"],
        "barnard_prefixes": ["KI"],
    },
    {
        "event": "Ebola outbreak in West Africa / Hemorrhagic fever",
        "keywords": ["ebola", "hemorrhagic fever", "haemorrhagic fever", "marburg"],
        "barnard_prefixes": ["KPH"],
    },
    {
        "event": "COVID-19 pandemic",
        "keywords": ["covid", "sars-cov", "coronavirus pandemic"],
        "barnard_prefixes": ["K"],
    },
]

# Regional terms: Congo and Belgium
CONGO_TERMS = [
    "congo", "belgian congo", "zaire", "belgique", "belgium",
    "kinshasa", "leopoldville", "brazzaville", "katanga"
]

# IRCB / ARSC institutional terms
IRCB_TERMS = [
    "ircb", "institut royal colonial belge", "royal belgian colonial institute",
    "koninklijk belgisch koloniaal instituut", "arsc", "academie royale des sciences coloniales",
    "royal academy of colonial sciences", "koninklijke academie voor koloniale wetenschappen"
]

# Conference and proceedings terms
CONFERENCE_TERMS = [
    "proceedings", "conference", "congres", "congrès", "congress", "congresso",
    "symposium", "colloque", "workshop", "abstracts", "anais", "arquivos",
    "conférence", "conferencia", "conferência", "meeting", "congresos",
    "congresso", "colloqui", "seminaire", "séminaire",
    "kongress", "konferenz", "tagung", "jahrestagung", "symposia",
]

# Tropical medicine and infectious disease keywords
TROPICAL_TERMS = [
    "tropical", "malaria", "leprosy", "leprol", "lèpre", "lepra", "lepre", "parasit",
    "infectious", "infecti", "colonial", "africa", "afrique", "african",
    "congo", "asia", "latin america", "developing", "health", "santé", "sante",
    "hygiene", "hygiène", "epidemiol", "immunol", "bacteriol", "virol",
    "entomol", "helminth", "schistosom", "trypanosoma", "filaria",
    "microbiolog", "chemotherap", "pharmacol", "nutrition", "medic",
    "tropenmedizin", "tropen", "geneeskunde", "gezondheid", "salud",
    "coccidi", "protozoa", "helminth", "nematod", "cestod", "trematod",
]

# Dedication, liber amicorum, and commemorative edition terms
DEDICATION_TERMS = [
    "liber amicorum", "festschrift",
    "dédié à", "dedie a", "dedicated to", "ter ere van", "ter gelegenheid van",
    "à l'occasion de", "a l'occasion de", "bei gelegenheit",
    "hommage à", "hommage a", "in honour of", "in honor of",
    "in memoriam", "à la mémoire de", "à la memoire de",
    "anniversaire", "anniversary", "jubileum", "jubilé", "jubile",
    "commemorat", "commémorat", "gedenkboek", "gedenkschrift",
    "centenaire", "centenario", "centenário", "centennial", "centenary",
    "comemorativ", "conmemorat",
]

# Africa-specific country and regional terms
AFRICA_TERMS = [
    "africa", "african", "afrique", "africain",
    # Specific countries
    "ghana", "gambia", "gambian", "nigeria", "nigerian", "kenya", "kenyan",
    "tanzania", "tanzanian", "uganda", "ugandan", "ethiopia", "ethiopian",
    "senegal", "senegalese", "mali", "malian", "niger", "cameroon", "cameroonian",
    "mozambique", "zimbabwe", "zambia", "malawi", "rwanda", "burundi",
    "somalia", "sudan", "south africa", "namibia", "botswana", "lesotho",
    "sierra leone", "liberia", "guinea", "ivory coast", "côte d'ivoire",
    "cote d ivoire", "togo", "benin", "burkina", "angola", "madagascar",
    "mauritius", "reunion", "egypt", "nigeria", "chad", "tchad",
    # Major cities
    "abidjan", "dakar", "nairobi", "kampala", "dar es salaam", "lagos",
    "accra", "bamako", "ouagadougou", "niamey", "lome", "cotonou",
]

# WHO and FAO organization terms
WHO_FAO_TERMS = [
    "world health organization", "world health organisation",
    "food and agriculture organization", "food and agriculture organisation",
    "wereldgezondheidsorganisatie", "organisation mondiale de la sante",
    "organisation mondiale de la santé", "organización mundial de la salud"
]

# WHO and FAO short codes (matched as whole words)
WHO_FAO_SHORT = ["who", "fao", "oms", "oas"]

# Specialist tropical medicine publishers and institutions
SPECIALIST_PUBLISHERS = [
    # ITG / ITM (Antwerp)
    "instituut voor tropische geneeskunde", "institut de medecine tropicale",
    "institute of tropical medicine", "prins leopold instituut", "prince leopold institute",
    "institut de medecine tropicale prince",
    # Other tropical medicine schools
    "london school of hygiene and tropical medicine", "london school of hygiene",
    "liverpool school of tropical medicine",
    "bernhard-nocht-institut", "swiss tropical institute",
    "mahidol university, faculty of tropical medicine",
    # African research institutes
    "musee royal de l", "musee royal du congo", "royal museum for central africa",
    "academie royale des sciences coloniales", "academie royale des sciences d",
    "institut royal colonial belge", "arsom", "arsc", "ircb",
    "orstom", "iemvt", "occge", "oceac", "fometro", "berps",
    "international livestock centre for africa", "ilca",
    # International tropical disease programmes
    "undp/world bank/who special programme", "unicef/undp/world bank/who",
    "special programme for research and training in tropical diseases",
    "division of control of tropical diseases",
    # Veterinary tropical medicine
    "centre for tropical veterinary medicine",
    "medecine veterinaire des pays tropicaux",
    "tropical products institute", "tropical health technology",
    # Other specialist
    "royal society of tropical medicine",
    "american society of tropical medicine", "bureau of hygiene and tropical diseases",
    "ross institute of tropical hygiene",
    # KIT Amsterdam (Royal Tropical Institute)
    "koninklijk instituut voor de tropen", "royal tropical institute",
    "institut royal des tropiques", "kit amsterdam",
]

# Manual, guide, and handbook keywords
MANUAL_GUIDE_TERMS = [
    "manual", "guide", "handbook", "guideline", "directory",
    "formulary", "protocol", "procedure", "curriculum"
]
