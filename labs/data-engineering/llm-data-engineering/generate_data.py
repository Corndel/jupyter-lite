"""Generate all data files for the llm-data-engineering module.

Creates:
  - data/bl_digitised_texts_raw.csv  (~2000 rows of deliberately dirty texts)
  - data/bl_research_papers.json     (5 long-form research papers)
  - data/bl_chunks_with_embeddings.parquet  (~500 chunks with TF-IDF embeddings)
  - data/bl_embeddings.npy           (same embeddings as numpy array)
"""

import csv
import json
import random
import re
import textwrap
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from sklearn.feature_extraction.text import TfidfVectorizer

random.seed(42)
np.random.seed(42)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SOURCE_TYPES = ["manuscript", "research_paper", "exhibition_guide", "historical_record", "letter"]

# Realistic British names for authors
AUTHORS = [
    "Dr. Eleanor Whitfield", "Prof. James Hartley", "Dr. Ananya Krishnamurthy",
    "Prof. Margaret Cavendish-Scott", "Dr. Thomas Blackwood", "Prof. Sarah Llewellyn",
    "Dr. Benjamin Ashworth", "Dr. Fatima Al-Rashid", "Prof. Richard Pemberton",
    "Dr. Catherine Okonkwo", "Prof. William Herschel-Morton", "Dr. Mei-Lin Chen",
    "Prof. David Attenborough-Clarke", "Dr. Priya Patel", "Prof. George Stephenson-Wright",
    "Dr. Hannah Westcott", "Dr. Oluwaseun Adeyemi", "Prof. Elizabeth Montagu",
    "Dr. Robert Fitzroy-Campbell", "Dr. Amara Osei",
]

# Fake emails and phone numbers for PII
FAKE_EMAILS = [
    "j.smith@britishlibrary.uk", "curator@bl.uk", "research@humanities.ox.ac.uk",
    "m.jones@cam.ac.uk", "admin@nationalarchives.gov.uk", "a.patel@ucl.ac.uk",
    "info@victorianstudies.org", "contact@medievalhistory.co.uk",
    "librarian@bodleian.ox.ac.uk", "help@digitalcollections.bl.uk",
]

FAKE_PHONES = [
    "+44 20 7946 0958", "020 7946 0123", "+44 (0)20 7123 4567",
    "0207 946 0987", "+44 161 496 0000", "0131 496 0321",
]

# Headers/footers that appear in digitised pages
HEADERS_FOOTERS = [
    "Page {n} of {total} -- British Library Digital Collection",
    "--- British Library Digitised Archive --- Page {n}",
    "BL Digital Collections | Catalogue Ref: {ref} | Page {n}",
    "[Digitised by the British Library, {year}]",
]

# Catalogue references
CATALOGUE_REFS = [
    "BL/MS/1234", "BL/RP/5678", "BL/EG/9012", "BL/HR/3456",
    "BL/LT/7890", "BL/MS/2345", "BL/RP/6789", "BL/EG/0123",
]

# ---------------------------------------------------------------------------
# Text content — realistic British Library topics
# ---------------------------------------------------------------------------

MEDIEVAL_TEXTS = [
    "The feudal system in England following the Norman Conquest of 1066 fundamentally restructured land ownership. William the Conqueror distributed vast estates to his loyal barons, who in turn granted smaller holdings to knights in exchange for military service. This hierarchical arrangement persisted for centuries and shaped the English countryside as we know it today.",
    "The Domesday Book, commissioned by William the Conqueror in 1085, represents the most comprehensive survey of medieval England. Its two volumes catalogue landholdings, livestock, and resources across the entire kingdom. Scholars continue to mine its pages for insights into eleventh-century economic life.",
    "The Black Death reached England in June 1348, arriving through the port of Melcombe Regis in Dorset. Within eighteen months, between a third and half of the population had perished. The resulting labour shortage transformed the economic landscape, giving surviving peasants unprecedented bargaining power.",
    "Medieval monasteries served as centres of learning, agriculture, and healthcare. The great abbeys of Glastonbury, Canterbury, and Fountains maintained extensive libraries, brewed ale, and tended physic gardens. Their dissolution under Henry VIII in the 1530s dispersed centuries of accumulated knowledge.",
    "The Magna Carta, sealed at Runnymede in 1215, established the principle that the king was subject to the law. Though many of its sixty-three clauses addressed specific baronial grievances, its broader legacy shaped constitutional governance across the English-speaking world.",
    "Trade routes connecting medieval England to the Continent ran through the great wool towns of the Cotswolds and East Anglia. English wool was prized across Flanders and Italy, and the profits funded magnificent churches that still dominate the landscape of Suffolk and Norfolk.",
    "The Peasants' Revolt of 1381, sparked by the imposition of a poll tax, saw rebels march on London under the leadership of Wat Tyler. They burned the Savoy Palace, opened the prisons, and briefly held the capital before the revolt was suppressed through a mixture of concession and treachery.",
    "Chaucer's Canterbury Tales, composed in the late fourteenth century, provides an unrivalled portrait of medieval English society. From the Knight to the Wife of Bath, each pilgrim represents a distinct social stratum, and their tales reveal the preoccupations, prejudices, and pleasures of the age.",
    "The Bayeux Tapestry, though Norman in origin, tells the story of the English succession crisis of 1066. Its seventy metres of embroidered linen depict the death of Edward the Confessor, Harold's oath to William, and the decisive Battle of Hastings.",
    "Medieval English castles evolved from simple motte-and-bailey constructions to sophisticated concentric fortifications. Edward I's castles in Wales, including Caernarfon, Conwy, and Harlech, represent the pinnacle of military architecture and served as instruments of colonial control.",
    "The Venerable Bede, writing in the monastery of Jarrow in the early eighth century, produced the Ecclesiastical History of the English People. His work remains the primary source for early Anglo-Saxon history and established conventions of dating that persist to this day.",
    "Pilgrimage was central to medieval religious life. The shrine of Thomas Becket at Canterbury drew visitors from across Europe, while lesser-known sites such as Walsingham in Norfolk attracted thousands of devotees annually seeking miraculous cures.",
    "The wool trade financed the construction of some of England's finest perpendicular Gothic churches. The so-called wool churches of the Cotswolds, with their soaring towers and ornate carvings, stand as monuments to the prosperity generated by the medieval textile industry.",
    "Anglo-Saxon England possessed a sophisticated literary culture. The epic poem Beowulf, composed sometime between the eighth and eleventh centuries, survives in a single manuscript held at the British Library. Its 3,182 lines of alliterative verse narrate the hero's battles against three supernatural foes.",
    "The medieval guild system regulated trade and craftsmanship in English towns. Each guild controlled apprenticeships, set quality standards, and maintained a monopoly over its particular craft. The Worshipful Companies of the City of London trace their origins to these medieval organisations.",
]

TUDOR_TEXTS = [
    "Henry VIII's break with Rome in 1534 was driven less by theology than by dynastic necessity. His desire for a male heir, combined with the Pope's refusal to annul his marriage to Catherine of Aragon, set in motion the English Reformation and the establishment of the Church of England.",
    "The dissolution of the monasteries between 1536 and 1541 represented the greatest redistribution of land since the Norman Conquest. The Crown seized monastic properties valued at roughly one-fifth of all land in England, selling much of it to the rising gentry class.",
    "Elizabeth I's reign saw England emerge as a maritime power. The defeat of the Spanish Armada in 1588, though aided by storms as much as naval skill, established English confidence at sea and opened the way for colonial ventures in the following century.",
    "The Tudor court was a theatre of power. Henry VIII's Palace of Nonsuch, now entirely vanished, was designed to rival the grandeur of Fontainebleau. Its elaborate stucco panels, intricate gardens, and sheer scale were calculated to project royal magnificence.",
    "Sir Francis Drake's circumnavigation of the globe between 1577 and 1580 combined exploration with piracy. His raids on Spanish treasure ships in the Pacific yielded an extraordinary return on investment, and Elizabeth I took a personal share of the profits.",
    "The Elizabethan Poor Laws of 1597 and 1601 established the principle that local parishes bore responsibility for their destitute inhabitants. This framework, however imperfect, endured for over two centuries and laid the groundwork for the modern welfare state.",
    "Shakespeare's Globe Theatre, built on the south bank of the Thames in 1599, could hold up to three thousand spectators. The groundlings paid a penny to stand in the open yard, while wealthier patrons occupied the covered galleries above.",
    "Thomas More's Utopia, published in 1516, imagined an ideal society on a fictional island. Its critiques of English social injustice, wrapped in layers of irony and ambiguity, continue to provoke scholarly debate about More's true intentions.",
    "Tudor navigation relied on a combination of dead reckoning, celestial observation, and coastal pilotage. The development of the astrolabe and the cross-staff improved latitude measurement, but longitude remained essentially guesswork until the eighteenth century.",
    "The Mary Rose, Henry VIII's flagship, sank in the Solent in 1545 while engaging a French invasion fleet. Raised from the seabed in 1982, she is now preserved in a dedicated museum in Portsmouth, offering an extraordinary window into Tudor maritime life.",
    "The English Renaissance saw a flowering of literature, music, and architecture. The poetry of Edmund Spenser, the music of Thomas Tallis, and the great prodigy houses of the Elizabethan era all drew on Continental influences while developing a distinctively English character.",
    "The Tudor dynasty's legitimacy was always contested. Henry VII's claim to the throne through his mother, Margaret Beaufort, was tenuous at best. The Tudors compensated through elaborate genealogies tracing their descent back to King Arthur and the ancient Britons.",
]

