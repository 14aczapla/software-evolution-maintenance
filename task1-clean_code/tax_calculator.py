from abc import ABC, abstractmethod
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum


class ContractType(Enum):
    EMPLOYMENT = "E"
    CIVIL = "C"


class TaxRates:
    RETIREMENT_RATE = Decimal("0.0976")
    PENSION_RATE = Decimal("0.0150")
    SICKNESS_RATE = Decimal("0.0245")
    HEALTH_INSURANCE_RATE = Decimal("0.0900")
    DEDUCTIBLE_HEALTH_RATE = Decimal("0.0775")
    PIT_RATE = Decimal("0.1800")
    CIVIL_EXPENSE_RATE = Decimal("0.2000")
    DEFAULT_EMPLOYMENT_EXPENSES = Decimal("111.25")
    DEFAULT_TAX_FREE_INCOME = Decimal("46.33")


class Contract(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def calculate_deductible_expenses(self, social_security_base: Decimal) -> Decimal:
        pass

    @abstractmethod
    def get_tax_free_income(self) -> Decimal:
        pass

    @abstractmethod
    def calculate_tax_paid(self, tax_rate: Decimal, tax_free_income: Decimal) -> Decimal:
        pass


class EmploymentContract(Contract):
    def __init__(self):
        super().__init__("EMPLOYMENT")

    def calculate_deductible_expenses(self, social_security_base: Decimal) -> Decimal:
        return TaxRates.DEFAULT_EMPLOYMENT_EXPENSES

    def get_tax_free_income(self) -> Decimal:
        return TaxRates.DEFAULT_TAX_FREE_INCOME

    def calculate_tax_paid(self, tax_rate: Decimal, tax_free_income: Decimal) -> Decimal:
        return tax_rate - tax_free_income


class CivilContract(Contract):
    def __init__(self):
        super().__init__("CIVIL")

    def calculate_deductible_expenses(self, social_security_base: Decimal) -> Decimal:
        return social_security_base * TaxRates.CIVIL_EXPENSE_RATE

    def get_tax_free_income(self) -> Decimal:
        return Decimal("0.00")

    def calculate_tax_paid(self, tax_rate: Decimal, tax_free_income: Decimal) -> Decimal:
        return tax_rate


class ContractFactory:
    @staticmethod
    def create_contract(contract_type: str) -> Contract:
        if contract_type == ContractType.EMPLOYMENT.value:
            return EmploymentContract()
        elif contract_type == ContractType.CIVIL.value:
            return CivilContract()
        else:
            raise ValueError(f"Unknown contract type: {contract_type}")


class TaxCalculator:
    def __init__(self, base_income: Decimal, contract: Contract):
        self.base_income = base_income
        self.contract = contract
        
        self.retirement_tax = Decimal("0.00")
        self.pension_tax = Decimal("0.00")
        self.sickness_tax = Decimal("0.00")
        self.deductible_expenses = Decimal("0.00")
        self.health_insurance_tax = Decimal("0.00")
        self.deductible_health_tax = Decimal("0.00")
        self.tax_rate = Decimal("0.00")
        self.tax_free_income = Decimal("0.00")
        self.advance_tax = Decimal("0.00")
        self.base_advance_tax = Decimal("0.00")

    def calculate_summary(self):
        social_security_base = self.calculate_income(self.base_income)
        self.calculate_other_taxes(social_security_base)

        self.deductible_expenses = self.contract.calculate_deductible_expenses(social_security_base)
        self.tax_free_income = self.contract.get_tax_free_income()

        taxable_income = social_security_base - self.deductible_expenses
        rounded_taxable_income = taxable_income.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        self.calculate_tax(rounded_taxable_income)

        tax_paid = self.contract.calculate_tax_paid(self.tax_rate, self.tax_free_income)

        self.calculate_advance_tax()
        self.base_advance_tax = self.advance_tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        
        total_deductions = (self.retirement_tax + self.pension_tax + self.sickness_tax + 
                            self.health_insurance_tax + self.base_advance_tax)
        net_income = self.base_income - total_deductions

        return {
            "base_income": self.base_income,
            "contract_name": self.contract.name,
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

    def calculate_tax(self, income: Decimal):
        self.tax_rate = income * TaxRates.PIT_RATE

    def calculate_income(self, income: Decimal):
        self.retirement_tax = income * TaxRates.RETIREMENT_RATE
        self.pension_tax = income * TaxRates.PENSION_RATE
        self.sickness_tax = income * TaxRates.SICKNESS_RATE
        return income - self.retirement_tax - self.pension_tax - self.sickness_tax

    def calculate_other_taxes(self, income: Decimal):
        self.health_insurance_tax = income * TaxRates.HEALTH_INSURANCE_RATE
        self.deductible_health_tax = income * TaxRates.DEDUCTIBLE_HEALTH_RATE


class TaxReportPrinter:
    @staticmethod
    def print_report(data):
        print("Income ", data["base_income"])
        print("Social security tax: " + "{:.2f}".format(data["retirement_tax"]))
        print("Health social security tax: " + "{:.2f}".format(data["pension_tax"]))
        print("Sickness social security tax: " + "{:.2f}".format(data["sickness_tax"]))
        print("Income basis for health social security: ", data["social_security_base"])
        print("Health social security tax: 9% = " + "{:.2f}".format(data["health_insurance_tax"]) + 
              " 7,75% = " + "{:.2f}".format(data["deductible_health_tax"]))
        print("Tax deductible expenses: ", data["deductible_expenses"])
        print("Income: ", data["taxable_income"], " rounded: " + "{:.0f}".format(data["rounded_taxable_income"]))
        print("Advance tax 18% = ", data["tax_rate"])

        if data["contract_name"] == "EMPLOYMENT":
            print("Tax free income =", data["tax_free_income"])
            print("Reduced tax = " + "{:.2f}".format(data["tax_paid"]))
        else:
            print("Already paid tax = " + "{:.2f}".format(data["tax_paid"]))

        print("Advance paid tax = " + "{:.2f}".format(data["advance_tax"]) + " rounded " + "{:.0f}".format(data["base_advance_tax"]))
        print("\nNet income = " + "{:.2f}".format(data["net_income"]))


def main():
    try:
        base_income_input = input("Enter income: ").strip()
        base_income = Decimal(base_income_input)
        contract_type_input = input("Contract Type: (E)mployment, (C)ivil: ").strip().upper()
        if not contract_type_input:
            raise ValueError
        contract_type = contract_type_input[0]
        
        contract = ContractFactory.create_contract(contract_type)
    except Exception:
        print("Incorrect input or unknown contract type.")
        return

    print(contract.name)

    calculator = TaxCalculator(base_income, contract)
    result = calculator.calculate_summary()
    
    TaxReportPrinter.print_report(result)


if __name__ == '__main__':
    main()