from services.tax_engine import calculate_self_employed, calculate_yatt, calculate_llc, compare_all_regimes

print("--- O'zini o'zi band qilgan (50 mln) ---")
r0 = calculate_self_employed(50_000_000)
print(f"{r0.category}: Jami soliq = {r0.total_tax_burden:,.0f} so'm, samaradorlik = {r0.effective_rate_percent:.2f}%")

print("\n--- YaTT (500 mln) ---")
r1 = calculate_yatt(500_000_000)
print(f"{r1.category}: Jami soliq = {r1.total_tax_burden:,.0f} so'm, samaradorlik = {r1.effective_rate_percent:.2f}%")

print("\n--- YaTT (2 mlrd) ---")
r2 = calculate_yatt(2_000_000_000)
print(f"{r2.category}: Jami soliq = {r2.total_tax_burden:,.0f} so'm, samaradorlik = {r2.effective_rate_percent:.2f}%")

print("\n--- Taqqoslash (800 mln) ---")
cmp_res = compare_all_regimes(800_000_000, documented_expenses=400_000_000, employees_count=2)
best = cmp_res["best_option"]
print(f"Tavsiya etilgan: {best.category} | Jami soliq = {best.total_tax_burden:,.0f} so'm | {best.effective_rate_percent:.2f}%")
for opt_name, opt_res in cmp_res["all_results"].items():
    print(f"  * {opt_res.category}: {opt_res.total_tax_burden:,.0f} so'm ({opt_res.effective_rate_percent:.2f}%)")
