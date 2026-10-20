from dataclasses import dataclass
from enum import Enum


class ContractType(Enum):
    EMPLOYMENT = "E"
    CIVIL = "C"

@dataclass(frozen=True)
class TaxRates:
    RETIREMENT_RATE: float = 0.0976
    PENSION_RATE: float = 0.0150
    SICKNESS_RATE: float = 0.0245
    HEALTH_INSURANCE_RATE: float = 0.0900
    DEDUCTIBLE_HEALTH_RATE: float = 0.0775
    PIT_RATE: float = 0.1800
    CIVIL_EXPENSE_RATE: float = 0.2000
    DEFAULT_EMPLOYMENT_EXPENSES: float = 111.25
    DEFAULT_TAX_FREE_INCOME: float = 46.33


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
        
        print("Income ", TaxCalculator.base_income)
        social_security_base = TaxCalculator.calculate_income(TaxCalculator.base_income)
        print("Social security tax: "+"{0:.2f}".format(TaxCalculator.retirement_tax))
        print("Health social security tax: "+"{0:.2f}".format(TaxCalculator.pension_tax))
        print("Sickness social security tax: "+"{0:.2f}".format(TaxCalculator.sickness_tax))
        print("Income basis for healt social security: ",social_security_base)
        
        TaxCalculator.calculate_other_taxes(social_security_base)
        print("Healt social security tax: 9% = " \
              +"{0:.2f}".format(TaxCalculator.health_insurance_tax)+" 7,75% = "+"{0:.2f}".format(TaxCalculator.deductible_health_tax))
        
        if TaxCalculator.contract_type==ContractType.EMPLOYMENT.value:
            TaxCalculator.deductible_expenses = TaxRates.DEFAULT_EMPLOYMENT_EXPENSES
            TaxCalculator.tax_free_income = TaxRates.DEFAULT_TAX_FREE_INCOME
        else:
            TaxCalculator.deductible_expenses = social_security_base * TaxRates.CIVIL_EXPENSE_RATE
            TaxCalculator.tax_free_income = 0.0

        print("Tax deductible expenses: ",TaxCalculator.deductible_expenses)

        taxable_income = social_security_base - TaxCalculator.deductible_expenses
        rounded_taxable_income = float(round(taxable_income))


        print("Income: ",taxable_income," rounded: "+"{0:.0f}".format(rounded_taxable_income))
        TaxCalculator.calculate_tax(rounded_taxable_income)
        print("Advance tax 18% = ",TaxCalculator.tax_rate)
        
        if TaxCalculator.contract_type==ContractType.EMPLOYMENT.value:
            print("Tax free income =",TaxCalculator.tax_free_income)
            taxPaid = TaxCalculator.tax_rate - TaxCalculator.tax_free_income
            print("Reduced tax = "+"{0:.2f}".format(taxPaid))
        else: 
            taxPaid = TaxCalculator.tax_rate
            print("Already paid tax = "+"{0:.2f}".format(taxPaid))
            
        TaxCalculator.calculate_advance_tax()
        TaxCalculator.base_advance_tax = float("{0:.0f}".format(TaxCalculator.advance_tax))
        print("Advance paid tax = "+"{0:.2f}".format(TaxCalculator.advance_tax)+\
              " rounded "+"{0:.0f}".format(TaxCalculator.base_advance_tax))
        
        net_income = TaxCalculator.base_income - ((TaxCalculator.retirement_tax + TaxCalculator.pension_tax \
                        + TaxCalculator.sickness_tax) + TaxCalculator.health_insurance_tax + TaxCalculator.base_advance_tax)
        print()
        print("Net income = "+"{0:.2f}".format(net_income))
            
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