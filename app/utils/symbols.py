from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SymbolMetadata:
    canonical: str
    display: str
    name: str
    exchange: str | None = None
    sector: str | None = None


SYMBOL_CATALOG: dict[str, SymbolMetadata] = {
    "EMAAR": SymbolMetadata("EMAAR", "EMAAR.DU", "Emaar Properties", "DFM", "Real Estate"),
    "DAMAC": SymbolMetadata("DAMAC", "DAMAC.DU", "DAMAC Properties", "DFM", "Real Estate"),
    "DEYAAR": SymbolMetadata("DEYAAR", "DEYAAR.DU", "Deyaar Development", "DFM", "Real Estate"),
    "UPP": SymbolMetadata("UPP", "UPP.DU", "Union Properties", "DFM", "Real Estate"),
    "AMLAK": SymbolMetadata("AMLAK", "AMLAK.DU", "Amlak Finance", "DFM", "Real Estate Finance"),
    "ALDAR": SymbolMetadata("ALDAR", "ALDAR.AD", "Aldar Properties", "ADX", "Real Estate"),
    "ESHRAQ": SymbolMetadata("ESHRAQ", "ESHRAQ.AD", "Eshraq Investments", "ADX", "Real Estate"),
    "RAKPROP": SymbolMetadata("RAKPROP", "RAKPROP.AD", "RAK Properties", "ADX", "Real Estate"),
    "DFM": SymbolMetadata("DFM", "DFM.DU", "Dubai Financial Market", "DFM", "Financial Services"),
    "DIC": SymbolMetadata("DIC", "DIC.DU", "Dubai Investments", "DFM", "Diversified"),
    "ADCB": SymbolMetadata("ADCB", "ADCB.AD", "Abu Dhabi Commercial Bank", "ADX", "Banking"),
    "FAB": SymbolMetadata("FAB", "FAB.AD", "First Abu Dhabi Bank", "ADX", "Banking"),
    "ADNOC": SymbolMetadata("ADNOC", "ADNOC.AD", "ADNOC Distribution", "ADX", "Energy"),
    "SPG": SymbolMetadata("SPG", "SPG", "Simon Property Group", "NYSE", "Global Real Estate"),
    "O": SymbolMetadata("O", "O", "Realty Income", "NYSE", "Global Real Estate"),
    "PLD": SymbolMetadata("PLD", "PLD", "Prologis", "NYSE", "Global Real Estate"),
    "AMT": SymbolMetadata("AMT", "AMT", "American Tower", "NYSE", "Global Real Estate"),
    "CCI": SymbolMetadata("CCI", "CCI", "Crown Castle", "NYSE", "Global Real Estate"),
    "LEN": SymbolMetadata("LEN", "LEN", "Lennar", "NYSE", "Developers"),
    "DHI": SymbolMetadata("DHI", "DHI", "D.R. Horton", "NYSE", "Developers"),
    "NVR": SymbolMetadata("NVR", "NVR", "NVR", "NYSE", "Developers"),
}


ALIAS_TO_CANONICAL: dict[str, str] = {}
for canonical, metadata in SYMBOL_CATALOG.items():
    ALIAS_TO_CANONICAL[canonical] = metadata.canonical
    ALIAS_TO_CANONICAL[metadata.display] = metadata.canonical


def normalize_symbol(symbol: str | None) -> str:
    if not symbol:
        return ""
    cleaned = symbol.strip().upper()
    return ALIAS_TO_CANONICAL.get(cleaned, cleaned)


def display_symbol(symbol: str | None) -> str:
    if not symbol:
        return ""
    canonical = normalize_symbol(symbol)
    metadata = SYMBOL_CATALOG.get(canonical)
    return metadata.display if metadata else canonical


def symbol_metadata(symbol: str | None) -> SymbolMetadata | None:
    canonical = normalize_symbol(symbol)
    return SYMBOL_CATALOG.get(canonical)