INDUSTRIAL_TEXTS = [
    "The spinning jenny, patented by James Hargreaves in 1770, multiplied the productivity of a single spinner eightfold. Within decades, the cottage industry of textile production had migrated to purpose-built factories powered first by water and then by steam.",
    "Isambard Kingdom Brunel's Great Western Railway, completed in 1841, linked London to Bristol in just under two hours. Brunel's insistence on a broad gauge of seven feet offered a smoother ride but ultimately lost out to George Stephenson's narrower standard.",
    "The Great Exhibition of 1851, housed in Joseph Paxton's Crystal Palace in Hyde Park, showcased the industrial might of the British Empire. Over six million visitors marvelled at machinery, raw materials, and manufactured goods from around the world.",
    "The factory system concentrated workers in purpose-built mills, fundamentally altering the rhythm of daily life. Clock time replaced seasonal time, the factory bell supplanted the church bell, and the distinction between home and workplace became absolute.",
    "Child labour in the cotton mills of Lancashire prompted a series of Factory Acts beginning in 1833. The earliest legislation limited the working hours of children under thirteen, though enforcement remained patchy and evasion widespread for decades.",
    "The Bridgewater Canal, opened in 1761, halved the price of coal in Manchester and demonstrated the commercial potential of inland waterways. Within fifty years, a network of canals connected the major industrial centres of England.",
    "James Watt's improvements to the Newcomen steam engine, particularly the separate condenser patented in 1769, transformed an inefficient pumping device into a versatile source of rotary power. Watt's partnership with the Birmingham manufacturer Matthew Boulton commercialised the invention.",
    "The Luddite movement of 1811 to 1816 saw textile workers in the Midlands and North of England destroy machinery that they believed threatened their livelihoods. The government responded with draconian measures, including making machine-breaking a capital offence.",
    "The railway navvies who built Britain's rail network were among the hardest-worked labourers in the country. Working with pick, shovel, and wheelbarrow, they shifted millions of tonnes of earth and rock, often in appalling conditions and at considerable risk to life.",
    "Iron production in Britain increased twentyfold between 1750 and 1850, driven by innovations such as Abraham Darby's coke smelting process and Henry Cort's puddling and rolling technique. Cheap iron made possible bridges, railways, and the structural frames of factories.",
    "The Stockton and Darlington Railway, opened in 1825, was the world's first public railway to use steam locomotion. George Stephenson's Locomotion No. 1 hauled a mixed train of coal wagons and passenger carriages at speeds of up to fifteen miles per hour.",
    "Manchester's population grew from around 25,000 in 1770 to over 300,000 by 1850. This explosive growth, driven by the cotton industry, created immense challenges of sanitation, housing, and public order that the existing institutions of local government were ill-equipped to handle.",
]

VICTORIAN_TEXTS = [
    "The Great Stink of 1858 forced Parliament to act on London's sewage crisis. Joseph Bazalgette's ambitious network of intercepting sewers, completed in the 1870s, diverted waste downstream and transformed public health in the capital.",
    "Charles Darwin's On the Origin of Species, published in 1859, provoked fierce debate but gradually reshaped understanding of the natural world. The British Library holds Darwin's personal copy, annotated in his own hand with corrections and additions.",
    "The Victorian workhouse, established under the New Poor Law of 1834, was deliberately designed to deter all but the most desperate. Families were separated, meals were monotonous, and inmates wore uniforms. Dickens drew on these conditions for Oliver Twist.",
    "Florence Nightingale's statistical work during and after the Crimean War was as significant as her nursing reforms. Her polar area diagrams demonstrated that most soldiers died of preventable disease rather than battle wounds, compelling the War Office to improve sanitary conditions.",
    "The Great Exhibition's profits funded the establishment of the South Kensington museums, including what would become the Victoria and Albert Museum and the Natural History Museum. Prince Albert's vision of a cultural quarter in South Kensington continues to shape London.",
    "The Victorian novel served as both entertainment and social commentary. Dickens serialised his tales of poverty and injustice, Eliot explored the moral complexities of provincial life, and Hardy documented the decline of rural England in the face of modernity.",
    "The expansion of the railway network in the 1840s and 1850s necessitated the standardisation of timekeeping across Britain. Before railway time, each town kept its own local time based on the position of the sun. Greenwich Mean Time was adopted nationally in 1880.",
    "The British Museum's reading room, opened in 1857, provided a space where Karl Marx, Virginia Woolf, and countless other scholars conducted their research. Its great domed ceiling, spanning 42 metres, was an engineering marvel of its day.",
    "Queen Victoria's reign saw the British Empire reach its greatest territorial extent. By the end of the nineteenth century, roughly a quarter of the world's land surface and population fell under British control, an empire on which, as the saying went, the sun never set.",
    "The Public Health Act of 1875 consolidated decades of sanitary legislation, requiring local authorities to provide clean water, sewerage, and refuse collection. It marked a decisive shift towards government intervention in matters previously left to individual initiative.",
    "The Victorian obsession with classification extended from the natural world to human society. The census, introduced in 1801 but greatly expanded under Victoria, attempted to categorise every inhabitant by occupation, age, marital status, and place of birth.",
    "Photography transformed Victorian culture. From the daguerreotype portraits of the 1840s to the snapshot cameras of the 1890s, the medium democratised image-making and created an entirely new relationship between individuals and their visual record.",
]

NATURAL_HISTORY_TEXTS = [
    "The Natural History Museum's collection of over eighty million specimens includes fossils, minerals, botanical samples, and zoological preparations. Many were acquired during the great age of Victorian exploration and continue to support scientific research today.",
    "Sir Hans Sloane's collection of natural curiosities, bequeathed to the nation in 1753, formed the nucleus of what would become both the British Museum and the Natural History Museum. His catalogue of Jamaican plants remains a foundational text of tropical botany.",
    "Alfred Russel Wallace independently conceived the theory of natural selection while suffering from malaria in the Malay Archipelago. His paper, presented jointly with Darwin's at the Linnean Society in 1858, received remarkably little immediate attention.",
    "The herbarium at the Royal Botanic Gardens, Kew, houses over seven million preserved plant specimens. Each is mounted on a standard sheet, labelled with its scientific name, collector, and location. Together they form a reference library of the world's flora.",
    "Mary Anning's fossil discoveries at Lyme Regis in the early nineteenth century transformed understanding of prehistoric life. Her finds included the first correctly identified ichthyosaur skeleton and an almost complete plesiosaur, yet as a woman and an outsider she received little formal recognition in her lifetime.",
    "Joseph Banks accompanied Captain Cook on his first voyage to the Pacific in 1768. The botanical specimens he collected in Australia, Tahiti, and New Zealand formed the basis of his extraordinary herbarium and helped establish Kew as a centre of botanical science.",
    "The dodo, native to Mauritius and extinct by the 1680s, survives in the collections of the Natural History Museum as a handful of bones and a single preserved head. Its disappearance has become a universal symbol of human-caused extinction.",
    "Darwin's finches, collected during the voyage of the Beagle in the 1830s, provided crucial evidence for the theory of evolution by natural selection. The variation in beak shape across the Galapagos islands suggested adaptation to different food sources.",
    "The geological collections at the British Museum include specimens gathered by William Smith, the father of English geology. His 1815 geological map of England and Wales was the first of its kind and demonstrated that rock strata could be identified by their characteristic fossils.",
    "Victorian naturalists were prolific collectors, and their expeditions to Africa, Asia, and South America yielded enormous quantities of specimens. The ethics of this collecting practice are now reconsidered, as many collections were assembled under colonial conditions.",
]

EARLY_SCIENCE_TEXTS = [
    "Isaac Newton's Principia Mathematica, published in 1687, laid the foundations of classical mechanics. The British Library holds a first edition, one of perhaps four hundred copies printed by Samuel Pepys's printer in an initial run that nearly didn't happen due to financial difficulties.",
    "Robert Hooke's Micrographia of 1665 presented the first detailed illustrations of objects viewed through a microscope. His drawing of a flea, magnified and rendered in exquisite detail, caused a sensation and popularised the instrument among the educated public.",
    "The Royal Society, founded in 1660, provided a forum for the exchange of scientific ideas through its meetings and its journal, the Philosophical Transactions. Early fellows included Newton, Hooke, Boyle, and Wren, though the society also admitted gentlemen amateurs.",
    "Michael Faraday's experiments at the Royal Institution in the 1830s established the principles of electromagnetic induction. His discovery that a changing magnetic field produces an electric current underpins every electric generator and transformer in use today.",
    "Charles Babbage's Difference Engine, designed in the 1820s, was intended to mechanise the calculation of mathematical tables. Though never completed in his lifetime, a full-scale working model was constructed from his original plans at the Science Museum in 1991.",
    "Ada Lovelace's notes on Babbage's Analytical Engine, published in 1843, contain what is widely regarded as the first computer programme. Her insight that the machine could manipulate symbols according to rules, not merely calculate numbers, was decades ahead of its time.",
    "The discovery of oxygen is variously attributed to Carl Wilhelm Scheele, Joseph Priestley, and Antoine Lavoisier. Priestley, working in Leeds and later in Birmingham, isolated the gas in 1774 by heating mercuric oxide and noted that a candle burned more brightly in it.",
    "Edward Jenner's development of the smallpox vaccine in 1796, using material from cowpox lesions, was initially met with scepticism and ridicule. Within a decade, vaccination had spread across Europe, and smallpox, which had killed millions, was on the path to eventual eradication.",
    "The transit of Venus across the face of the sun in 1769 prompted international scientific expeditions to observe the event from multiple locations. Captain Cook's voyage to Tahiti was primarily a scientific mission to measure the transit, with exploration as a secondary objective.",
    "William Herschel's discovery of Uranus in 1781 was the first identification of a new planet since antiquity. Working from his garden in Bath with a homemade reflecting telescope, Herschel initially believed he had found a comet.",
]

LITERARY_TEXTS = [
    "The Bronte sisters published their first collection of poetry in 1846 under the pseudonyms Currer, Ellis, and Acton Bell. The volume sold only two copies, yet within a year Charlotte's Jane Eyre had become a sensation and Emily's Wuthering Heights had bewildered and fascinated critics in equal measure.",
    "Samuel Johnson's Dictionary of the English Language, published in 1755, was the most comprehensive English dictionary of its era. Johnson worked largely alone, defining over 42,000 words with characteristic wit: his definition of oats as 'a grain which in England is generally given to horses, but in Scotland supports the people' is still quoted.",
    "The Romantic poets transformed English literature in the early nineteenth century. Wordsworth and Coleridge's Lyrical Ballads of 1798 rejected the formal diction of the eighteenth century in favour of the language of ordinary speech, setting a new direction for poetry.",
    "Virginia Woolf's experiments with stream-of-consciousness narrative in Mrs Dalloway and To the Lighthouse challenged conventional storytelling. Her essays on the craft of writing remain essential reading for anyone interested in the relationship between form and meaning.",
    "The British Library's collection of literary manuscripts includes drafts by Jane Austen, the Brontes, and James Joyce. These working documents reveal the creative process: deletions, insertions, second thoughts, and moments of inspiration captured in ink on paper.",
    "George Orwell's Nineteen Eighty-Four, published in 1949, drew on the totalitarian regimes of the twentieth century to imagine a future of perpetual surveillance and linguistic manipulation. Its vocabulary -- Big Brother, doublethink, thoughtcrime -- has entered everyday language.",
    "The Bloomsbury Group, centred on the household of Virginia and Leonard Woolf, brought together writers, artists, and intellectuals who challenged Victorian conventions of art and morality. Their influence on English literary and cultural life extended far beyond their relatively small number.",
    "John Milton's Paradise Lost, composed while the poet was blind and in political disgrace, retells the Biblical story of the Fall with extraordinary ambition and psychological depth. Its opening lines, invoking the 'great argument' to 'justify the ways of God to men', remain among the most famous in English literature.",
    "The Gothic novel emerged in the late eighteenth century with Horace Walpole's The Castle of Otranto and reached its zenith with Ann Radcliffe's The Mysteries of Udolpho. The genre's preoccupation with ruins, secrets, and the supernatural reflected anxieties about the pace of social change.",
    "Dickens's public readings, which he performed across Britain and America in the 1850s and 1860s, were theatrical events that drew enormous crowds. His reading of the murder of Nancy from Oliver Twist was so intense that audience members reportedly fainted.",
]

