from enum import Enum


class ContractType(Enum):
    EMPLOYMENT = "E"
    CIVIL = "C"


class TaxRates:
    RETIREMENT_RATE = 0.0976
    PENSION_RATE = 0.0150
    SICKNESS_RATE = 0.0245
    HEALTH_INSURANCE_RATE = 0.0900
    DEDUCTIBLE_HEALTH_RATE = 0.0775
    PIT_RATE = 0.1800
    CIVIL_EXPENSE_RATE = 0.2000
    DEFAULT_EMPLOYMENT_EXPENSES = 111.25
    DEFAULT_TAX_FREE_INCOME = 46.33


class TaxCalculator:
    def __init__(self, base_income: float, contract_type: str):
        self.base_income = base_income
        self.contract_type = contract_type
        
        self.retirement_tax = 0.0
        self.pension_tax = 0.0
        self.sickness_tax = 0.0
        self.deductible_expenses = 0.0
        self.health_insurance_tax = 0.0
        self.deductible_health_tax = 0.0
        self.tax_rate = 0.0
        self.tax_free_income = 0.0
        self.advance_tax = 0.0
        self.base_advance_tax = 0.0

    def calculate_summary(self):
        social_security_base = self.calculate_income(self.base_income)
        self.calculate_other_taxes(social_security_base)

        if self.contract_type == ContractType.EMPLOYMENT.value:
            self.deductible_expenses = TaxRates.DEFAULT_EMPLOYMENT_EXPENSES
            self.tax_free_income = TaxRates.DEFAULT_TAX_FREE_INCOME
        else:
            self.deductible_expenses = social_security_base * TaxRates.CIVIL_EXPENSE_RATE
            self.tax_free_income = 0.0

        taxable_income = social_security_base - self.deductible_expenses
        rounded_taxable_income = float(round(taxable_income))
        self.calculate_tax(rounded_taxable_income)

        if self.contract_type == ContractType.EMPLOYMENT.value:
            tax_paid = self.tax_rate - self.tax_free_income
        else:
            tax_paid = self.tax_rate

        self.calculate_advance_tax()
        self.base_advance_tax = float("{0:.0f}".format(self.advance_tax))
        
        total_deductions = (self.retirement_tax + self.pension_tax + self.sickness_tax + 
                            self.health_insurance_tax + self.base_advance_tax)
        net_income = self.base_income - total_deductions

        return {
            "base_income": self.base_income,
            "contract_type": self.contract_type,
            "social_security_base": social_security_base,
            "retirement_tax": self.retirement_tax,
            "pension_tax": self.pension_tax,
            "sickness_tax": self.sickness_tax,
            "health_insurance_tax": self.health_insurance_tax,
            "deductible_health_tax": self.deductible_health_tax,
            "deductible_expenses": self.deductible_expenses,
            "taxable_income": taxable_income,
            "rounded_taxable_income": rounded_taxable_income,
            "tax_rate": self.tax_rate,
            "tax_free_income": self.tax_free_income,
            "tax_paid": tax_paid,
            "advance_tax": self.advance_tax,
            "base_advance_tax": self.base_advance_tax,
            "net_income": net_income,
        }

    def calculate_advance_tax(self):
        self.advance_tax = self.tax_rate - self.deductible_health_tax - self.tax_free_income

    def calculate_tax(self, income):
        self.tax_rate = income * TaxRates.PIT_RATE

    def calculate_income(self, income):
        self.retirement_tax = income * TaxRates.RETIREMENT_RATE
        self.pension_tax = income * TaxRates.PENSION_RATE
        self.sickness_tax = income * TaxRates.SICKNESS_RATE
        return income - self.retirement_tax - self.pension_tax - self.sickness_tax

    def calculate_other_taxes(self, income):
        self.health_insurance_tax = income * TaxRates.HEALTH_INSURANCE_RATE
        self.deductible_health_tax = income * TaxRates.DEDUCTIBLE_HEALTH_RATE

    def print_report(self, data):
        print("Income ", data["base_income"])
        print("Social security tax: " + "{0:.2f}".format(data["retirement_tax"]))
        print("Health social security tax: " + "{0:.2f}".format(data["pension_tax"]))
        print("Sickness social security tax: " + "{0:.2f}".format(data["sickness_tax"]))
        print("Income basis for health social security: ", data["social_security_base"])
        print("Health social security tax: 9% = " + "{0:.2f}".format(data["health_insurance_tax"]) + 
              " 7,75% = " + "{0:.2f}".format(data["deductible_health_tax"]))
        print("Tax deductible expenses: ", data["deductible_expenses"])
        print("Income: ", data["taxable_income"], " rounded: " + "{0:.0f}".format(data["rounded_taxable_income"]))
        print("Advance tax 18% = ", data["tax_rate"])

        if data["contract_type"] == ContractType.EMPLOYMENT.value:
            print("Tax free income =", data["tax_free_income"])
            print("Reduced tax = " + "{0:.2f}".format(data["tax_paid"]))
        else:
            print("Already paid tax = " + "{0:.2f}".format(data["tax_paid"]))

        print("Advance paid tax = " + "{0:.2f}".format(data["advance_tax"]) + " rounded " + "{0:.0f}".format(data["base_advance_tax"]))
        print("\nNet income = " + "{0:.2f}".format(data["net_income"]))


def main():
    try:
        base_income = float(input("Enter income: "))
        contract_type_input = input("Contract Type: (E)mployment, (C)ivil: ").strip().upper()
        if not contract_type_input:
            raise ValueError
        contract_type = contract_type_input[0]
    except ValueError:
        print("Incorrect input")
        return

    if contract_type == ContractType.EMPLOYMENT.value:
        print("EMPLOYMENT")
    elif contract_type == ContractType.CIVIL.value:
        print("CIVIL")
    else:
        print("Unknown type of contract.")
        return

    calculator = TaxCalculator(base_income, contract_type)
    result = calculator.calculate_summary()
    calculator.print_report(result)


if __name__ == '__main__':
    main()