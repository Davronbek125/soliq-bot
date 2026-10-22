"""
2026-yilgi O'zbekiston Soliq Qonunchiligi asosidagi soliq hisoblash va optimallashtirish dvigateli.
Asosiy me'yoriy hujjatlar:
- PQ-247-son (12.08.2025)
- O'RQ-1108-son (25.12.2025)
- O'RQ-1126-son (27.03.2026)
- Soliq kodeksi (2026-yil tahriri)
"""

from dataclasses import dataclass
from typing import Dict, Any, List

# Asosiy doimiy ko'rsatkichlar (2026)
BHM = 412_000  # Bazaviy hisoblash miqdori (so'm)
MHEKM = 1_360_000  # Mehnatga haq to'lashning eng kam miqdori (so'm)

LIMIT_YATT_1_PERCENT = 1_000_000_000  # 1 milliard so'm (1% stavka chegarasi)
LIMIT_SMALL_BIZ_TURNOVER = 5_000_000_000  # 5 milliard so'm (QQSga o'tish chegarasi)

RATE_YATT_1_PERCENT = 0.01  # 1%
RATE_TURNOVER_TAX_BASE = 0.04  # 4%
RATE_CATERING_SIMPLIFIED_VAT = 0.06  # 6% (Umumiy ovqatlanish va xizmatlar soddalashtirilgan QQS)
RATE_VAT_STANDARD = 0.12  # 12% QQS
RATE_PROFIT_TAX_BASE = 0.15  # 15% Foyda solig'i
RATE_INCOME_TAX_JSHDS = 0.12  # 12% JShDS
RATE_SOCIAL_TAX_PRIVATE = 0.12  # 12% Ijtimoiy soliq (xususiy sektor)
RATE_PROPERTY_TAX_LEGAL = 0.015  # 1.5% Mol-mulk solig'i


@dataclass
class TaxCalculationResult:
    category: str
    annual_revenue: float
    turnover_tax: float
    vat: float
    profit_tax: float
    social_tax: float
    income_tax: float
    total_tax_burden: float
    effective_rate_percent: float
    legal_notes: List[str]
    recommendations: List[str]


def calculate_self_employed(annual_revenue: float, pay_social_tax: bool = True) -> TaxCalculationResult:
    """O'zini o'zi band qilgan shaxslar solig'ini hisoblash (PQ-247 bo'yicha)."""
    legal_notes = [
        "PQ-247-son qaror: 100 mln so'mlik aylanma solig'idan ozod etish bekor qilingan.",
        "1 milliard so'mgacha bo'lgan tushumga 1% lik aylanma solig'i qo'llanadi."
    ]
    recommendations = []

    if annual_revenue <= LIMIT_YATT_1_PERCENT:
        turnover_tax = annual_revenue * RATE_YATT_1_PERCENT
    else:
        # 1 mlrddan oshganda
        turnover_tax = (LIMIT_YATT_1_PERCENT * RATE_YATT_1_PERCENT) + \
                       ((annual_revenue - LIMIT_YATT_1_PERCENT) * RATE_TURNOVER_TAX_BASE)
        recommendations.append(
            "Yillik daromadingiz 1 mlrd so'mdan oshdi. 1 mlrddan yuqori qismiga 4% stavka hisoblanadi. "
            "YaTT yoki yuridik shaxs (MChJ) shakliga o'tishni ko'rib chiqing."
        )

    # Ijtimoiy soliq (mehnat staji uchun ixtiyoriy, ammo tavsiya etiladi - yiliga kamida 1 BHM)
    social_tax = (1 * BHM) if pay_social_tax else 0
    if pay_social_tax:
        legal_notes.append("Ijtimoiy soliq: Pensiya staji uchun yiliga 1 BHM (412 000 so'm) to'lanadi.")

    total_tax = turnover_tax + social_tax
    effective_rate = (total_tax / annual_revenue * 100) if annual_revenue > 0 else 0

    return TaxCalculationResult(
        category="O'zini o'zi band qilgan shaxs",
        annual_revenue=annual_revenue,
        turnover_tax=turnover_tax,
        vat=0,
        profit_tax=0,
        social_tax=social_tax,
        income_tax=0,
        total_tax_burden=total_tax,
        effective_rate_percent=effective_rate,
        legal_notes=legal_notes,
        recommendations=recommendations
    )