ART_HISTORY_TEXTS = [
    "The Pre-Raphaelite Brotherhood, founded in 1848 by Dante Gabriel Rossetti, John Everett Millais, and William Holman Hunt, rejected what they saw as the formulaic conventions of academic painting. Their vivid colours, meticulous detail, and literary subjects were initially denounced by critics.",
    "J.M.W. Turner's later paintings, with their dissolving forms and luminous colour, anticipated Impressionism by several decades. His bequest to the nation included nearly 300 oil paintings and over 30,000 works on paper, now housed in the Clore Gallery at Tate Britain.",
    "William Morris's Arts and Crafts movement sought to revive traditional craftsmanship in the face of industrial mass production. His wallpaper designs, textiles, and typefaces combined medieval aesthetics with a socialist vision of dignified labour.",
    "The Elgin Marbles, removed from the Parthenon by Lord Elgin in the early nineteenth century, remain a source of diplomatic tension between Britain and Greece. Their display in the British Museum raises ongoing questions about the ethics of cultural property and repatriation.",
    "Henry Moore's monumental sculptures, with their organic forms and pierced surfaces, drew on the collections of the British Museum. His reclining figures, installed in landscapes across the world, established a distinctly British contribution to international modernism.",
    "The illuminated manuscripts of medieval Britain represent some of the finest examples of European book art. The Lindisfarne Gospels, created around 700 CE on the island of Lindisfarne, combine Celtic, Germanic, and Mediterranean decorative traditions in pages of breathtaking complexity.",
    "John Constable's landscapes of the Suffolk countryside, particularly The Hay Wain and Dedham Vale, established a tradition of English landscape painting rooted in direct observation. His cloud studies, painted en plein air, were pioneering exercises in atmospheric realism.",
    "The Royal Academy of Arts, founded in 1768, provided a framework for artistic education and exhibition in Britain. Its annual Summer Exhibition, still held today, offered artists a crucial opportunity to display their work and attract patrons.",
    "The Bayeux Tapestry, though technically an embroidery, is one of the most important visual records of medieval history. Its narrative of the Norman Conquest unfolds across nearly seventy metres of linen, combining vivid imagery with a sense of dramatic momentum.",
    "Barbara Hepworth's abstract sculptures, carved in wood and stone, explored the relationship between form, space, and landscape. Working from her studio in St Ives, Cornwall, she developed a vocabulary of pierced and hollow forms that became synonymous with British modernism.",
]

ALL_TOPIC_TEXTS = {
    "medieval": MEDIEVAL_TEXTS,
    "tudor": TUDOR_TEXTS,
    "industrial": INDUSTRIAL_TEXTS,
    "victorian": VICTORIAN_TEXTS,
    "natural_history": NATURAL_HISTORY_TEXTS,
    "early_science": EARLY_SCIENCE_TEXTS,
    "literary": LITERARY_TEXTS,
    "art_history": ART_HISTORY_TEXTS,
}

TOPIC_TITLES = {
    "medieval": [
        "The Feudal System in Post-Conquest England",
        "The Domesday Survey: A Census of Norman England",
        "The Black Death and Its Economic Consequences",
        "Monastic Life and Learning in Medieval England",
        "Magna Carta: Origins and Legacy",
        "Wool Trade and Prosperity in Medieval England",
        "The Peasants' Revolt of 1381",
        "Chaucer and the Social World of the Canterbury Tales",
        "The Bayeux Tapestry as Historical Record",
        "Castle Architecture from Motte-and-Bailey to Concentric",
        "Bede and the Origins of English History",
        "Pilgrimage in Medieval England",
        "Wool Churches of the Cotswolds",
        "Beowulf and Anglo-Saxon Literature",
        "The Medieval Guild System",
    ],
    "tudor": [
        "Henry VIII and the Break with Rome",
        "The Dissolution of the Monasteries",
        "Elizabeth I and the Defeat of the Armada",
        "The Tudor Court: Architecture and Display",
        "Drake's Circumnavigation, 1577-1580",
        "The Elizabethan Poor Laws",
        "Shakespeare's Globe Theatre",
        "Thomas More and the Idea of Utopia",
        "Tudor Navigation and Exploration",
        "The Mary Rose: A Tudor Warship Recovered",
        "The English Renaissance in Literature and Music",
        "Tudor Legitimacy and the Myth of Arthur",
    ],
    "industrial": [
        "The Spinning Jenny and the Factory System",
        "Brunel's Great Western Railway",
        "The Great Exhibition of 1851",
        "Factory Life and the Rhythm of Industrial Time",
        "Child Labour and the Factory Acts",
        "The Canal Age and Inland Navigation",
        "James Watt and the Steam Engine",
        "The Luddite Movement",
        "The Railway Navvies",
        "Iron Production and the Industrial Revolution",
        "The Stockton and Darlington Railway",
        "Manchester: Growth of an Industrial City",
    ],
    "victorian": [
        "The Great Stink and London's Sewers",
        "Darwin's On the Origin of Species",
        "The Victorian Workhouse",
        "Florence Nightingale: Nurse and Statistician",
        "South Kensington and the Legacy of 1851",
        "The Victorian Novel as Social Commentary",
        "Railway Time and the Standardisation of Clocks",
        "The British Museum Reading Room",
        "The British Empire at Its Zenith",
        "Public Health Legislation in Victorian Britain",
        "The Victorian Census and the Urge to Classify",
        "Photography and Victorian Culture",
    ],
    "natural_history": [
        "The Natural History Museum Collections",
        "Hans Sloane and the Origins of the British Museum",
        "Alfred Russel Wallace and Natural Selection",
        "The Herbarium at Kew Gardens",
        "Mary Anning: Fossil Hunter of Lyme Regis",
        "Joseph Banks and the Botany of the Pacific",
        "The Dodo: Extinction and Memory",
        "Darwin's Finches and Adaptive Radiation",
        "William Smith and the Geological Map of England",
        "Victorian Collecting and Colonial Ethics",
    ],
    "early_science": [
        "Newton's Principia Mathematica",
        "Hooke's Micrographia and the Microscope",
        "The Royal Society and the Birth of Modern Science",
        "Faraday and Electromagnetic Induction",
        "Babbage's Difference Engine",
        "Ada Lovelace and the First Programme",
        "The Discovery of Oxygen",
        "Jenner and the Smallpox Vaccine",
        "The Transit of Venus, 1769",
        "Herschel's Discovery of Uranus",
    ],
    "literary": [
        "The Bronte Sisters: From Pseudonym to Fame",
        "Johnson's Dictionary of the English Language",
        "The Romantic Poets and Lyrical Ballads",
        "Virginia Woolf and Stream of Consciousness",
        "Literary Manuscripts at the British Library",
        "Orwell's Nineteen Eighty-Four",
        "The Bloomsbury Group",
        "Milton's Paradise Lost",
        "The Gothic Novel",
        "Dickens's Public Readings",
    ],
    "art_history": [
        "The Pre-Raphaelite Brotherhood",
        "Turner and the Anticipation of Impressionism",
        "William Morris and the Arts and Crafts Movement",
        "The Elgin Marbles Controversy",
        "Henry Moore's Monumental Sculptures",
        "Illuminated Manuscripts of Medieval Britain",
        "Constable and the English Landscape",
        "The Royal Academy of Arts",
        "The Bayeux Tapestry as Visual Narrative",
        "Barbara Hepworth and British Modernism",
    ],
}

YEAR_RANGES = {
    "medieval": (1850, 2023),
    "tudor": (1870, 2023),
    "industrial": (1880, 2023),
    "victorian": (1890, 2023),
    "natural_history": (1900, 2023),
    "early_science": (1910, 2023),
    "literary": (1920, 2023),
    "art_history": (1930, 2023),
}


def add_html_artefacts(text: str) -> str:
    """Inject HTML tags into text."""
    sentences = text.split(". ")
    if len(sentences) >= 2:
        idx = random.randint(0, len(sentences) - 1)
        tag = random.choice(["<p>", "<em>", "<br/>", "<span>", "<div>"])
        close_tag = tag.replace("<", "</").replace("/>", ">")
        if tag == "<br/>":
            sentences[idx] = sentences[idx] + "<br/>"
        else:
            sentences[idx] = tag + sentences[idx] + close_tag
    return ". ".join(sentences)


def add_invisible_chars(text: str) -> str:
    """Inject non-breaking spaces and zero-width spaces."""
    words = text.split(" ")
    for _ in range(random.randint(2, 6)):
        idx = random.randint(0, len(words) - 1)
        char = random.choice(["\xa0", "\u200b"])
        words[idx] = words[idx] + char
    return " ".join(words)


def add_ocr_artefacts(text: str) -> str:
    """Simulate OCR errors: rn->m, l->1, random linebreaks."""
    replacements = [
        ("rn", "m"),     # common OCR error
        ("l", "1"),      # l -> 1
        ("cl", "d"),     # cl -> d
    ]
    rep_type, rep_val = random.choice(replacements)
    # Apply only once or twice to avoid destroying readability
    count = 0
    result = []
    for word in text.split(" "):
        if rep_type in word.lower() and count < 2 and random.random() < 0.3:
            word = word.replace(rep_type, rep_val, 1)
            count += 1
        result.append(word)
    text = " ".join(result)

    # Random linebreak
    if random.random() < 0.3:
        words = text.split(" ")
        if len(words) > 5:
            idx = random.randint(2, len(words) - 3)
            words[idx] = words[idx] + "\n"
            text = " ".join(words)
    return text


def add_pii(text: str) -> str:
    """Add fake PII (email or phone) to some texts."""
    addition = random.choice([
        f"For enquiries contact {random.choice(FAKE_EMAILS)}",
        f"Contact: {random.choice(FAKE_PHONES)}",
        f"Digitised by {random.choice(FAKE_EMAILS)} on behalf of the British Library",
        f"For access requests, email {random.choice(FAKE_EMAILS)} or call {random.choice(FAKE_PHONES)}",
    ])
    return text + " " + addition


def add_header_footer(text: str, page_num: int = None) -> str:
    """Add British Library header/footer."""
    if page_num is None:
        page_num = random.randint(1, 200)
    total = page_num + random.randint(5, 50)
    template = random.choice(HEADERS_FOOTERS)
    header = template.format(
        n=page_num, total=total, ref=random.choice(CATALOGUE_REFS),
        year=random.randint(2005, 2023)
    )
    if random.random() < 0.5:
        return header + "\n\n" + text
    else:
        return text + "\n\n" + header


