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


class TaxCalculator(object):
    base_income = 0
    contract_type = ""

    retirement_tax = 0
    pension_tax = 0
    sickness_tax = 0
 
    deductible_expenses = 0.0
    health_insurance_tax = 0
    deductible_health_tax = 0
    tax_rate = 0
    tax_free_income = 0.0
    advance_tax = 0
    base_advance_tax = 0

    @staticmethod
    def main():
        try:
            TaxCalculator.base_income=float(input("Enter income: "))
            TaxCalculator.contract_type=input("Contract Type: (E)mployment, (C)ivil")[0]
        except ValueError:
            print("Incorrect")
            return

        if TaxCalculator.contract_type==ContractType.EMPLOYMENT.value:
            print("EMPLOYMENT")
        elif TaxCalculator.contract_type==ContractType.CIVIL.value:
            print("CIVIL")
        else:
            print("Unknown type of contract.")
            return

        result = TaxCalculator.calculate_summary()
        TaxCalculator.print_report(result)

    @staticmethod
    def calculate_summary():
        social_security_base = TaxCalculator.calculate_income(TaxCalculator.base_income)
        TaxCalculator.calculate_other_taxes(social_security_base)

        if TaxCalculator.contract_type==ContractType.EMPLOYMENT.value:
            TaxCalculator.deductible_expenses = TaxRates.DEFAULT_EMPLOYMENT_EXPENSES
            TaxCalculator.tax_free_income = TaxRates.DEFAULT_TAX_FREE_INCOME
        else:
            TaxCalculator.deductible_expenses = social_security_base * TaxRates.CIVIL_EXPENSE_RATE
            TaxCalculator.tax_free_income = 0.0

        taxable_income = social_security_base - TaxCalculator.deductible_expenses
        rounded_taxable_income = float(round(taxable_income))
        TaxCalculator.calculate_tax(rounded_taxable_income)

        if TaxCalculator.contract_type==ContractType.EMPLOYMENT.value:
            tax_paid = TaxCalculator.tax_rate - TaxCalculator.tax_free_income
        else:
            tax_paid = TaxCalculator.tax_rate

        TaxCalculator.calculate_advance_tax()
        TaxCalculator.base_advance_tax = float("{0:.0f}".format(TaxCalculator.advance_tax))
        net_income = TaxCalculator.base_income - ((TaxCalculator.retirement_tax + TaxCalculator.pension_tax + TaxCalculator.sickness_tax) + TaxCalculator.health_insurance_tax + TaxCalculator.base_advance_tax)

        return {
            "base_income": TaxCalculator.base_income,
            "contract_type": TaxCalculator.contract_type,
            "social_security_base": social_security_base,
            "retirement_tax": TaxCalculator.retirement_tax,
            "pension_tax": TaxCalculator.pension_tax,
            "sickness_tax": TaxCalculator.sickness_tax,
            "health_insurance_tax": TaxCalculator.health_insurance_tax,
            "deductible_health_tax": TaxCalculator.deductible_health_tax,
            "deductible_expenses": TaxCalculator.deductible_expenses,
            "taxable_income": taxable_income,
            "rounded_taxable_income": rounded_taxable_income,
            "tax_rate": TaxCalculator.tax_rate,
            "tax_free_income": TaxCalculator.tax_free_income,
            "tax_paid": tax_paid,
            "advance_tax": TaxCalculator.advance_tax,
            "base_advance_tax": TaxCalculator.base_advance_tax,
            "net_income": net_income,
        }

    @staticmethod
    def print_report(data):
        print("Income ", data["base_income"])
        print("Social security tax: "+"{0:.2f}".format(data["retirement_tax"]))
        print("Health social security tax: "+"{0:.2f}".format(data["pension_tax"]))
        print("Sickness social security tax: "+"{0:.2f}".format(data["sickness_tax"]))
        print("Income basis for healt social security: ", data["social_security_base"])
        print("Healt social security tax: 9% = " + "{0:.2f}".format(data["health_insurance_tax"]) + " 7,75% = " + "{0:.2f}".format(data["deductible_health_tax"]))
        print("Tax deductible expenses: ", data["deductible_expenses"])
        print("Income: ", data["taxable_income"], " rounded: "+"{0:.0f}".format(data["rounded_taxable_income"]))
        print("Advance tax 18% = ", data["tax_rate"])

        if data["contract_type"]==ContractType.EMPLOYMENT.value:
            print("Tax free income =", data["tax_free_income"])
            print("Reduced tax = "+"{0:.2f}".format(data["tax_paid"]))
        else:
            print("Already paid tax = "+"{0:.2f}".format(data["tax_paid"]))

        print("Advance paid tax = "+"{0:.2f}".format(data["advance_tax"]) + " rounded "+"{0:.0f}".format(data["base_advance_tax"]))
        print()
        print("Net income = "+"{0:.2f}".format(data["net_income"]))

    @staticmethod
    def calculate_advance_tax():
        TaxCalculator.advance_tax=TaxCalculator.tax_rate - TaxCalculator.deductible_health_tax - TaxCalculator.tax_free_income

    @staticmethod
    def calculate_tax(income):
        TaxCalculator.tax_rate = income * TaxRates.PIT_RATE

    @staticmethod
    def calculate_income(income):
        TaxCalculator.retirement_tax = income * TaxRates.RETIREMENT_RATE      
        TaxCalculator.pension_tax = income * TaxRates.PENSION_RATE
        TaxCalculator.sickness_tax = income * TaxRates.SICKNESS_RATE
        return (income - TaxCalculator.retirement_tax- TaxCalculator.pension_tax - TaxCalculator.sickness_tax)

    @staticmethod
    def calculate_other_taxes(income):
        TaxCalculator.health_insurance_tax = income * TaxRates.HEALTH_INSURANCE_RATE
        TaxCalculator.deductible_health_tax = income * TaxRates.DEDUCTIBLE_HEALTH_RATE

        
if __name__=='__main__':
    TaxCalculator.main()