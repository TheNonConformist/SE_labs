CATEGORIES = {"P": "Individual", "C": "Company", "H": "HUF", "F": "Firm"}

def parse_income(income):
    if not isinstance(income, str):
        raise ValueError("income must be given as text")
    cleaned = income.replace(',', '').strip()
    if not cleaned:
        raise ValueError("income is empty")
    try:
        return int(cleaned)
    except ValueError:
        raise ValueError(f"'{income}' is not a valid income") from None

def monthly_emi(details):
    if not isinstance(details, str):
        raise ValueError("details must be given as 'principal,rate,years'")
    parts = [part.strip() for part in details.split(',')]
    if len(parts) != 3:
        raise ValueError("expected exactly three values: principal,rate,years")
    try:
        principal, rate, years = (int(part) for part in parts)
    except ValueError:
        raise ValueError("principal, rate and years must be integers") from None
    if principal <= 0 or rate <= 0 or years <= 0:
        raise ValueError("principal, rate and years must be positive")
    if principal > 10**12:
        raise ValueError("principal is too large")
    if rate > 100:
        raise ValueError("rate must be at most 100")
    if years > 50:
        raise ValueError("years must be at most 50")
    r = rate / 1200
    n = years * 12
    return round(principal * r * (1 + r) ** n / ((1 + r) ** n - 1), 2)

def pan_category(pan):
    if not isinstance(pan, str):
        raise ValueError("PAN must be given as text")
    pan = pan.strip().upper()
    if len(pan) != 10:
        raise ValueError("PAN must be exactly 10 characters")
    if pan[3] not in CATEGORIES:
        raise ValueError(f"'{pan[3]}' is not a valid PAN category (P, C, H or F)")
    return CATEGORIES[pan[3]]

def main():
    print("==== Running parse_income ====")
    user_input = input("Enter monthly income (e.g. 50,000): ")
    result = parse_income(user_input)
    print("Income:", result)

    print("\n==== Running monthly_emi ====")
    user_input = input("Enter principal,rate,years (e.g. 500000,10,5): ")
    result = monthly_emi(user_input)
    print("Monthly EMI:", result)

    print("\n==== Running pan_category ====")
    user_input = input("Enter a PAN number (e.g. ABCPE1234F): ")
    result = pan_category(user_input)
    print("PAN Category:", result)

if __name__ == "__main__":
    main()
