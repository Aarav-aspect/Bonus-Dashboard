"""Regional postcode mappings for trade group filtering."""


# Trade Group Phase Mapping
# Defines which phase of regional rolling out applies to which trade group.
TRADE_GROUP_PHASE = {
    "Fire Safety": 2,
    "Environmental Services": 1,
    "HVac & Electrical": 2,
    "Building Fabric": 2,
    "Plumbing & Drainage": 3,
    "Leak, Damp & Restoration": 3,
}

# Available Region Options by Phase
REGION_OPTIONS_BY_PHASE = {
    1: ["All"],
    2: ["All", "North", "South"],
    3: ["All", "North West", "South West", "East"],
}


def get_region_options(trade_group: str) -> list[str]:
    """Returns the available region filter options for a given trade group."""
    if trade_group == "All Groups":
        # If looking at everything, we can't cleanly filter by region since rules differ
        return ["All"]
    
    phase = TRADE_GROUP_PHASE.get(trade_group, 1)
    return REGION_OPTIONS_BY_PHASE.get(phase, ["All"])


def get_region_for_trade(postcode: str, trade_group: str) -> str:
    """
    Returns the appropriate region for a postcode based on the trade group's phase.
    If the trade group doesn't have regional routing yet (Phase 1), returns 'All'.
    """
    phase = TRADE_GROUP_PHASE.get(trade_group, 1)
    
    if phase == 1:
        return "All"
    elif phase == 2:
        return get_region_phase2(postcode)
    elif phase == 3:
        return get_region_phase3(postcode)
    
    return "All"


# Phase 2 mapping (North/South)
def get_region_phase2(postcode: str):
    """Map postcode to region (North/South)"""
    if not isinstance(postcode, str) or len(postcode.strip()) < 1:
        return "Leads Without Postcode"

    postcode = postcode.strip().upper()

    # 4-character mappings
    if postcode[:4] == "UB11":
        return "South"

    # 3-character mappings
    mapping_3_north = {"SL9", "SL8", "SL7", "RG9", "RG8", "SN7"}
    mapping_3_south = {"UB2", "UB4", "UB8", "UB7", "UB3"}

    if postcode[:3] in mapping_3_north:
        return "North"
    if postcode[:3] in mapping_3_south:
        return "South"

    # 2-character mappings
    mapping_2_north = {
        "RM", "IG", "EN", "WD", "HA", "UB", "NW", "WC", "EC", "WV", "WR", "WA",
        "WF", "WS", "WN",
    }
    mapping_2_south = {
        "SL", "SE", "SW", "TW", "KT", "SM", "CR", "BR", "DA", "ME", "TN", "BN",
        "RH", "GU", "SO", "BH", "SP", "CT", "PO", "RG", "BA", "EX", "TA", "BS",
        "DT", "SN", "PL", "TQ", "TR",
    }

    if postcode[:2] in mapping_2_north:
        return "North"
    if postcode[:2] in mapping_2_south:
        return "South"

    # 1-character mappings
    mapping_1_north = {
        "N", "E", "L", "B", "G", "C", "S", "P", "H", "A", "M", "I", "D", "T",
        "Y", "F", "O", "W",
    }

    if postcode[0] in mapping_1_north:
        return "North"

    return "Other"


# Phase 3 mapping (East/North West/South West)
def get_region_phase3(postcode: str):
    """Map postcode to region (East/North West/South West/Other)"""
    if not isinstance(postcode, str) or len(postcode.strip()) < 1:
        return "Leads Without Postcode"

    postcode = postcode.strip().upper()

    # 4-character mappings
    mapping_4_east = {"NR33", "NR34", "NR35", "NR32", "SW1A", "SW1E", "SW1H", "SW1P", "SW1B", "SW1W", "SW1X", "SW1Y", "SW1V"}
    mapping_4_northwest = {"LE16", "NW10", "NW11", "UB10"}
    mapping_4_southwest = {
        "BH24", "BH25", "SW20", "SW10", "SW11", "SW18", "SW12",
        "TN22", "TN20", "TN21", "TN19", "TN31", "TN32", "TN33", "TN34", "TN35",
        "TN36", "TN37", "TN38", "TN39", "TN40"
    }

    prefix4 = postcode[:4]
    if prefix4 in mapping_4_east: return "East"
    if prefix4 in mapping_4_northwest: return "North West"
    if prefix4 in mapping_4_southwest: return "South West"

    # 3-character mappings
    mapping_3_east = {"NW1", "EN9", "SG8", "WC1", "WC2", "N1C", "PE8"}
    mapping_3_northwest = {
        "N10", "N11", "N12", "N13", "N14", "N17", "N18", "N20", "N21", "N22", 
        "NW2", "NW4", "NW7", "NW9", "RG8", "RG9", "UB9", "SN7", "NW3", "NW5", 
        "NW6", "NW8", "W14", "W11", "W10", "N19", "N15", "N16", "UB6", "UB5", 
        "SL9", "SL8", "SL7", "W12", "W13"
    }
    mapping_3_southwest = {
        "SW4", "SW5", "SW2", "SW3", "SW6", "SW7", "SW8", "SW9", "TN7", "TN6", "TN5"
    }

    prefix3 = postcode[:3]
    if prefix3 in mapping_3_east: return "East"
    if prefix3 in mapping_3_northwest: return "North West"
    if prefix3 in mapping_3_southwest: return "South West"

    # 2-character mappings
    mapping_2_east = {
        "BR", "CB", "CM", "CO", "CT", "DA", "EC", "IG", "IP", "ME", "PE", "RM", 
        "SE", "SS", "TN", "N1", "W1"
    }
    mapping_2_northwest = {
        "NE", "HU", "YO", "LS", "HG", "TS", "DL", "CA", "LA", "PR", "FY", "HX", 
        "DH", "OL", "HD", "W2", "W9", "W8", "AL", "EN", "HA", "HP", "LU", "MK", 
        "N2", "N3", "N9", "NN", "OX", "SG", "WD", "NP", "NG", "GL", "HR", "LE", 
        "CV", "WR", "DY", "ST", "TF", "LL", "CW", "SK", "WA", "WN", "LN", "DN", 
        "N6", "N7", "N5", "N4", "N8", "SY", "CH", "DE", "WS", "WV", "BL", "W6", 
        "W3", "W4", "W5", "WF", "W7"
    }
    mapping_2_southwest = {
        "BN", "CR", "GU", "KT", "PO", "RG", "RH", "SL", "SN", "SO", "SW", "TW", 
        "UB", "SM", "EX", "TQ", "PL", "DT", "BA", "BH", "SP", "BS", "CF", "SA", 
        "TA", "TR"
    }

    prefix2 = postcode[:2]
    if prefix2 in mapping_2_east: return "East"
    if prefix2 in mapping_2_northwest: return "North West"
    if prefix2 in mapping_2_southwest: return "South West"

    # 1-character mappings
    mapping_1_east = {"E", "N"}
    mapping_1_northwest = {"B", "S", "M", "L"}
    mapping_1_southwest = {"W"}

    prefix1 = postcode[:1]
    if prefix1 in mapping_1_east: return "East"
    if prefix1 in mapping_1_northwest: return "North West"
    if prefix1 in mapping_1_southwest: return "South West"

    return "Other"