def corrupt_text(text: str) -> str:
    """Apply a random combination of corruption strategies."""
    corruptions = []

    # Always apply at least one corruption
    if random.random() < 0.35:
        corruptions.append("html")
    if random.random() < 0.40:
        corruptions.append("invisible")
    if random.random() < 0.25:
        corruptions.append("ocr")
    if random.random() < 0.15:
        corruptions.append("pii")
    if random.random() < 0.30:
        corruptions.append("header")

    # Ensure at least one corruption
    if not corruptions:
        corruptions.append(random.choice(["html", "invisible", "ocr", "header"]))

    for c in corruptions:
        if c == "html":
            text = add_html_artefacts(text)
        elif c == "invisible":
            text = add_invisible_chars(text)
        elif c == "ocr":
            text = add_ocr_artefacts(text)
        elif c == "pii":
            text = add_pii(text)
        elif c == "header":
            text = add_header_footer(text)

    return text


# ---------------------------------------------------------------------------
# Generate bl_digitised_texts_raw.csv
# ---------------------------------------------------------------------------

def generate_digitised_texts(n: int = 2000) -> list[dict]:
    """Generate ~2000 rows of dirty digitised text data."""
    rows = []
    topics = list(ALL_TOPIC_TEXTS.keys())

    for i in range(n):
        topic = random.choice(topics)
        texts = ALL_TOPIC_TEXTS[topic]
        titles = TOPIC_TITLES[topic]
        text_idx = i % len(texts)
        title_idx = i % len(titles)

        base_text = texts[text_idx]
        raw_text = corrupt_text(base_text)

        year_lo, year_hi = YEAR_RANGES[topic]
        year = random.randint(year_lo, year_hi)

        rows.append({
            "text_id": f"BL-DT-{i+1:04d}",
            "source_type": random.choice(SOURCE_TYPES),
            "title": titles[title_idx],
            "author": random.choice(AUTHORS),
            "year": year,
            "raw_text": raw_text,
        })

    return rows


# ---------------------------------------------------------------------------
# Generate bl_research_papers.json
# ---------------------------------------------------------------------------