def calculate_yatt(annual_revenue: float, employees_count: int = 0, avg_employee_salary: float = 0) -> TaxCalculationResult:
    """Yakka tartibdagi tadbirkor (YaTT) solig'ini hisoblash (2026-yilgi me'yorlar)."""
    legal_notes = [
        "PQ-247-son: YaTTlar uchun qat'iy belgilangan daromad solig'i to'liq bekor qilingan.",
        "1 milliard so'mgacha bo'lgan aylanmaga 1% aylanma solig'i belgilanadi."
    ]
    recommendations = []

    # Aylanma solig'i
    if annual_revenue <= LIMIT_YATT_1_PERCENT:
        turnover_tax = annual_revenue * RATE_YATT_1_PERCENT
    elif annual_revenue <= LIMIT_SMALL_BIZ_TURNOVER:
        turnover_tax = (LIMIT_YATT_1_PERCENT * RATE_YATT_1_PERCENT) + \
                       ((annual_revenue - LIMIT_YATT_1_PERCENT) * RATE_TURNOVER_TAX_BASE)
        legal_notes.append(
            "2026-yil 1-iyundagi chegara bo'yicha tushum 5 mlrd so'mgacha bo'lsa, YaTT QQS to'lamaydi, "
            "1 mlrddan oshgan qismiga 4% aylanma solig'i to'laydi."
        )
    else:
        # 5 mlrddan oshganda QQSga o'tish majburiy
        turnover_tax = 0
        recommendations.append(
            "DIQQAT: Yillik aylanma 5 mlrd so'mdan oshdi. YaTT majburiy ravishda QQS (12%) to'lashga o'tadi. "
            "Bunday hajmda biznesni MChJga aylantirish tavsiya etiladi."
        )

    vat = 0
    profit_tax = 0
    if annual_revenue > LIMIT_SMALL_BIZ_TURNOVER:
        vat = annual_revenue * RATE_VAT_STANDARD
        profit_tax = (annual_revenue * 0.20) * RATE_INCOME_TAX_JSHDS  # taxminiy rentabellik 20%

    # YaTTning o'zi uchun ijtimoiy soliq (har oyda 1 BHM)
    yatt_social_tax = 1 * BHM * 12

    # Yollangan xodimlar uchun ijtimoiy soliq va JShDS
    employees_payroll = employees_count * avg_employee_salary * 12
    employees_social_tax = employees_payroll * RATE_SOCIAL_TAX_PRIVATE
    employees_income_tax = employees_payroll * RATE_INCOME_TAX_JSHDS

    total_social = yatt_social_tax + employees_social_tax
    total_tax = turnover_tax + vat + profit_tax + total_social + employees_income_tax
    effective_rate = (total_tax / annual_revenue * 100) if annual_revenue > 0 else 0

    return TaxCalculationResult(
        category="Yakka tartibdagi tadbirkor (YaTT)",
        annual_revenue=annual_revenue,
        turnover_tax=turnover_tax,
        vat=vat,
        profit_tax=profit_tax,
        social_tax=total_social,
        income_tax=employees_income_tax,
        total_tax_burden=total_tax,
        effective_rate_percent=effective_rate,
        legal_notes=legal_notes,
        recommendations=recommendations
    )


