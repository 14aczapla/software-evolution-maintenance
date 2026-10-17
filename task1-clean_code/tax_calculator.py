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


class TaxCalculator(object):
    base_income = 0
    contractType = ""

    retirement_tax = 0
    pension_tax = 0
    sickness_tax = 0
 
    deductible_expenses = 111.25
    health_insurancet_tax = 0
    dedactable_health_tax = 0
    tax_rate = 0
    tax_free_income = 46.33
    advance_tax = 0
    base_advance_tax = 0

    @staticmethod
    def main():
        try:
            TaxCalculator.base_income=float(input("Enter income: "))
            TaxCalculator.contractType=input("Contract Type: (E)mployment, (C)ivil")[0]
        except ValueError:
            print("Incorrect")
            return
        
        if TaxCalculator.contractType=="E":
            print("EMPLOYMENT")
            print("Income ", TaxCalculator.base_income)
            social_security_base = TaxCalculator.calculateIncome(TaxCalculator.base_income)
            print("Social security tax: "+"{0:.2f}".format(TaxCalculator.retirement_tax))
            print("Health social security tax: "+"{0:.2f}".format(TaxCalculator.pension_tax))
            print("Sickness social security tax: "+"{0:.2f}".format(TaxCalculator.sickness_tax))
            print("Income basis for healt social security: ",social_security_base)
            TaxCalculator.calculateOtherTaxes(social_security_base)
            print("Healt social security tax: 9% = " \
                  +"{0:.2f}".format(TaxCalculator.health_insurancet_tax)+" 7,75% = "+"{0:.2f}".format(TaxCalculator.dedactable_health_tax))
            print("Tax deductible expenses: ",TaxCalculator.deductible_expenses)

            taxable_Income = social_security_base - TaxCalculator.deductible_expenses
            taxable_Income = float(round(taxable_Income))


            print("Income: ",taxable_Income," rounded: "+"{0:.0f}".format(taxedIncome0))
            TaxCalculator.calculateTax(taxedIncome0)
            print("Advance tax 18% = ",TaxCalculator.tax_rate)
            print("Tax free income =",TaxCalculator.tax_free_income)
            taxPaid = TaxCalculator.tax_rate - TaxCalculator.tax_free_income
            print("Reduced tax = "+"{0:.2f}".format(taxPaid))
            TaxCalculator.calculateAdvanceTax()
            TaxCalculator.base_advance_tax = float("{0:.0f}".format(TaxCalculator.advance_tax))
            print("Advance paid tax = "+"{0:.2f}".format(TaxCalculator.advance_tax)+\
                  " rounded "+"{0:.0f}".format(TaxCalculator.base_advance_tax))
            netIncome = TaxCalculator.base_income - ((TaxCalculator.retirement_tax + TaxCalculator.pension_tax \
                            + TaxCalculator.sickness_tax) + TaxCalculator.health_insurancet_tax + TaxCalculator.base_advance_tax)
            print()
            print("Net income = "+"{0:.2f}".format(netIncome))
            

        elif TaxCalculator.contractType=="C":
            print("CIVIL")
            print("Income",TaxCalculator.base_income)
            social_security_base = TaxCalculator.calculateIncome(TaxCalculator.base_income)
            print("Social security tax: "+"{0:.2f}".format(TaxCalculator.retirement_tax))
            print("Health social security tax: "+"{0:.2f}".format(TaxCalculator.pension_tax))
            print("Sickness social security tax  "+"{0:.2f}".format(TaxCalculator.sickness_tax))
            print("Income for calculating health security tax: ",social_security_base)
            TaxCalculator.calculateOtherTaxes(social_security_base)
            print("Health security tax: 9% = " \
                  +"{0:.2f}".format(TaxCalculator.health_insurancet_tax)+" 7,75% = "+"{0:.2f}".format(TaxCalculator.dedactable_health_tax))
            TaxCalculator.tax_free_income = 0
            TaxCalculator.deductible_expenses = (social_security_base * 20) / 100
            print("Tax deductible expenses = ",TaxCalculator.deductible_expenses)
            taxable_Income = social_security_base - TaxCalculator.deductible_expenses
            taxedIncome0 = float("{0:.0f}".format(taxable_Income))
            print("income to be taxed: ",taxable_Income," rounded: "+"{0:.0f}".format(taxedIncome0))
            TaxCalculator.calculateTax(taxedIncome0)
            print("Advance tax 18% =",TaxCalculator.tax_rate)
            taxPaid = TaxCalculator.tax_rate            
            print("Already paid tax = "+"{0:.2f}".format(taxPaid))
            TaxCalculator.calculateAdvanceTax()
            TaxCalculator.base_advance_tax = float("{0:.0f}".format(TaxCalculator.advance_tax))
            print("Advance tax = "+"{0:.2f}".format(TaxCalculator.advance_tax)+\
                  " rounded "+"{0:.0f}".format(TaxCalculator.base_advance_tax))
            netIncome = TaxCalculator.base_income - ((TaxCalculator.retirement_tax + TaxCalculator.pension_tax \
                          + TaxCalculator.sickness_tax) + TaxCalculator.health_insurancet_tax + TaxCalculator.base_advance_tax)
            print()
            print("Net income = "+"{0:.2f}".format(netIncome))
             
        else:
            print("Unknowne type of contract!")
            
    @staticmethod
    def calculateAdvanceTax():
        TaxCalculator.advance_tax=TaxCalculator.tax_rate - TaxCalculator.dedactable_health_tax - TaxCalculator.tax_free_income

    @staticmethod
    def calculateTax(income):
        TaxCalculator.tax_rate = (income * TaxRates.PIT_RATE) / 100

    @staticmethod
    def calculateIncome(income):
        TaxCalculator.retirement_tax = (income * TaxRates.RETIREMENT_RATE) / 100        
        TaxCalculator.pension_tax = (income * TaxRates.PENSION_RATE) / 100
        TaxCalculator.sickness_tax = (income * TaxRates.SICKNESS_RATE) / 100
        return (income - TaxCalculator.retirement_tax- TaxCalculator.pension_tax - TaxCalculator.sickness_tax)

    @staticmethod
    def calculateOtherTaxes(income):
        TaxCalculator.health_insurancet_tax = (income * TaxRates.HEALTH_INSURANCE_RATE) / 100
        TaxCalculator.dedactable_health_tax = (income * TaxRates.DEDUCTIBLE_HEALTH_RATE) / 100

        
if __name__=='__main__':
    TaxCalculator.main()