RESEARCH_PAPERS = [
    {
        "paper_id": "BL-RP-001",
        "title": "The Economic Impact of the Black Death on English Agriculture",
        "author": "Dr. Eleanor Whitfield",
        "year": 2019,
        "text": textwrap.dedent("""\
            The Economic Impact of the Black Death on English Agriculture

            Introduction

            The Black Death, which reached the shores of England in the summer of 1348, was the most devastating demographic catastrophe in the recorded history of the British Isles. Current estimates suggest that between one-third and one-half of the population perished within the space of roughly eighteen months. The consequences for agriculture, the dominant economic activity of medieval England, were profound and far-reaching. This paper examines the immediate disruption caused by the plague, the subsequent transformation of labour relations, and the long-term structural changes that reshaped the English countryside over the following century.

            The Pre-Plague Agricultural Economy

            To understand the impact of the Black Death, we must first sketch the economy it disrupted. In the decades before 1348, England was a densely populated agrarian society. The population had grown substantially since the Norman Conquest, reaching perhaps five or six million by the early fourteenth century. This growth had pushed cultivation onto marginal land, increased the fragmentation of peasant holdings, and depressed wages. Lords of manors relied heavily on villeinage, a system in which unfree tenants owed labour services on the demesne in exchange for their holdings. The balance of economic power lay firmly with the landowners.

            Grain production dominated the agricultural landscape. The open-field system, in which strips of arable land were distributed among the tenants of a manor, governed farming practice across much of lowland England. Wheat, barley, oats, and rye were the principal crops, supplemented by legumes grown in rotation to restore soil fertility. Yields were low by modern standards, typically around four to one for wheat, meaning that four bushels were harvested for every bushel sown. Livestock played a secondary role, though sheep were increasingly important in regions suited to pastoral farming, particularly the Cotswolds and East Anglia, where wool production generated substantial export revenue.

            The manorial economy was not entirely self-contained. Markets and fairs facilitated the exchange of agricultural surplus, and the wool trade connected English producers to Continental buyers, particularly in Flanders and Italy. Nevertheless, the majority of the population lived close to subsistence, and even modest harvest failures could trigger localised famine. The Great Famine of 1315 to 1317, caused by a succession of wet summers, had demonstrated the fragility of the system, killing perhaps ten per cent of the population and leaving survivors weakened and malnourished.

            The Arrival of the Plague

            The plague arrived in England through the port of Melcombe Regis in Dorset, probably in June 1348. It spread rapidly along trade routes and through the densely packed populations of towns and monasteries. By the autumn, it had reached London. By the spring of 1349, it was devastating the Midlands and the North. The speed and ferocity of the disease overwhelmed the medical understanding of the age, which attributed the pestilence to miasma, divine punishment, or the conjunction of malign planets.

            The mortality was staggering. In some communities, the death rate approached seventy or eighty per cent. Entire villages were depopulated. The manor court rolls of the period record the succession of tenants in rapid sequence, as one holder after another died and was replaced within weeks or even days. Clergy, who tended the sick and administered last rites, suffered disproportionately. In the diocese of Bath and Wells, nearly half of all beneficed clergy died between 1348 and 1349. The loss of experienced administrators, both ecclesiastical and secular, compounded the economic disruption.

            Immediate Agricultural Disruption

            The immediate effect on agriculture was catastrophic. Fields went unharvested as labourers died or fled. Livestock strayed and perished for want of tending. The Statute of Labourers, enacted in 1351, attempted to freeze wages at pre-plague levels and compel able-bodied workers to accept employment, but the legislation was widely evaded. With a dramatically reduced labour supply and unchanged or increasing demand, the surviving workers were in a position to command higher wages and better conditions, regardless of what the statute prescribed.

            Manorial accounts from the years immediately following the plague reveal a consistent pattern: rising labour costs, falling rents, and declining revenues from demesne farming. At the manor of Cuxham in Oxfordshire, for which unusually detailed records survive, the cost of hiring harvest workers rose by roughly fifty per cent between 1347 and 1350. Similar increases are documented across southern and central England.

            The Transformation of Labour Relations

            The labour shortage created by the Black Death fundamentally altered the relationship between lord and tenant. Villeinage, already under pressure before the plague, became increasingly difficult to enforce. Peasants could and did abscond to neighbouring manors offering better terms, and lords who attempted to maintain traditional labour services found their tenants resistant and their courts overwhelmed. The commutation of labour services into cash rents, a process that had been underway since the thirteenth century, accelerated dramatically in the decades after 1348.

            This transformation was not merely economic. It carried profound social and psychological implications. The peasantry, long accustomed to deference and subordination, began to assert their interests with increasing confidence. The Peasants' Revolt of 1381, triggered by the imposition of a poll tax but rooted in decades of accumulated grievance, was the most dramatic expression of this new assertiveness. Though the revolt was suppressed, the underlying shift in the balance of power proved irreversible.

            Land Use and the Shift to Pastoral Farming

            With a smaller population to feed and higher labour costs to contend with, many landlords found it more profitable to convert arable land to pasture. Sheep farming required far less labour than grain cultivation, and the demand for English wool remained strong on the Continent. The enclosure of open fields and common land, a process that would continue for centuries, had its origins in the post-plague landscape. The rolling hills of the Cotswolds, which had supported mixed farming communities before 1348, became increasingly dominated by sheep walks in the second half of the fourteenth century.

            The shift was neither universal nor immediate. In fertile lowland areas with good access to markets, arable farming continued to be viable, though at reduced intensity. In more marginal regions, however, the retreat from cultivation was marked. Deserted medieval villages, of which over two thousand have been identified in England, are the physical testimony of this contraction. Archaeological evidence from sites such as Wharram Percy in Yorkshire reveals a gradual process of abandonment, as holdings were consolidated, buildings fell into disrepair, and the last inhabitants drifted away to more promising locations.

            Long-Term Structural Changes

            The Black Death did not merely disrupt the medieval agricultural economy; it hastened its transformation into something recognisably different. The century following the plague saw the emergence of a more commercialised, market-oriented rural economy in which tenant farmers, operating on larger and more consolidated holdings, replaced the small-scale subsistence cultivation of the pre-plague era. Wages remained elevated, rents remained depressed, and the standard of living for the surviving peasantry improved substantially.

            The dietary evidence supports this picture. Archaeological analysis of human remains from the period shows improved nutrition and stature in the generations following the plague. The consumption of meat, dairy products, and wheat bread increased, while the reliance on coarser grains such as barley and rye diminished. The English peasant of the late fourteenth century was, on average, better fed, better clothed, and better housed than their pre-plague ancestors.

            Conclusion

            The Black Death was, by any measure, a catastrophe. Its human cost was immense and its immediate effects devastating. Yet the economic consequences were paradoxically transformative. By drastically reducing the labour supply, the plague shifted the balance of power from landlord to labourer, accelerated the decline of villeinage, encouraged the conversion of arable to pasture, and promoted the consolidation of holdings. These changes, driven by demographic catastrophe, laid the groundwork for the agrarian capitalism that would characterise the early modern period. The English countryside of 1450 was a fundamentally different place from the countryside of 1340, and much of that transformation can be traced, directly or indirectly, to the Black Death of 1348.

            References

            Bolton, J. L. (2013). "Looking for Yersinia pestis: Scientists, Historians, and the Black Death." In The Medieval Globe, 1(1), pp. 15-28.
            Campbell, B. M. S. (2016). The Great Transition: Climate, Disease and Society in the Late-Medieval World. Cambridge University Press.
            Dyer, C. (2002). Making a Living in the Middle Ages: The People of Britain 850-1520. Yale University Press.
            Hatcher, J. (1977). Plague, Population and the English Economy 1348-1530. Macmillan.
            Platt, C. (1996). King Death: The Black Death and Its Aftermath in Late-Medieval England. UCL Press.
            Rigby, S. H. (2010). "Urban Population in Late Medieval England." In D. M. Palliser (ed.), The Cambridge Urban History of Britain. Cambridge University Press.
        """).strip(),
    },
    {
        "paper_id": "BL-RP-002",
        "title": "Tudor Maritime Exploration and the Expansion of English Trade Networks",
        "author": "Prof. James Hartley",
        "year": 2021,
        "text": textwrap.dedent("""\
            Tudor Maritime Exploration and the Expansion of English Trade Networks

            Introduction

            The Tudor period, spanning from 1485 to 1603, witnessed a fundamental reorientation of England's relationship with the sea. At the accession of Henry VII, England was a peripheral maritime power, its trade largely confined to the export of raw wool and cloth to Continental markets. By the death of Elizabeth I, English ships had circumnavigated the globe, established trading posts on three continents, and laid the foundations of a commercial empire that would reshape the world over the following centuries. This paper traces the development of Tudor maritime enterprise, examining the interplay of royal patronage, merchant ambition, technological innovation, and geopolitical rivalry that drove England's transformation from a modest island kingdom into a seaborne power.

            The Maritime Inheritance

            Henry VII inherited a kingdom that had little tradition of long-distance maritime exploration. English commerce in the late fifteenth century was dominated by the wool staple at Calais and the cloth trade with the Low Countries, both conducted across the relatively short crossing of the English Channel and the North Sea. The Hanseatic League, a confederation of German merchant towns, maintained a powerful presence in London through its trading post at the Steelyard, and Italian merchants controlled much of the luxury trade.

            There were, however, precedents for English maritime ambition. Bristol merchants had been trading with Iceland since the early fifteenth century and had made tentative voyages into the Atlantic in search of the legendary island of Brasil. The fishing grounds of the North Atlantic, teeming with cod, attracted English vessels to increasingly distant waters. And the tradition of piracy and privateering, which blurred the line between commerce and warfare, provided a reservoir of maritime experience and a willingness to venture beyond familiar waters.

            John Cabot and the North Atlantic

            The first significant act of Tudor maritime exploration was the voyage of John Cabot, a Venetian navigator sailing under English patronage. In 1497, Cabot departed from Bristol aboard the Matthew with a crew of perhaps eighteen men and made landfall somewhere on the coast of North America, probably Newfoundland or Cape Breton Island. The precise location remains disputed, but the significance of the voyage is clear: it established an English claim to the North American continent and demonstrated that the Atlantic could be crossed from English ports.

            Henry VII, characteristically cautious with money, had invested minimally in the venture. Cabot received letters patent granting him authority to explore and claim territory, but the financial backing came largely from Bristol merchants. The king's reward for the discovery of a "new found land" was a pension of twenty pounds per year. Cabot's second voyage, in 1498, departed with five ships but ended in mystery: Cabot himself was never heard from again, and only one ship is known to have returned.

            Despite this inauspicious outcome, the Cabot voyages opened a connection between England and the North American coast that would be maintained, intermittently, throughout the sixteenth century. Bristol fishermen began to frequent the cod-rich waters of the Newfoundland Banks, establishing seasonal fishing stations that represented England's earliest foothold in the New World.

            Henry VIII and the Royal Navy

            Henry VIII's contribution to English maritime development was primarily military rather than exploratory. His construction of a standing navy, equipped with purpose-built warships carrying heavy guns, transformed England's defensive capability and projected royal power across the narrow seas. The Mary Rose, launched in 1511, and the Henri Grace a Dieu, launched in 1514, were among the most formidable warships of their era.

            Henry also invested in the infrastructure of naval power. He established royal dockyards at Deptford and Woolwich, created the Navy Board to manage the fleet's administration, and built a chain of coastal fortifications along the south coast to defend against invasion. These investments, though motivated by the immediate threat of French and Spanish aggression, created the institutional and material foundations upon which later maritime expansion would be built.

            The Muscovy Company and Northern Voyages

            The mid-sixteenth century saw a new phase of English maritime enterprise, driven by the search for alternative routes to the lucrative markets of Asia. The catalyst was the closure of traditional overland routes by the Ottoman Empire and the dominance of the Portuguese and Spanish over the southern sea routes around Africa and through the Strait of Magellan.

            In 1553, a consortium of London merchants financed an expedition under Sir Hugh Willoughby and Richard Chancellor to search for a Northeast Passage to China. Willoughby's ships were lost, but Chancellor reached the White Sea and travelled overland to Moscow, where he was received by Tsar Ivan IV. The resulting trade agreement led to the formation of the Muscovy Company in 1555, the first English joint-stock trading company and a model for the commercial enterprises that would later extend English trade to the East Indies, the Levant, and the Americas.

            The search for a Northwest Passage, around the northern coast of America, also attracted English navigators. Martin Frobisher made three voyages to the Canadian Arctic between 1576 and 1578, discovering Frobisher Bay and bringing back quantities of what he believed to be gold ore but which proved to be worthless iron pyrite. John Davis made three further attempts between 1585 and 1587, reaching as far north as 73 degrees and contributing significantly to the mapping of the North Atlantic.

            Drake, Hawkins, and the Challenge to Spain

            The most dramatic chapter of Tudor maritime history centres on the exploits of Sir Francis Drake and Sir John Hawkins, who combined exploration, trade, and warfare in a direct challenge to Spanish dominance of the Atlantic and Pacific.

            Hawkins pioneered the English involvement in the transatlantic slave trade, making three voyages between 1562 and 1569 in which he transported enslaved Africans to Spanish colonies in the Caribbean. His third voyage ended in disaster at San Juan de Ulua in Mexico, where a Spanish fleet attacked and destroyed most of his ships. The young Francis Drake, who accompanied Hawkins on this voyage, emerged from the experience with a lifelong hatred of Spain and a determination to seek revenge.

            Drake's circumnavigation of the globe between 1577 and 1580 was one of the most remarkable voyages of the age. Ostensibly an expedition to explore the Pacific coast of South America, it was in practice a piratical raid on Spanish treasure ships and colonial settlements. Drake captured enormous quantities of gold, silver, and precious goods, returning to England with a cargo valued at several hundred thousand pounds. Elizabeth I, who had invested in the venture, took a substantial share of the profits and knighted Drake on the deck of his ship, the Golden Hind.

            The Armada and Its Aftermath

            The defeat of the Spanish Armada in 1588 was a defining moment in English maritime history. Philip II's invasion fleet, comprising some 130 ships and 30,000 men, was intended to ferry the Duke of Parma's army across the Channel and overthrow Elizabeth. The English fleet, smaller in tonnage but more manoeuvrable, harassed the Armada as it sailed up the Channel, disrupted its formation with fireships off Gravelines, and inflicted significant damage in the ensuing battle.

            The Armada's destruction, completed by storms as much as by English guns, had consequences that extended far beyond the immediate military victory. It demonstrated that Spanish naval power was not invincible, it boosted English national confidence, and it created the conditions for a further expansion of English maritime enterprise in the following decades. The privateering war against Spain, which continued until the end of Elizabeth's reign, drew hundreds of English ships into the Atlantic and provided a generation of sailors with experience of long-distance navigation.

            The East India Company and the Dawn of Empire

            The culmination of Tudor maritime expansion was the formation of the East India Company in 1600, just three years before Elizabeth's death. The Company received a royal charter granting it a monopoly on English trade with the East Indies, and its first voyage, launched in 1601, reached the spice islands of modern Indonesia. Though the Company's greatest achievements lay in the future, its establishment in the final years of the Tudor period represented the logical conclusion of a century of maritime development.

            Conclusion

            Tudor maritime exploration transformed England from a peripheral island kingdom into a nation with global commercial ambitions. The process was neither planned nor systematic; it was driven by a shifting combination of royal ambition, merchant enterprise, navigational daring, and geopolitical rivalry. Yet its cumulative effect was to create the maritime infrastructure, institutional framework, and cultural confidence that would underpin England's emergence as a world power in the centuries to come. The voyages of Cabot, Drake, and their contemporaries did not merely discover new lands and new routes; they redefined England's sense of its place in the world.

            References

            Andrews, K. R. (1984). Trade, Plunder, and Settlement: Maritime Enterprise and the Genesis of the British Empire, 1480-1630. Cambridge University Press.
            Kelsey, H. (1998). Sir Francis Drake: The Queen's Pirate. Yale University Press.
            Loades, D. (1992). The Tudor Navy: An Administrative, Political, and Military History. Scolar Press.
            McDermott, J. (2001). Martin Frobisher: Elizabethan Privateer. Yale University Press.
            Rodger, N. A. M. (1997). The Safeguard of the Sea: A Naval History of Britain, 660-1649. HarperCollins.
            Willan, T. S. (1956). The Early History of the Russia Company, 1553-1603. Manchester University Press.
        """).strip(),
    },
    {
        "paper_id": "BL-RP-003",
        "title": "Steam, Iron, and Speed: Technology and Society in the British Industrial Revolution",
        "author": "Dr. Ananya Krishnamurthy",
        "year": 2020,
        "text": textwrap.dedent("""\
            Steam, Iron, and Speed: Technology and Society in the British Industrial Revolution

            Introduction

            The Industrial Revolution, conventionally dated from the mid-eighteenth to the mid-nineteenth century, represents the most fundamental transformation of human economic life since the adoption of agriculture. It began in Britain and radiated outward, reshaping first the economies of Western Europe and North America, and eventually the entire world. At its heart was a cluster of technological innovations — the steam engine, the spinning machine, the iron furnace — that multiplied human productive capacity by orders of magnitude. But technology alone does not explain the Industrial Revolution. It was embedded in a web of social, institutional, and environmental conditions that made Britain uniquely receptive to industrial change. This paper examines the interplay of technology and society in the British Industrial Revolution, tracing the connections between mechanical invention, commercial enterprise, and social transformation.

            The Energy Revolution

            The most fundamental shift underlying the Industrial Revolution was a change in the sources of energy available to human society. Pre-industrial economies were organic economies, dependent on the annual flow of solar energy captured by plants and converted into food, fuel, and raw materials. Land was the binding constraint: the amount of energy available to a society was limited by the area of land it could cultivate and the efficiency with which it could convert sunlight into useful work.

            Coal shattered this constraint. Britain possessed abundant and accessible coal deposits, and the mining industry had been expanding since the sixteenth century to meet growing demand for domestic heating fuel. By 1700, Britain was producing over two million tonnes of coal per year, more than the rest of the world combined. What the steam engine provided was a means of converting this geological energy store into mechanical work, liberating the economy from its dependence on the annual solar energy flow and opening up possibilities for growth that had no precedent in human history.

            Thomas Newcomen's atmospheric engine, first installed at a Dudley Castle colliery in 1712, was designed to pump water from mines. It was crude and inefficient, consuming enormous quantities of coal, but it worked. For half a century, Newcomen engines spread through the mining districts of England, keeping the pits dry and enabling the extraction of coal from ever-greater depths. The critical improvement came in the 1760s and 1770s, when James Watt, an instrument-maker at the University of Glasgow, redesigned the engine with a separate condenser that dramatically reduced fuel consumption. Watt's partnership with the Birmingham manufacturer Matthew Boulton, formed in 1775, commercialised the improved engine and extended its application beyond mining to factories, mills, and eventually transportation.

            The Textile Revolution

            If coal and steam provided the energy, the textile industry provided the demand. Cotton textiles, imported from India, had become enormously popular in England by the early eighteenth century, and domestic manufacturers were eager to replicate and undersell the Indian product. The challenge was productivity: Indian weavers, working on hand looms, could produce cloth of extraordinary fineness at labour costs that English workers could not match.

            The response was mechanisation. A succession of inventions, each addressing a different bottleneck in the production process, transformed the cotton industry between 1760 and 1800. James Hargreaves's spinning jenny, patented in 1770, allowed a single spinner to operate multiple spindles simultaneously. Richard Arkwright's water frame, patented in 1769, used water power to drive spinning rollers that produced a stronger yarn suitable for the warp threads of the loom. Samuel Crompton's spinning mule, developed in the 1770s, combined features of both machines to produce a fine, strong yarn that could compete with Indian muslin.

            The effect on productivity was extraordinary. A hand spinner working on a traditional spinning wheel could produce perhaps one pound of cotton yarn per day. By the early nineteenth century, a single operative tending a power-driven mule could produce a hundred times as much. The price of cotton yarn fell correspondingly, making cotton cloth affordable to a mass market and driving an insatiable demand for raw cotton, which was increasingly supplied by slave plantations in the American South.

            Iron and Infrastructure

            The third element of the technological triad was iron. The ability to produce cheap, high-quality iron in large quantities was essential to the construction of the machines, bridges, railways, and buildings that characterised the industrial landscape.

            The key innovation was the substitution of coke for charcoal in the smelting of iron ore. Abraham Darby, working at Coalbrookdale in Shropshire, developed a coke-smelting process in the early eighteenth century that freed iron production from its dependence on dwindling timber supplies. Further advances, particularly Henry Cort's puddling and rolling process of 1784, improved the quality and reduced the cost of wrought iron. British iron production, which had been roughly 25,000 tonnes per year in 1720, reached 250,000 tonnes by 1806 and over two million tonnes by 1850.

            Cheap iron made possible the construction of the infrastructure on which the industrial economy depended. The Iron Bridge at Coalbrookdale, erected in 1779, demonstrated that iron could serve as a structural material for large-scale construction. The Menai Strait suspension bridge, designed by Thomas Telford and opened in 1826, used wrought-iron chains to span over 170 metres. And the railways, which began with the Stockton and Darlington line in 1825 and expanded explosively in the 1830s and 1840s, consumed vast quantities of iron for rails, locomotives, and rolling stock.

            The Factory System

            The social consequences of mechanisation were profound. The factory system, which concentrated workers in purpose-built mills equipped with power-driven machinery, fundamentally altered the organisation of labour and the texture of daily life. In the domestic system that preceded it, spinners and weavers had worked in their own homes, at their own pace, combining textile work with agricultural tasks according to the season. The factory imposed a new discipline: fixed hours, constant supervision, and a rhythm of work dictated by the machine rather than by the sun or the weather.

            The earliest factories were the cotton mills of Lancashire and the West Riding of Yorkshire. Arkwright's mill at Cromford, Derbyshire, established in 1771, is often cited as the first true factory, employing several hundred workers in a multi-storey building powered by a waterwheel. By the early nineteenth century, steam-powered mills were transforming the landscape of Manchester, Leeds, and Bradford, drawing in thousands of workers from the surrounding countryside and from Ireland.

            Working conditions in the early factories were grim. Hours were long, typically twelve to fourteen hours per day, six days per week. Children as young as six or seven were employed as piecers and scavengers, crawling beneath the machinery to retrieve loose cotton and tie broken threads. Accidents were common, and the combination of dust, noise, and confinement took a heavy toll on health. A succession of Factory Acts, beginning with the Health and Morals of Apprentices Act of 1802 and continuing through the 1833 and 1847 Acts, gradually imposed limits on working hours and conditions, though enforcement remained imperfect for decades.

            Urbanisation and Its Discontents

            The growth of industry was accompanied by an unprecedented urbanisation. Manchester, which had been a modest market town of perhaps 25,000 inhabitants in 1770, grew to over 300,000 by 1850. Birmingham, Leeds, Sheffield, and Glasgow underwent similar transformations. The speed of growth overwhelmed existing infrastructure: housing was thrown up hastily and cheaply, streets were unpaved, water supplies were contaminated, and sanitation was virtually nonexistent.

            The public health consequences were devastating. Cholera, typhus, and tuberculosis were endemic in the industrial towns, and life expectancy in the poorest districts of Manchester was just seventeen years. Friedrich Engels, who managed his father's cotton mill in the city, described the conditions in The Condition of the Working Class in England, published in 1845: streets running with filth, cellars housing entire families, and a population physically degraded by overwork and malnutrition.

            The response was a gradual expansion of state intervention. The Public Health Act of 1848, prompted by Edwin Chadwick's Report on the Sanitary Condition of the Labouring Population, established the principle that government had a responsibility to protect the health of its citizens. The Act created a General Board of Health with powers to establish local boards, regulate water supplies, and construct sewers. Subsequent legislation extended these powers and made them compulsory, laying the foundations of the public health infrastructure that we take for granted today.

            Transport and Communication

            The Industrial Revolution was also a revolution in transport and communication. The canal network, constructed largely between 1760 and 1830, provided the first means of moving bulk goods cheaply and reliably over long distances. The Bridgewater Canal, opened in 1761 to carry coal from the Duke of Bridgewater's mines at Worsley to the mills of Manchester, halved the price of coal in the city and triggered a canal-building boom that eventually connected all the major industrial centres of England.

            The railways surpassed the canals in speed, capacity, and versatility. The Liverpool and Manchester Railway, opened in 1830, was the first inter-city passenger railway and demonstrated the commercial viability of steam-powered rail transport. The railway mania of the 1840s saw the construction of thousands of miles of track, financed by speculative investment and built by armies of navvies working with pick, shovel, and wheelbarrow. By 1850, the basic network of British railways was in place, connecting London to every major provincial city and enabling the rapid movement of goods, people, and information across the country.

            Conclusion

            The Industrial Revolution was not a single event but a cascading series of innovations and adaptations that, together, transformed British society more profoundly than any development since the Norman Conquest. Its technological achievements — the steam engine, the spinning machine, the railway — were remarkable, but they cannot be understood in isolation from the social, economic, and institutional context in which they emerged. The revolution created unprecedented wealth and unprecedented misery, spectacular engineering and squalid slums, the factory system and the labour movement. Its legacy, for good and ill, remains with us today.

            References

            Allen, R. C. (2009). The British Industrial Revolution in Global Perspective. Cambridge University Press.
            Berg, M. (1994). The Age of Manufactures, 1700-1820: Industry, Innovation and Work in Britain. Routledge.
            Crafts, N. F. R. (1985). British Economic Growth during the Industrial Revolution. Oxford University Press.
            Mokyr, J. (2009). The Enlightened Economy: An Economic History of Britain, 1700-1850. Yale University Press.
            Thompson, E. P. (1963). The Making of the English Working Class. Victor Gollancz.
            Wrigley, E. A. (2010). Energy and the English Industrial Revolution. Cambridge University Press.
        """).strip(),
    },
    {
        "paper_id": "BL-RP-004",
        "title": "Cholera, Cesspools, and the Sanitary Idea: Victorian Public Health Reform",
        "author": "Prof. Margaret Cavendish-Scott",
        "year": 2022,
        "text": textwrap.dedent("""\
            Cholera, Cesspools, and the Sanitary Idea: Victorian Public Health Reform

            Introduction

            In the summer of 1854, a severe outbreak of cholera struck the Soho district of London. Over the course of three terrible weeks, more than six hundred people died within a few hundred yards of the Broad Street pump. Dr. John Snow, a physician with a growing suspicion that cholera was transmitted through contaminated water rather than through the prevailing miasma of foul air, mapped the cases and traced them to the pump. His persuasion of the local authorities to remove the pump handle is one of the most celebrated episodes in the history of public health. But the story of Victorian sanitary reform is far broader than a single pump. It encompasses decades of political struggle, scientific controversy, engineering ambition, and social transformation that fundamentally changed the relationship between government and the governed.

            The Urban Crisis

            The scale of the public health crisis facing Victorian Britain can scarcely be overstated. The rapid urbanisation driven by the Industrial Revolution had created cities of unprecedented size and density, without the infrastructure to support them. In 1801, roughly twenty per cent of the English population lived in towns of more than ten thousand inhabitants. By 1851, the figure was over fifty per cent. London's population grew from roughly one million in 1800 to nearly three million by 1850. Manchester, Birmingham, Leeds, and Glasgow underwent similar transformations.

            Housing in the industrial towns was built hastily and cheaply to accommodate the influx of workers. Back-to-back houses, sharing three walls with their neighbours and opening onto narrow courts, were the standard form of working-class accommodation in northern English cities. Cellars, originally intended for storage, were converted into dwellings. In Liverpool in 1840, an estimated forty thousand people lived in cellars, often below the water table, in conditions of appalling damp and darkness.

            Sanitation was rudimentary or nonexistent. Few houses had connection to a sewer. Human waste was deposited in cesspools, which were emptied intermittently by nightsoil men and the contents sold as fertiliser. In many districts, cesspools overflowed into the streets, contaminated wells, and seeped through the walls of adjacent cellars. The River Thames, into which the city's sewers drained, was an open sewer itself, yet it also served as London's principal source of drinking water. The water companies drew their supply from the river without filtration or treatment, distributing contaminated water to hundreds of thousands of households.

            The result was endemic disease on a scale that would be inconceivable today. Typhus, spread by body lice in overcrowded conditions, was a constant presence. Tuberculosis, fostered by malnutrition and poor ventilation, killed more Victorians than any other single disease. And cholera, arriving in four major epidemics between 1831 and 1866, struck with a speed and ferocity that terrified rich and poor alike.

            Edwin Chadwick and the Sanitary Report

            The most influential figure in the early public health movement was Edwin Chadwick, a lawyer and administrator who served as secretary to the Poor Law Commission. Chadwick was not a medical man, but he possessed a formidable capacity for gathering evidence and an unshakeable conviction that disease was caused by environmental conditions and could be prevented by sanitary engineering.

            In 1842, Chadwick published his Report on the Sanitary Condition of the Labouring Population of Great Britain. Drawing on evidence gathered from medical officers, poor law guardians, and local investigators across the country, the report painted a devastating picture of the conditions in which the working population lived. It documented the contamination of water supplies, the inadequacy of drainage, the accumulation of refuse, and the consequences for health and life expectancy. In the worst districts of Manchester, Chadwick reported, the average age of death for labourers was seventeen. In the rural county of Rutland, it was thirty-eight.

            Chadwick's solution was comprehensive and characteristically authoritarian. He proposed a system of arterial drainage, using glazed earthenware pipes and a constant supply of water under pressure to flush waste from every house into a network of sewers that would carry it beyond the city for use as agricultural fertiliser. The scheme, which Chadwick promoted with tireless energy and considerable abrasiveness, was technically ambitious and politically controversial. It required new powers of compulsion, new forms of local government, and substantial public expenditure, all of which were resisted by vested interests and by those who regarded government intervention as an infringement of individual liberty.

            The Public Health Act of 1848

            The first legislative fruit of the sanitary movement was the Public Health Act of 1848. Passed in the aftermath of a severe cholera epidemic, the Act established a General Board of Health with Chadwick as one of its members. The Board had power to create local boards of health in areas where the death rate exceeded 23 per thousand or where ten per cent of ratepayers petitioned for one. Local boards were empowered to appoint a medical officer of health, manage water supplies and sewerage, regulate offensive trades, and remove nuisances.

            The Act was a milestone, but its limitations were severe. The powers of the General Board were advisory rather than compulsory in most cases, and local resistance was fierce. Ratepayers objected to the cost, property owners resented interference with their rights, and water companies fought to protect their commercial interests. The Board's abrasive style, largely attributable to Chadwick himself, alienated potential allies. In 1854, the Board was abolished and Chadwick was dismissed, a victim of his own inability to build political coalitions.

            The Great Stink and Bazalgette's Sewers

            The event that finally compelled decisive action was the Great Stink of the summer of 1858. An exceptionally hot June caused the Thames, already heavily polluted with sewage, to emit a stench so overwhelming that Parliament, sitting in the riverside Palace of Westminster, could barely function. Sheets soaked in chloride of lime were hung in the windows of the committee rooms, and there was serious discussion of relocating the legislature.

            The urgency of the situation produced rapid results. Within weeks, Parliament authorised the Metropolitan Board of Works to construct a comprehensive system of intercepting sewers designed by its chief engineer, Joseph Bazalgette. The project was one of the great engineering achievements of the Victorian age. Over the next sixteen years, Bazalgette constructed 82 miles of main intercepting sewers and over a thousand miles of street sewers, diverting the sewage that had previously flowed into the Thames and carrying it to treatment works downstream at Beckton and Crossness. The system was built to last: Bazalgette's sewers, constructed of Portland cement and brick, remain in service today, a testament to the scale of his ambition and the quality of his engineering.

            The impact on public health was dramatic. Cholera, which had struck London four times in thirty years, did not return after 1866. The death rate from waterborne diseases fell sharply, and the Thames, though still far from clean, ceased to be a direct threat to the health of Londoners.

            John Snow and the Waterborne Theory

            The intellectual underpinning of effective public health intervention was the identification of the mechanism by which cholera was transmitted. The prevailing theory, championed by Chadwick among many others, held that disease was caused by miasma, the noxious gases emanating from decomposing organic matter. The miasma theory was not unreasonable: foul-smelling environments did tend to harbour disease, and sanitary improvements motivated by the theory were often effective, if for the wrong reasons.

            John Snow's work on cholera challenged the miasma theory directly. Snow had first proposed a waterborne theory of transmission during the 1849 epidemic, and he refined his argument in a monograph published in 1855. His investigation of the Broad Street outbreak in 1854, in which he mapped cases and traced them to a single contaminated well, provided compelling evidence. His earlier study comparing the cholera mortality of customers supplied by two different water companies, one drawing from a contaminated stretch of the Thames and the other from a cleaner upstream source, provided additional support.

            Snow's theory was not immediately accepted. The miasma theory had powerful adherents, and the germ theory of disease, which would eventually explain the mechanism of waterborne transmission, was not established until the work of Pasteur and Koch in the 1860s and 1870s. But Snow's epidemiological method, using spatial analysis and statistical comparison to identify the source of an outbreak, laid the foundations of modern epidemiology.

            The Consolidation of Public Health

            The decades following the Great Stink saw a progressive consolidation of public health legislation and administration. The Sanitary Act of 1866 made it compulsory for local authorities to provide sewerage and water supply. The Public Health Act of 1875, passed under Disraeli's Conservative government, consolidated the existing legislation into a comprehensive code that remained the basis of English public health law for decades. It required every local authority to appoint a medical officer of health, to ensure an adequate water supply, to provide for sewage disposal, and to regulate housing and food safety.

            The appointment of medical officers of health proved particularly significant. Men such as John Simon at the General Board of Health and later at the Privy Council, and Arthur Newsholme at Brighton and later at the Local Government Board, used their positions to gather data, identify threats, and advocate for preventive measures. The annual reports of medical officers of health, rich in statistical detail and often forthright in their criticism of local conditions, provide an invaluable record of the public health challenges facing Victorian communities.

            Conclusion

            Victorian public health reform was neither rapid nor straightforward. It was resisted at every stage by those who objected to its cost, its interference with property rights, and its expansion of government power. The sanitary idea, championed by Chadwick and his allies, was rooted in an incomplete understanding of disease causation and was often implemented with more enthusiasm than tact. Yet its cumulative achievement was extraordinary. By the end of the nineteenth century, the major cities of Britain possessed systems of water supply, sewerage, and public health administration that had reduced mortality, extended life expectancy, and established the principle that government bore a responsibility for the health of its citizens. The infrastructure that Bazalgette built beneath the streets of London, the legislation that Parliament enacted, and the epidemiological methods that Snow pioneered remain foundations of public health practice today.

            References

            Chadwick, E. (1842). Report on the Sanitary Condition of the Labouring Population of Great Britain. W. Clowes and Sons.
            Halliday, S. (1999). The Great Stink of London: Sir Joseph Bazalgette and the Cleansing of the Victorian Metropolis. Sutton Publishing.
            Hamlin, C. (1998). Public Health and Social Justice in the Age of Chadwick: Britain, 1800-1854. Cambridge University Press.
            Johnson, S. (2006). The Ghost Map: The Story of London's Most Terrifying Epidemic. Riverhead Books.
            Snow, J. (1855). On the Mode of Communication of Cholera. John Churchill.
            Wohl, A. S. (1983). Endangered Lives: Public Health in Victorian Britain. J. M. Dent.
        """).strip(),
    },
    {
        "paper_id": "BL-RP-005",
        "title": "From Babbage to Bletchley: The Prehistory of British Computing",
        "author": "Dr. Thomas Blackwood",
        "year": 2023,
        "text": textwrap.dedent("""\
            From Babbage to Bletchley: The Prehistory of British Computing

            Introduction

            The history of computing is often narrated as an American story, centred on Silicon Valley and the great corporations of the digital age. But many of the foundational ideas, machines, and personalities that made the digital revolution possible were British. Charles Babbage conceived the programmable computer in the 1830s. Ada Lovelace wrote the first algorithm intended for machine execution. Alan Turing defined the theoretical foundations of computation and played a decisive role in breaking the Enigma cipher during the Second World War. The Colossus machines at Bletchley Park were among the first electronic digital computers. This paper traces the British contribution to the prehistory of computing, from Babbage's mechanical engines to the electronic machines of the 1940s, examining the ideas, the machines, and the people who brought them into being.

            Charles Babbage and the Difference Engine

            The story begins with Charles Babbage, Lucasian Professor of Mathematics at Cambridge, polymath, and one of the most original minds of the nineteenth century. In 1821, Babbage was checking a set of mathematical tables prepared by human computers, clerks who calculated values by hand using the method of finite differences. Finding numerous errors, he is said to have exclaimed: "I wish to God these calculations had been executed by steam." The remark, whether apocryphal or not, captures the essential insight that mechanical precision could eliminate human error in the production of the tables upon which navigation, engineering, and science depended.

            Babbage designed his Difference Engine to automate the method of finite differences, a technique for calculating polynomial functions by repeated addition. The machine was to consist of some 25,000 precision-machined parts, capable of calculating and printing tables to six decimal places. In 1823, the British government agreed to fund the project, advancing over seventeen thousand pounds over the following decade, an enormous sum equivalent to the cost of a warship.

            The project was never completed. Babbage quarrelled with his chief engineer, Joseph Clement. The technology of precision machining was at the limit of what was achievable. Babbage himself kept redesigning the machine, unable to resist improvements. By 1842, the government had lost patience and withdrawn its support. The partially completed mechanism, now preserved in the Science Museum in London, represents only a fraction of the intended machine.

            But Babbage had already moved on to something far more ambitious.

            The Analytical Engine

            In the mid-1830s, Babbage began designing a new machine that went beyond anything previously conceived. The Analytical Engine was to be not merely a calculator but a general-purpose computing machine, capable of performing any mathematical operation specified by a sequence of instructions. It incorporated the essential elements of a modern computer: an arithmetic processing unit (the "mill"), a memory (the "store"), a control unit that read instructions from punched cards, and an output mechanism for printing results.

            The design was inspired in part by the Jacquard loom, which used punched cards to control the weaving of complex patterns in silk. Babbage recognised that the same principle could be applied to the control of a calculating machine: the cards would specify not data but operations, enabling the machine to carry out an arbitrary sequence of calculations.

            The Analytical Engine was never built. Babbage produced thousands of pages of design drawings and notes, but the machine existed only on paper and in the wooden and metal components of various experimental assemblies. The British government, having been burned by the Difference Engine, declined to fund the new project. Babbage spent the remaining decades of his life refining the design, growing increasingly bitter about what he perceived as the government's philistinism and the public's indifference.

            Yet the significance of the Analytical Engine can scarcely be overstated. Babbage had conceived, in mechanical form, the fundamental architecture of the programmable computer. The separation of the processing unit from the memory, the use of conditional branching, the concept of iterative loops, all were present in his design, a full century before they were implemented in electronic form.

            Ada Lovelace and the First Programme

            The most perceptive contemporary account of the Analytical Engine was written not by Babbage but by Augusta Ada King, Countess of Lovelace, the daughter of Lord Byron. In 1843, Lovelace translated an article about the Analytical Engine written by the Italian mathematician Luigi Menabrea, appending a set of notes that were considerably longer than the original article.

            Lovelace's notes contain what is widely regarded as the first computer programme: a detailed algorithm for calculating Bernoulli numbers using the Analytical Engine. The algorithm specifies the sequence of operations, the use of variables, and the iterative structure of the calculation, expressed in a notation that anticipates modern programming concepts.

            But Lovelace's contribution went beyond the technical. She articulated, more clearly than Babbage himself, the broader implications of the machine. In her most famous passage, she observed that the Analytical Engine "weaves algebraical patterns just as the Jacquard loom weaves flowers and leaves." She foresaw that the machine could manipulate not merely numbers but any objects whose mutual relationships could be expressed in terms of the abstract science of operations. Music, she speculated, might be composed by a machine that could represent the relations of musical sounds in terms of abstract operations.

            Lovelace also identified a fundamental limitation. "The Analytical Engine has no pretensions whatever to originate anything," she wrote. "It can do whatever we know how to order it to perform." This observation, sometimes called Lady Lovelace's objection, anticipated by more than a century the debates about artificial intelligence that would preoccupy computer scientists in the second half of the twentieth century.

            George Boole and the Algebra of Logic

            A parallel strand of the British contribution to computing was theoretical rather than mechanical. In 1854, George Boole, a self-taught mathematician who held the chair of mathematics at Queen's College Cork, published An Investigation of the Laws of Thought. Boole showed that the operations of logic, including conjunction, disjunction, and negation, could be expressed as algebraic operations on variables that took only two values, which he represented as 0 and 1.

            Boolean algebra, as it came to be known, appeared at first to be a purely abstract exercise in mathematical logic. Its practical significance was not recognised for nearly eighty years, until Claude Shannon, an American engineer at MIT, demonstrated in his 1937 master's thesis that Boolean algebra could be used to design and analyse electrical switching circuits. Shannon's insight made it possible to implement logical operations in electronic hardware, providing the theoretical bridge between Boole's algebra and the digital computer.

            Alan Turing and the Universal Machine

            The most important theoretical contribution to computing came from Alan Turing, a young Cambridge mathematician who, in 1936, published a paper entitled "On Computable Numbers, with an Application to the Entscheidungsproblem." Turing's paper addressed a fundamental question in mathematical logic: is there a mechanical procedure that can determine, for any given mathematical statement, whether it is provable?

            To answer this question, Turing invented an abstract computing device, now known as the Turing machine. The machine consists of an infinite tape divided into cells, a read-write head that can move along the tape, and a finite set of rules (the programme) that determine the machine's behaviour based on the symbol currently under the head and the machine's current state. Turing showed that such a machine could simulate the behaviour of any other computing device, making it a universal machine capable, in principle, of performing any computation that can be described by an algorithm.

            Turing's paper established the theoretical foundations of computer science. The concept of the universal machine demonstrated that a single device, given the right programme, could perform any computational task. This idea, the separation of hardware from software, is the fundamental principle underlying every modern computer.

            Bletchley Park and the Enigma

            The Second World War transformed computing from a theoretical pursuit into a matter of national survival. The German military communicated using the Enigma cipher machine, which produced encrypted messages of such complexity that the Germans considered them unbreakable. The task of breaking Enigma fell to the Government Code and Cypher School at Bletchley Park, a Victorian mansion in Buckinghamshire, where a remarkable assembly of mathematicians, linguists, and chess players was gathered.

            Turing arrived at Bletchley Park in September 1939 and quickly became the central figure in the effort to break the naval Enigma, the most complex variant of the cipher. Building on pre-war work by Polish codebreakers, Turing designed the Bombe, an electromechanical device that could test the vast number of possible Enigma settings at a speed far beyond human capability. By 1941, the Bombes were routinely breaking Enigma traffic, providing intelligence that proved critical to the Battle of the Atlantic and the eventual Allied victory.

            Colossus: The First Electronic Computer

            The culmination of wartime computing at Bletchley Park was the Colossus, designed by the Post Office engineer Tommy Flowers to break the Lorenz cipher, a more sophisticated encryption system used for high-level German communications. Colossus, which became operational in February 1944, used approximately 1,500 thermionic valves (vacuum tubes) to perform logical operations on data read from a paper tape at a speed of 5,000 characters per second.

            Colossus was not a general-purpose computer in the modern sense. It was designed for a specific cryptanalytic task and could not be reprogrammed to perform arbitrary computations. But it was the first large-scale electronic digital computing device, and it demonstrated that electronic valves could be used reliably for high-speed computation, a crucial proof of concept that influenced the design of post-war computers.

            The existence of Colossus remained classified until the 1970s, and its full significance was not publicly acknowledged until much later. As a result, the American ENIAC, completed in 1945, was long credited as the first electronic computer, an attribution that overlooked the British achievement at Bletchley Park.

            The Post-War Legacy

            The end of the war dispersed the extraordinary concentration of talent that had gathered at Bletchley Park. Turing moved to the National Physical Laboratory, where he designed the Automatic Computing Engine (ACE), one of the first detailed designs for a stored-programme electronic computer. The Manchester Baby, built at the University of Manchester in 1948, was the first machine to run a programme stored in electronic memory. The Cambridge EDSAC, completed in 1949, was the first practical stored-programme computer to offer a regular computing service.

            These machines, and the people who built them, represented the translation of wartime experience into peacetime innovation. The British computing industry of the 1950s and 1960s, centred on companies such as Ferranti, English Electric, and Leo Computers (which built the first business computer for the J. Lyons tea company), drew directly on the expertise developed at Bletchley Park and in the university laboratories.

            Conclusion

            The British contribution to the development of computing was foundational. Babbage conceived the programmable computer. Lovelace articulated its potential and its limitations. Boole provided the algebra of logic. Turing defined the theoretical framework. The codebreakers of Bletchley Park built the first electronic computing devices and demonstrated their practical power. That much of this story was concealed by official secrecy for decades, and that the commercial exploitation of computing shifted to the United States in the post-war period, should not obscure the depth and originality of the British achievement.

            References

            Copeland, B. J. (2012). Turing: Pioneer of the Information Age. Oxford University Press.
            Dyson, G. (2012). Turing's Cathedral: The Origins of the Digital Universe. Allen Lane.
            Hyman, A. (1982). Charles Babbage: Pioneer of the Computer. Princeton University Press.
            Swade, D. (2001). The Difference Engine: Charles Babbage and the Quest to Build the First Computer. Viking.
            Turing, A. M. (1936). "On Computable Numbers, with an Application to the Entscheidungsproblem." Proceedings of the London Mathematical Society, 42(1), pp. 230-265.
            Winterbotham, F. W. (1974). The Ultra Secret. Weidenfeld and Nicolson.
        """).strip(),
    },
]