def calculate_llc(annual_revenue: float, documented_expenses: float = 0,
                  employees_count: int = 1, avg_employee_salary: float = 2_000_000,
                  sector: str = "general") -> TaxCalculationResult:
    """
    Yuridik shaxs (MChJ) solig'ini hisoblash.
    sector: 'general', 'catering_retail' (umumiy ovqatlanish/chakana savdo), 'it_park'
    """
    legal_notes = []
    recommendations = []

    payroll_annual = employees_count * avg_employee_salary * 12
    social_tax = payroll_annual * RATE_SOCIAL_TAX_PRIVATE
    income_tax = payroll_annual * RATE_INCOME_TAX_JSHDS

    turnover_tax = 0
    vat = 0
    profit_tax = 0

    if sector == "it_park":
        # IT Park rezidenti imtiyozlari (2040-yilgacha)
        turnover_tax = 0
        profit_tax = 0
        vat = 0
        social_tax = 0
        income_tax = payroll_annual * 0.075  # 7.5% JShDS
        legal_notes.append("IT-Park rezidenti: Foyda solig'i, ijtimoiy soliq va aylanma solig'i 0%, JShDS xodimlar uchun 7.5%.")
    elif annual_revenue <= LIMIT_SMALL_BIZ_TURNOVER:
        # Soddalashtirilgan rejim (5 mlrd gacha)
        legal_notes.append("2026-yil 1-iyundan 5 milliard so'mgacha aylanmaga ega MChJ aylanmadan olinadigan soliq to'lovchisi hisoblanadi.")
        if sector == "catering_retail":
            # Muqobil 6% QQS varianti
            turnover_tax = 0
            vat = annual_revenue * RATE_CATERING_SIMPLIFIED_VAT
            profit_tax = 0
            legal_notes.append("Umumiy ovqatlanish/chakana savdo: Foyda solig'isiz 6% soddalashtirilgan QQS qo'llandi.")
        else:
            turnover_tax = annual_revenue * RATE_TURNOVER_TAX_BASE
            legal_notes.append("Standart aylanma solig'i stavkasi: 4%.")
    else:
        # 5 mlrddan oshganda majburiy umumiy rejim (QQS 12% + Foyda 15%)
        legal_notes.append("Tushum 5 mlrd so'mdan oshgani sababli umumiy soliq tizimi (12% QQS va 15% Foyda) majburiydir.")
        # Hisobga olinadigan QQSni taxminan xarajatlar ichidan 12% deb olamiz
        input_vat = (documented_expenses * (RATE_VAT_STANDARD / (1 + RATE_VAT_STANDARD)))
        vat = max(0, (annual_revenue * RATE_VAT_STANDARD) - input_vat)

        net_profit_base = max(0, annual_revenue - documented_expenses - payroll_annual - social_tax)
        profit_tax = net_profit_base * RATE_PROFIT_TAX_BASE

        if annual_revenue > 20_000_000_000:
            legal_notes.append("Yillik tushum 20 mlrd so'mdan oshdi: Oylik avans to'lovlari majburiydir (O'RQ-1108).")

    total_tax = turnover_tax + vat + profit_tax + social_tax + income_tax
    effective_rate = (total_tax / annual_revenue * 100) if annual_revenue > 0 else 0

    return TaxCalculationResult(
        category=f"MChJ ({sector})",
        annual_revenue=annual_revenue,
        turnover_tax=turnover_tax,
        vat=vat,
        profit_tax=profit_tax,
        social_tax=social_tax,
        income_tax=income_tax,
        total_tax_burden=total_tax,
        effective_rate_percent=effective_rate,
        legal_notes=legal_notes,
        recommendations=recommendations
    )


def compare_all_regimes(annual_revenue: float, documented_expenses: float = 0,
                        employees_count: int = 1, avg_employee_salary: float = 3_000_000) -> Dict[str, Any]:
    """Barcha rejimlar bo'yicha qiyosiy tahlil va optimal rejim tavsiyasi."""
    results = {}

    if annual_revenue <= LIMIT_YATT_1_PERCENT:
        results["self_employed"] = calculate_self_employed(annual_revenue)
        results["yatt"] = calculate_yatt(annual_revenue, employees_count, avg_employee_salary)
    elif annual_revenue <= LIMIT_SMALL_BIZ_TURNOVER:
        results["yatt"] = calculate_yatt(annual_revenue, employees_count, avg_employee_salary)

    results["llc_turnover_tax"] = calculate_llc(annual_revenue, documented_expenses, employees_count, avg_employee_salary, "general")
    results["llc_catering_simplified"] = calculate_llc(annual_revenue, documented_expenses, employees_count, avg_employee_salary, "catering_retail")
    results["llc_general_vat"] = calculate_llc(annual_revenue, documented_expenses, employees_count, avg_employee_salary, "general_vat_mode")

    # Eng kam soliq yukini aniqlash
    best_key = min(results, key=lambda k: results[k].total_tax_burden)
    best_option = results[best_key]

    return {
        "annual_revenue": annual_revenue,
        "best_option": best_option,
        "best_key": best_key,
        "all_results": results
    }
