class TaxCalculator(object):
    income = 0
    contractType = ""
    # social security taxes
    t_socialSecurity = 0 # 9,76% of the income
    t_socialSecurityHealth = 0 # 1,5% of the income
    t_socialSecuritySickness = 0 # 2,45% of the income
 
    t_deductibleExpenses = 111.25
    t_health1 = 0 # 9% of the income
    t_health2 = 0 # 7,75% of the income
    t_advance = 0 # advance tax = 18%
    reducedTax = 46.33 # tax free income 46,33 PLN
    advanceTax = 0
    advanceTax0 = 0

    @staticmethod
    def main():
        try:
            TaxCalculator.income=float(input("Enter income: "))
            TaxCalculator.contractType=input("Contract Type: (E)mployment, (C)ivil")[0]
        except ValueError:
            print("Incorrect")
            return
        if TaxCalculator.contractType=="E":
            print("EMPLOYMENT")
            print("Income ", TaxCalculator.income)
            d_income = TaxCalculator.calculateIncome(TaxCalculator.income)
            print("Social security tax: "+"{0:.2f}".format(TaxCalculator.t_socialSecurity))
            print("Health social security tax: "+"{0:.2f}".format(TaxCalculator.t_socialSecurityHealth))
            print("Sickness social security tax: "+"{0:.2f}".format(TaxCalculator.t_socialSecuritySickness))
            print("Income basis for healt social security: ",d_income)
            TaxCalculator.calculateOtherTaxes(d_income)
            print("Healt social security tax: 9% = " \
                  +"{0:.2f}".format(TaxCalculator.t_health1)+" 7,75% = "+"{0:.2f}".format(TaxCalculator.t_health2))
            print("Tax deductible expenses: ",TaxCalculator.t_deductibleExpenses)
            taxedIncome = d_income - TaxCalculator.t_deductibleExpenses
            taxedIncome0 = float("{0:.0f}".format(taxedIncome))
            print("Income: ",taxedIncome," rounded: "+"{0:.0f}".format(taxedIncome0))
            TaxCalculator.calculateTax(taxedIncome0)
            print("Advance tax 18% = ",TaxCalculator.t_advance)
            print("Tax free income =",TaxCalculator.reducedTax)
            taxPaid = TaxCalculator.t_advance - TaxCalculator.reducedTax
            print("Reduced tax = "+"{0:.2f}".format(taxPaid))
            TaxCalculator.calculateAdvanceTax()
            TaxCalculator.advanceTax0 = float("{0:.0f}".format(TaxCalculator.advanceTax))
            print("Advance paid tax = "+"{0:.2f}".format(TaxCalculator.advanceTax)+\
                  " rounded "+"{0:.0f}".format(TaxCalculator.advanceTax0))
            netIncome = TaxCalculator.income - ((TaxCalculator.t_socialSecurity + TaxCalculator.t_socialSecurityHealth \
                            + TaxCalculator.t_socialSecuritySickness) + TaxCalculator.t_health1 + TaxCalculator.advanceTax0)
            print()
            print("Net income = "+"{0:.2f}".format(netIncome))
            

        elif TaxCalculator.contractType=="C":
            print("CIVIL")
            print("Income",TaxCalculator.income)
            d_income = TaxCalculator.calculateIncome(TaxCalculator.income)
            print("Social security tax: "+"{0:.2f}".format(TaxCalculator.t_socialSecurity))
            print("Health social security tax: "+"{0:.2f}".format(TaxCalculator.t_socialSecurityHealth))
            print("Sickness social security tax  "+"{0:.2f}".format(TaxCalculator.t_socialSecuritySickness))
            print("Income for calculating health security tax: ",d_income)
            TaxCalculator.calculateOtherTaxes(d_income)
            print("Health security tax: 9% = " \
                  +"{0:.2f}".format(TaxCalculator.t_health1)+" 7,75% = "+"{0:.2f}".format(TaxCalculator.t_health2))
            TaxCalculator.reducedTax = 0
            TaxCalculator.t_deductibleExpenses = (d_income * 20) / 100
            print("Tax deductible expenses = ",TaxCalculator.t_deductibleExpenses)
            taxedIncome = d_income - TaxCalculator.t_deductibleExpenses
            taxedIncome0 = float("{0:.0f}".format(taxedIncome))
            print("income to be taxed: ",taxedIncome," rounded: "+"{0:.0f}".format(taxedIncome0))
            TaxCalculator.calculateTax(taxedIncome0)
            print("Advance tax 18% =",TaxCalculator.t_advance)
            taxPaid = TaxCalculator.t_advance            
            print("Already paid tax = "+"{0:.2f}".format(taxPaid))
            TaxCalculator.calculateAdvanceTax()
            TaxCalculator.advanceTax0 = float("{0:.0f}".format(TaxCalculator.advanceTax))
            print("Advance tax = "+"{0:.2f}".format(TaxCalculator.advanceTax)+\
                  " rounded "+"{0:.0f}".format(TaxCalculator.advanceTax0))
            netIncome = TaxCalculator.income - ((TaxCalculator.t_socialSecurity + TaxCalculator.t_socialSecurityHealth \
                          + TaxCalculator.t_socialSecuritySickness) + TaxCalculator.t_health1 + TaxCalculator.advanceTax0)
            print()
            print("Net income = "+"{0:.2f}".format(netIncome))
             
        else:
            print("Unknowne type of contract!")
            
    @staticmethod
    def calculateAdvanceTax():
        TaxCalculator.advanceTax=TaxCalculator.t_advance - TaxCalculator.t_health2 - TaxCalculator.reducedTax

    @staticmethod
    def calculateTax(income):
        TaxCalculator.t_advance = (income * 18) / 100

    @staticmethod
    def calculateIncome(income):
        TaxCalculator.t_socialSecurity = (income * 9.76) / 100        
        TaxCalculator.t_socialSecurityHealth = (income * 1.5) / 100
        TaxCalculator.t_socialSecuritySickness = (income * 2.45) / 100
        return (income - TaxCalculator.t_socialSecurity- TaxCalculator.t_socialSecurityHealth - TaxCalculator.t_socialSecuritySickness)

    @staticmethod
    def calculateOtherTaxes(income):
        TaxCalculator.t_health1 = (income * 9) / 100
        TaxCalculator.t_health2 = (income * 7.75) / 100

        
if __name__=='__main__':
    TaxCalculator.main()