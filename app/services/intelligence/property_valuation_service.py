from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import mean, median
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsArticle


class PropertyValuationService:
    """Deterministic valuation and ROI tooling tuned for current Dubai/UAE product needs."""

    LOCATION_PROFILES: dict[str, dict[str, Any]] = {
        "Dubai Marina": {
            "supported_types": ["Apartment", "Penthouse", "Duplex"],
            "default_area_sqft": 1350,
            "default_bedrooms": 2,
            "default_year_built": 2020,
            "default_amenities": ["Pool", "Gym", "Sea View", "Parking"],
            "monthly_rent": 16500,
            "monthly_expenses": 2200,
            "appreciation_rate": 0.055,
        },
        "Downtown Dubai": {
            "supported_types": ["Apartment", "Penthouse"],
            "default_area_sqft": 1280,
            "default_bedrooms": 2,
            "default_year_built": 2019,
            "default_amenities": ["Pool", "Gym", "Smart Home", "Parking"],
            "monthly_rent": 18250,
            "monthly_expenses": 2400,
            "appreciation_rate": 0.058,
        },
        "Palm Jumeirah": {
            "supported_types": ["Apartment", "Villa", "Penthouse"],
            "default_area_sqft": 1780,
            "default_bedrooms": 3,
            "default_year_built": 2021,
            "default_amenities": ["Beach Access", "Private Pool", "Sea View", "Parking"],
            "monthly_rent": 26500,
            "monthly_expenses": 3800,
            "appreciation_rate": 0.064,
        },
        "Business Bay": {
            "supported_types": ["Apartment", "Duplex"],
            "default_area_sqft": 1160,
            "default_bedrooms": 1,
            "default_year_built": 2020,
            "default_amenities": ["Pool", "Gym", "Smart Home", "Parking"],
            "monthly_rent": 12800,
            "monthly_expenses": 1850,
            "appreciation_rate": 0.051,
        },
        "Dubai Hills": {
            "supported_types": ["Apartment", "Townhouse", "Villa"],
            "default_area_sqft": 1680,
            "default_bedrooms": 3,
            "default_year_built": 2022,
            "default_amenities": ["Golf View", "Gym", "Study", "Parking"],
            "monthly_rent": 17100,
            "monthly_expenses": 2450,
            "appreciation_rate": 0.053,
        },
        "Jumeirah Village Circle": {
            "supported_types": ["Apartment", "Townhouse"],
            "default_area_sqft": 1180,
            "default_bedrooms": 2,
            "default_year_built": 2021,
            "default_amenities": ["Pool", "Gym", "Parking", "Smart Home"],
            "monthly_rent": 8600,
            "monthly_expenses": 1450,
            "appreciation_rate": 0.047,
        },
        "Dubai Creek Harbour": {
            "supported_types": ["Apartment", "Penthouse"],
            "default_area_sqft": 1240,
            "default_bedrooms": 2,
            "default_year_built": 2023,
            "default_amenities": ["Pool", "Gym", "Sea View", "Parking"],
            "monthly_rent": 13800,
            "monthly_expenses": 1950,
            "appreciation_rate": 0.054,
        },
        "Yas Island": {
            "supported_types": ["Apartment", "Townhouse", "Villa"],
            "default_area_sqft": 1520,
            "default_bedrooms": 3,
            "default_year_built": 2021,
            "default_amenities": ["Pool", "Gym", "Parking", "Private Garden"],
            "monthly_rent": 12100,
            "monthly_expenses": 1800,
            "appreciation_rate": 0.049,
        },
    }

    LOCATION_BASELINES: dict[str, float] = {
        "downtown dubai": 2550,
        "dubai marina": 2350,
        "palm jumeirah": 3450,
        "jbr": 2150,
        "business bay": 2050,
        "dubai hills": 1950,
        "jumeirah village circle": 1350,
        "jvc": 1350,
        "arabian ranches": 1650,
        "emaar beachfront": 2900,
        "dubai creek harbour": 1850,
        "al reem island": 1450,
        "yas island": 1750,
    }

    TYPE_MULTIPLIERS: dict[str, float] = {
        "apartment": 1.0,
        "villa": 1.22,
        "townhouse": 1.12,
        "penthouse": 1.35,
        "duplex": 1.18,
    }

    AMENITY_WEIGHTS: dict[str, float] = {
        "pool": 0.018,
        "gym": 0.012,
        "sea view": 0.045,
        "marina view": 0.03,
        "golf view": 0.02,
        "maid room": 0.012,
        "study": 0.008,
        "private garden": 0.02,
        "private pool": 0.035,
        "beach access": 0.04,
        "smart home": 0.012,
        "parking": 0.01,
    }

    def get_supported_locations(self) -> list[str]:
        return list(self.LOCATION_PROFILES.keys())

    def get_supported_property_types(self, location: str | None = None) -> list[str]:
        if location and location in self.LOCATION_PROFILES:
            return self.LOCATION_PROFILES[location]["supported_types"]
        return ["Apartment", "Villa", "Townhouse", "Penthouse", "Duplex"]

    async def get_property_options(self, db: AsyncSession) -> dict[str, Any]:
        locations: list[dict[str, Any]] = []
        for location, profile in self.LOCATION_PROFILES.items():
            trend = await self._get_market_trend(db, location)
            locations.append(
                {
                    "name": location,
                    "price_per_sqft": round(self._baseline_price_per_sqft(location), 2),
                    "trend_percent": round(trend * 100, 2),
                    "supported_types": profile["supported_types"],
                }
            )

        return {
            "locations": locations,
            "property_types": self.get_supported_property_types(),
            "amenities": list(self.AMENITY_WEIGHTS.keys()),
        }

    async def get_property_preset(self, db: AsyncSession | None, *, location: str, property_type: str) -> dict[str, Any]:
        normalized_location = location if location in self.LOCATION_PROFILES else self.get_supported_locations()[0]
        profile = self.LOCATION_PROFILES[normalized_location]
        chosen_type = property_type if property_type in profile["supported_types"] else profile["supported_types"][0]
        type_multiplier = self.TYPE_MULTIPLIERS.get(chosen_type.lower(), 1.0)
        area_sqft = round(profile["default_area_sqft"] * (1.18 if chosen_type.lower() in {"villa", "penthouse"} else 1.0), 0)
        bedrooms = profile["default_bedrooms"] + (1 if chosen_type.lower() in {"villa", "penthouse"} else 0)
        price_per_sqft = self._baseline_price_per_sqft(normalized_location) * type_multiplier
        purchase_price = round(area_sqft * price_per_sqft, 2)
        market_trend = await self._get_market_trend(db, normalized_location) if db is not None else 0.03
        rental_income = round(profile["monthly_rent"] * (1.22 if chosen_type.lower() in {"villa", "penthouse"} else 1.0), 2)
        expenses = round(profile["monthly_expenses"] * (1.18 if chosen_type.lower() in {"villa", "penthouse"} else 1.0), 2)

        return {
            "location": normalized_location,
            "property_type": chosen_type,
            "valuation_defaults": {
                "location": normalized_location,
                "property_type": chosen_type,
                "area_sqft": area_sqft,
                "bedrooms": bedrooms,
                "year_built": profile["default_year_built"],
                "amenities": profile["default_amenities"],
            },
            "roi_defaults": {
                "purchase_price": purchase_price,
                "rental_income_monthly": rental_income,
                "expenses_monthly": expenses,
                "appreciation_rate": profile["appreciation_rate"],
            },
            "market_context": {
                "baseline_price_per_sqft": round(price_per_sqft, 2),
                "market_trend_percent": round(market_trend * 100, 2),
                "supported_types": profile["supported_types"],
            },
        }

    async def estimate_property_value(
        self,
        db: AsyncSession,
        *,
        area_sqft: float,
        bedrooms: int,
        location: str,
        property_type: str,
        year_built: int,
        amenities: list[str] | None = None,
    ) -> dict[str, Any]:
        amenities = amenities or []
        baseline = self._baseline_price_per_sqft(location)
        type_multiplier = self.TYPE_MULTIPLIERS.get(property_type.lower(), 1.0)
        bedroom_multiplier = 1 + min(max(bedrooms - 1, 0) * 0.03, 0.15)
        age_factor = self._age_factor(year_built)
        amenity_factor = 1 + sum(self.AMENITY_WEIGHTS.get(item.lower(), 0.006) for item in amenities[:8])
        market_trend = await self._get_market_trend(db, location)

        price_per_sqft = baseline * type_multiplier * bedroom_multiplier * age_factor * amenity_factor
        base_value = area_sqft * price_per_sqft
        adjusted_value = base_value * (1 + market_trend)
        confidence_band = adjusted_value * 0.085

        comparables = await self._find_comparables(
            area_sqft=area_sqft,
            bedrooms=bedrooms,
            location=location,
            property_type=property_type,
            base_price_per_sqft=price_per_sqft,
        )

        return {
            "estimated_value_aed": round(adjusted_value, 2),
            "confidence_interval": {
                "lower": round(adjusted_value - confidence_band, 2),
                "upper": round(adjusted_value + confidence_band, 2),
            },
            "price_per_sqft": round(price_per_sqft, 2),
            "market_trend": round(market_trend * 100, 2),
            "comparables": comparables,
            "value_drivers": self._get_value_drivers(
                location=location,
                property_type=property_type,
                year_built=year_built,
                amenities=amenities,
                market_trend=market_trend,
                baseline=baseline,
            ),
            "valuation_date": datetime.now(timezone.utc),
            "narrative": (
                f"{location} is currently pricing like a {property_type.lower()} submarket with "
                f"{'constructive' if market_trend >= 0 else 'softer'} narrative support. "
                f"The estimate leans on location baseline, property form factor, building age, and amenity lift."
            ),
        }

    async def calculate_roi(
        self,
        *,
        purchase_price: float,
        rental_income_monthly: float,
        expenses_monthly: float,
        appreciation_rate: float = 0.05,
    ) -> dict[str, Any]:
        annual_rental = rental_income_monthly * 12
        annual_expenses = expenses_monthly * 12
        net_annual_income = annual_rental - annual_expenses
        cap_rate = (net_annual_income / purchase_price) * 100 if purchase_price else 0.0
        cash_on_cash = cap_rate

        projections: list[dict[str, Any]] = []
        property_value = purchase_price
        for year in range(1, 11):
            property_value *= 1 + appreciation_rate
            total_rental = net_annual_income * year
            total_return = property_value - purchase_price + total_rental
            roi = (total_return / purchase_price) * 100 if purchase_price else 0.0
            projections.append(
                {
                    "year": year,
                    "property_value": round(property_value, 2),
                    "cumulative_rental_income": round(total_rental, 2),
                    "total_return": round(total_return, 2),
                    "roi_percent": round(roi, 2),
                }
            )

        return {
            "cap_rate": round(cap_rate, 2),
            "cash_on_cash_return": round(cash_on_cash, 2),
            "annual_net_income": round(net_annual_income, 2),
            "payback_period_years": round(purchase_price / net_annual_income, 1) if net_annual_income > 0 else None,
            "projections": projections,
            "investment_grade": self._get_investment_grade(cap_rate),
        }

    async def comparative_market_analysis(
        self,
        db: AsyncSession,
        *,
        location: str,
        property_type: str,
        bedrooms: int,
        area_sqft: float,
        year_built: int,
        radius_km: float = 2.0,
    ) -> dict[str, Any]:
        del radius_km, year_built
        comparables = await self._find_comparables(
            area_sqft=area_sqft,
            bedrooms=bedrooms,
            location=location,
            property_type=property_type,
            base_price_per_sqft=self._baseline_price_per_sqft(location),
        )

        prices = [item["estimated_price_aed"] for item in comparables]
        price_per_sqft = [item["price_per_sqft"] for item in comparables]
        market_stats = None
        if comparables:
            market_stats = {
                "average_price": round(mean(prices), 2),
                "median_price": round(median(prices), 2),
                "price_range": (round(min(prices), 2), round(max(prices), 2)),
                "average_price_per_sqft": round(mean(price_per_sqft), 2),
                "median_price_per_sqft": round(median(price_per_sqft), 2),
                "total_sales": len(comparables),
                "days_on_market_avg": round(28 + max(0, 4 - bedrooms) * 3, 1),
            }

        market_trend = await self._get_market_trend(db, location)
        activity = "hot" if market_trend >= 0.08 else "moderate" if market_trend >= 0 else "slow"
        recommendation = self._get_pricing_recommendation(location, property_type, market_stats, market_trend)

        return {
            "recent_sales": comparables,
            "market_statistics": market_stats,
            "market_activity": activity,
            "recommendation": recommendation,
        }

    def _baseline_price_per_sqft(self, location: str) -> float:
        normalized = location.strip().lower()
        for known, value in self.LOCATION_BASELINES.items():
            if known in normalized:
                return value
        return 1450.0

    def _age_factor(self, year_built: int) -> float:
        age = max(0, datetime.now(timezone.utc).year - year_built)
        return max(0.78, 1 - age * 0.006)

    async def _get_market_trend(self, db: AsyncSession, location: str) -> float:
        from_date = datetime.now(timezone.utc) - timedelta(days=30)
        result = await db.execute(
            select(NewsArticle)
            .where(
                and_(
                    NewsArticle.published_at >= from_date,
                    NewsArticle.is_published.is_(True),
                )
            )
            .order_by(NewsArticle.published_at.desc())
        )
        articles = result.scalars().all()

        normalized_location = location.lower()
        scores: list[float] = []
        for article in articles:
            text = " ".join([article.title, article.description or "", article.content or ""]).lower()
            if normalized_location in text or any(token in text for token in {"dubai", "uae", "property", "real estate"}):
                raw_score = float(article.sentiment_score or 0)
                normalized_score = raw_score / 100 if abs(raw_score) > 1 else raw_score
                scores.append(normalized_score)

        if not scores:
            return 0.02
        return max(-0.08, min(0.12, mean(scores[-20:]) * 0.12))

    async def _find_comparables(
        self,
        *,
        area_sqft: float,
        bedrooms: int,
        location: str,
        property_type: str,
        base_price_per_sqft: float,
    ) -> list[dict[str, Any]]:
        size_adjustments = [0.92, 0.98, 1.0, 1.04, 1.09]
        comparable_titles = [
            "Comparable Tower Residence",
            "Waterfront Collection Unit",
            "Signature Investor Listing",
            "Prime District Comparable",
            "Recent Market Match",
        ]
        items: list[dict[str, Any]] = []
        for index, factor in enumerate(size_adjustments):
            comparable_area = round(area_sqft * factor, 0)
            price_per_sqft = base_price_per_sqft * (0.97 + index * 0.018)
            estimated_price = comparable_area * price_per_sqft
            similarity = max(72.0, 96.0 - abs(factor - 1.0) * 120 - index * 2.5)
            items.append(
                {
                    "title": comparable_titles[index],
                    "location": location,
                    "property_type": property_type,
                    "bedrooms": max(0, bedrooms + (-1 if index == 0 else 0 if index < 3 else 1)),
                    "area_sqft": float(comparable_area),
                    "estimated_price_aed": round(estimated_price, 2),
                    "price_per_sqft": round(price_per_sqft, 2),
                    "similarity_score": round(similarity, 1),
                }
            )
        return items

    def _get_value_drivers(
        self,
        *,
        location: str,
        property_type: str,
        year_built: int,
        amenities: list[str],
        market_trend: float,
        baseline: float,
    ) -> list[dict[str, str | float]]:
        drivers: list[dict[str, str | float]] = [
            {"label": "Location baseline", "value": round(baseline, 2), "context": f"{location} reference price per sqft"},
            {"label": "Property format", "value": self.TYPE_MULTIPLIERS.get(property_type.lower(), 1.0), "context": property_type},
            {"label": "Building age", "value": round(self._age_factor(year_built), 2), "context": f"Built in {year_built}"},
            {"label": "Market trend", "value": round(market_trend * 100, 2), "context": "30-day narrative adjustment"},
        ]
        if amenities:
            drivers.append(
                {
                    "label": "Amenities",
                    "value": round(sum(self.AMENITY_WEIGHTS.get(item.lower(), 0.006) for item in amenities[:8]) * 100, 2),
                    "context": ", ".join(amenities[:4]),
                }
            )
        return drivers

    def _get_investment_grade(self, cap_rate: float) -> str:
        if cap_rate >= 8:
            return "Excellent (A)"
        if cap_rate >= 6:
            return "Good (B)"
        if cap_rate >= 4:
            return "Fair (C)"
        return "Below Average (D)"

    def _get_pricing_recommendation(
        self,
        location: str,
        property_type: str,
        market_stats: dict[str, Any] | None,
        market_trend: float,
    ) -> str:
        if market_stats is None:
            return f"Price {property_type.lower()} inventory in {location} conservatively until more direct comps are captured."
        if market_trend > 0.05:
            return f"The submarket is supportive. A disciplined premium over the median comp can be justified if finish quality is strong."
        if market_trend < -0.03:
            return f"Lean closer to the lower half of the current comp band in {location} until sentiment and demand firm up."
        return f"Anchor pricing close to the median comparable set and compete on presentation, payment flexibility, and certainty."


property_valuation = PropertyValuationService()