# ---------------------------------------------------------------------------
# Generate chunks and embeddings
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks by character count, respecting sentence boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        if current_length + len(sentence) > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            # Keep overlap: find sentences from end that fit in overlap
            overlap_chunk = []
            overlap_len = 0
            for s in reversed(current_chunk):
                if overlap_len + len(s) <= overlap:
                    overlap_chunk.insert(0, s)
                    overlap_len += len(s)
                else:
                    break
            current_chunk = overlap_chunk
            current_length = overlap_len

        current_chunk.append(sentence)
        current_length += len(sentence)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def generate_chunks_and_embeddings(
    papers: list[dict],
    digitised_rows: list[dict],
    target_chunks: int = 500,
) -> tuple[list[dict], np.ndarray]:
    """Generate chunks from papers and digitised texts, then compute TF-IDF embeddings."""
    all_chunks = []

    # Chunk all research papers
    for paper in papers:
        paper_chunks = chunk_text(paper["text"], chunk_size=600, overlap=100)
        for idx, chunk_text_str in enumerate(paper_chunks):
            all_chunks.append({
                "chunk_id": f"{paper['paper_id']}-C{idx+1:03d}",
                "text_id": paper["paper_id"],
                "chunk_text": chunk_text_str,
                "chunk_index": idx,
            })

    # Add chunks from a selection of digitised texts (take clean versions)
    # Select enough to reach target
    remaining = target_chunks - len(all_chunks)
    if remaining > 0:
        # Use the original (uncorrupted) texts
        topic_keys = list(ALL_TOPIC_TEXTS.keys())
        chunk_idx = 0
        texts_used = 0
        while len(all_chunks) < target_chunks and texts_used < 200:
            topic = topic_keys[texts_used % len(topic_keys)]
            text_list = ALL_TOPIC_TEXTS[topic]
            text = text_list[texts_used % len(text_list)]
            text_id = f"BL-DT-{texts_used+1:04d}"

            # These texts are short, so each becomes one chunk
            all_chunks.append({
                "chunk_id": f"{text_id}-C001",
                "text_id": text_id,
                "chunk_text": text,
                "chunk_index": 0,
            })
            texts_used += 1

    # Trim to target
    all_chunks = all_chunks[:target_chunks]

    # Generate TF-IDF embeddings with 384 dimensions
    chunk_texts = [c["chunk_text"] for c in all_chunks]
    vectorizer = TfidfVectorizer(max_features=384)
    tfidf_matrix = vectorizer.fit_transform(chunk_texts).toarray().astype(np.float32)

    # Normalise to unit vectors for cosine similarity
    norms = np.linalg.norm(tfidf_matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1  # avoid division by zero
    tfidf_matrix = tfidf_matrix / norms

    return all_chunks, tfidf_matrix


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Generating digitised texts...")
    digitised_rows = generate_digitised_texts(2000)

    # Write CSV
    csv_path = DATA_DIR / "bl_digitised_texts_raw.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text_id", "source_type", "title", "author", "year", "raw_text"])
        writer.writeheader()
        writer.writerows(digitised_rows)
    print(f"  Written {len(digitised_rows)} rows to {csv_path}")

    # Write research papers JSON
    print("Writing research papers...")
    papers_path = DATA_DIR / "bl_research_papers.json"
    with open(papers_path, "w", encoding="utf-8") as f:
        json.dump(RESEARCH_PAPERS, f, indent=2, ensure_ascii=False)
    print(f"  Written {len(RESEARCH_PAPERS)} papers to {papers_path}")

    # Generate chunks and embeddings
    print("Generating chunks and embeddings...")
    chunks, embeddings = generate_chunks_and_embeddings(RESEARCH_PAPERS, digitised_rows, target_chunks=500)

    # Write parquet
    parquet_path = DATA_DIR / "bl_chunks_with_embeddings.parquet"
    table = pa.table({
        "chunk_id": [c["chunk_id"] for c in chunks],
        "text_id": [c["text_id"] for c in chunks],
        "chunk_text": [c["chunk_text"] for c in chunks],
        "chunk_index": [c["chunk_index"] for c in chunks],
        "embedding": [emb.tolist() for emb in embeddings],
    })
    pq.write_table(table, parquet_path)
    print(f"  Written {len(chunks)} chunks to {parquet_path}")

    # Write numpy embeddings
    npy_path = DATA_DIR / "bl_embeddings.npy"
    np.save(npy_path, embeddings)
    print(f"  Written embeddings shape {embeddings.shape} to {npy_path}")

    # Quick sanity check: search for "medieval trade routes"
    print("\nSanity check: searching for 'medieval trade routes'...")
    from sklearn.metrics.pairwise import cosine_similarity as cos_sim

    query = "medieval trade routes"
    # We need to transform the query using the same vectorizer
    # Re-fit is needed since we don't save the vectorizer
    chunk_texts = [c["chunk_text"] for c in chunks]
    vectorizer = TfidfVectorizer(max_features=384)
    tfidf_matrix = vectorizer.fit_transform(chunk_texts).toarray().astype(np.float32)
    norms = np.linalg.norm(tfidf_matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    tfidf_matrix = tfidf_matrix / norms

    query_vec = vectorizer.transform([query]).toarray().astype(np.float32)
    query_norm = np.linalg.norm(query_vec)
    if query_norm > 0:
        query_vec = query_vec / query_norm

    similarities = cos_sim(query_vec, tfidf_matrix)[0]
    top_5_idx = np.argsort(similarities)[-5:][::-1]
    for idx in top_5_idx:
        print(f"  Score: {similarities[idx]:.4f} | {chunks[idx]['chunk_text'][:100]}...")

    print("\nData generation complete!")


if __name__ == "__main__":
    main()
