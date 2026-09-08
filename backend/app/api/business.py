"""ARCHITECTURE.md §5 — Business categories (wizard step 2)."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

# Structured categories with Indic names per §4 data model
CATEGORIES = [
    {"slug": "dairy", "name": "Dairy Farming", "name_hi": "डेयरी", "name_mr": "दूध व्यवसाय", "name_ta": "பால் பண்ணை", "icon": "🌾"},
    {"slug": "retail", "name": "Retail / Kirana Store", "name_hi": "किराना दुकान", "name_mr": "किराणा दुकान", "name_ta": "கடை", "icon": "🏪"},
    {"slug": "textiles", "name": "Textiles & Garments", "name_hi": "वस्त्र", "name_mr": "वस्त्रोद्योग", "name_ta": "நெசவு", "icon": "🧵"},
    {"slug": "food_processing", "name": "Food Processing", "name_hi": "खाद्य प्रसंस्करण", "name_mr": "अन्न प्रक्रिया", "name_ta": "உணவு பதப்படுத்துதல்", "icon": "🥫"},
    {"slug": "agriservices", "name": "Agri-Services Centre", "name_hi": "कृषि सेवा केंद्र", "name_mr": "कृषी सेवा केंद्र", "name_ta": "விவசாய சேவை", "icon": "🚜"},
    {"slug": "poultry", "name": "Poultry Farming", "name_hi": "मुर्गी पालन", "name_mr": "कोंबडी पालन", "name_ta": "கோழி பண்ணை", "icon": "🐔"},
    {"slug": "handicrafts", "name": "Handicrafts", "name_hi": "हस्तशिल्प", "name_mr": "हस्तकला", "name_ta": "கைவினை", "icon": "🎨"},
    {"slug": "other", "name": "Other Micro-Enterprise", "name_hi": "अन्य", "name_mr": "इतर", "name_ta": "மற்றவை", "icon": "📦"},
]


@router.get("/categories")
def list_categories(lang: str = "en") -> list[dict]:
    """Categories for the wizard, with localized names."""
    key = {"hi": "name_hi", "mr": "name_mr", "ta": "name_ta"}.get(lang, "name")
    return [
        {"slug": c["slug"], "name": c[key] if lang != "en" else c["name"],
         "name_en": c["name"], "icon": c["icon"]}
        for c in CATEGORIES
    ]
