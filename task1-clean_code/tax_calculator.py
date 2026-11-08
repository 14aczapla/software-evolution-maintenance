from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from typing import TextIO
import sys


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

    WHOLE_ZLOTY = Decimal("1")
    TWO_DECIMAL_PLACES = Decimal("0.01")


class ContractType(Enum):
    EMPLOYMENT = "E"
    CIVIL = "C"



@dataclass(frozen=True)
class InputData:
    base_income: Decimal
    contract_type: ContractType


class InputHandler:

    @staticmethod
    def collect_input() -> InputData:
        raw_income = input("Enter income: ").strip()
        raw_contract = input(
            "Contract type: (E)mployment, (C)ivil: "
        ).strip().upper()

        try:
            income = Decimal(raw_income)
        except InvalidOperation as error:
            raise ValueError("Income must be a valid decimal number.") from error

        if not income.is_finite():
            raise ValueError("Income must be a finite number.")

        if income < 0:
            raise ValueError("Income cannot be negative.")

        try:
            contract_type = ContractType(raw_contract)
        except ValueError as error:
            raise ValueError(
                "Unknown contract type. Enter E for employment or C for civil."
            ) from error

        return InputData(
            base_income=income,
            contract_type=contract_type,
        )



@dataclass(frozen=True)
class SocialSecurityResult:
    retirement_contribution: Decimal
    pension_contribution: Decimal
    sickness_contribution: Decimal
    contribution_base: Decimal


@dataclass(frozen=True)
class HealthInsuranceResult:
    contribution: Decimal
    deductible_contribution: Decimal


@dataclass(frozen=True)
class TaxableIncomeResult:
    deductible_expenses: Decimal
    amount: Decimal
    rounded_amount: Decimal


@dataclass(frozen=True)
class TaxCalculation:

    base_income: Decimal
    social_security: SocialSecurityResult
    health_insurance: HealthInsuranceResult
    taxable_income: TaxableIncomeResult
    tax_before_deductions: Decimal
    tax_after_tax_free_amount: Decimal
    tax_advance: Decimal
    rounded_tax_advance: Decimal
    net_income: Decimal



@dataclass(frozen=True)
class TaxReport(ABC):
    calculation: TaxCalculation


@dataclass(frozen=True)
class EmploymentTaxReport(TaxReport):
    tax_free_income: Decimal


@dataclass(frozen=True)
class CivilTaxReport(TaxReport):
    calculated_tax: Decimal


class ContractRules(ABC):

    @abstractmethod
    def calculate_deductible_expenses(
        self,
        social_security_base: Decimal,
    ) -> Decimal:
        raise NotImplementedError

    @property
    @abstractmethod
    def tax_free_income(self) -> Decimal:
        raise NotImplementedError

    def calculate_tax_after_tax_free_amount(
        self,
        tax_before_deductions: Decimal,
    ) -> Decimal:
        return tax_before_deductions - self.tax_free_income

    @abstractmethod
    def create_report(
        self,
        calculation: TaxCalculation,
    ) -> TaxReport:
        raise NotImplementedError


class EmploymentContractRules(ContractRules):
    def calculate_deductible_expenses(
        self,
        social_security_base: Decimal,
    ) -> Decimal:
        return TaxRates.DEFAULT_EMPLOYMENT_EXPENSES

    @property
    def tax_free_income(self) -> Decimal:
        return TaxRates.DEFAULT_TAX_FREE_INCOME

    def create_report(
        self,
        calculation: TaxCalculation,
    ) -> EmploymentTaxReport:
        return EmploymentTaxReport(
            calculation=calculation,
            tax_free_income=self.tax_free_income,
        )


class CivilContractRules(ContractRules):
    def calculate_deductible_expenses(
        self,
        social_security_base: Decimal,
    ) -> Decimal:
        return social_security_base * TaxRates.CIVIL_EXPENSE_RATE

    @property
    def tax_free_income(self) -> Decimal:
        return Decimal("0.00")

    def create_report(
        self,
        calculation: TaxCalculation,
    ) -> CivilTaxReport:
        return CivilTaxReport(
            calculation=calculation,
            calculated_tax=calculation.tax_after_tax_free_amount,
        )


class TaxCalculator:

    def __init__(self, rules: ContractRules):
        self._rules = rules

    def calculate(self, income: Decimal) -> TaxReport:
        social_security = self._calculate_social_security(income)
        health_insurance = self._calculate_health_insurance(
            social_security.contribution_base
        )
        taxable_income = self._calculate_taxable_income(
            social_security.contribution_base
        )

        tax_before_deductions = (
            taxable_income.rounded_amount * TaxRates.PIT_RATE
        )
        tax_after_tax_free_amount = (
            self._rules.calculate_tax_after_tax_free_amount(
                tax_before_deductions
            )
        )

        tax_advance = (
            tax_after_tax_free_amount
            - health_insurance.deductible_contribution
        )
        rounded_tax_advance = self._round_to_whole_zloty(tax_advance)

        total_deductions = (
            social_security.retirement_contribution
            + social_security.pension_contribution
            + social_security.sickness_contribution
            + health_insurance.contribution
            + rounded_tax_advance
        )
        net_income = income - total_deductions

        calculation = TaxCalculation(
            base_income=income,
            social_security=social_security,
            health_insurance=health_insurance,
            taxable_income=taxable_income,
            tax_before_deductions=tax_before_deductions,
            tax_after_tax_free_amount=tax_after_tax_free_amount,
            tax_advance=tax_advance,
            rounded_tax_advance=rounded_tax_advance,
            net_income=net_income,
        )

        return self._rules.create_report(calculation)

    @staticmethod
    def _calculate_social_security(
        income: Decimal,
    ) -> SocialSecurityResult:
        retirement = income * TaxRates.RETIREMENT_RATE
        pension = income * TaxRates.PENSION_RATE
        sickness = income * TaxRates.SICKNESS_RATE

        contribution_base = income - retirement - pension - sickness

        return SocialSecurityResult(
            retirement_contribution=retirement,
            pension_contribution=pension,
            sickness_contribution=sickness,
            contribution_base=contribution_base,
        )

    @staticmethod
    def _calculate_health_insurance(
        social_security_base: Decimal,
    ) -> HealthInsuranceResult:
        return HealthInsuranceResult(
            contribution=(
                social_security_base * TaxRates.HEALTH_INSURANCE_RATE
            ),
            deductible_contribution=(
                social_security_base * TaxRates.DEDUCTIBLE_HEALTH_RATE
            ),
        )

    def _calculate_taxable_income(
        self,
        social_security_base: Decimal,
    ) -> TaxableIncomeResult:
        deductible_expenses = self._rules.calculate_deductible_expenses(
            social_security_base
        )
        amount = social_security_base - deductible_expenses

        return TaxableIncomeResult(
            deductible_expenses=deductible_expenses,
            amount=amount,
            rounded_amount=self._round_to_whole_zloty(amount),
        )

    @staticmethod
    def _round_to_whole_zloty(amount: Decimal) -> Decimal:
        return amount.quantize(
            TaxRates.WHOLE_ZLOTY,
            rounding=ROUND_HALF_UP,
        )
    

class TaxCalculatorFactory:

    _RULES_BY_CONTRACT = {
        ContractType.EMPLOYMENT: EmploymentContractRules,
        ContractType.CIVIL: CivilContractRules,
    }

    @classmethod
    def create(cls, contract_type: ContractType) -> TaxCalculator:
        try:
            rules_class = cls._RULES_BY_CONTRACT[contract_type]
        except KeyError as error:
            raise ValueError(
                f"Unsupported contract type: {contract_type}"
            ) from error

        return TaxCalculator(rules_class())


class TaxReportPresenter(ABC):

    def __init__(self, output_stream: TextIO | None = None):
        self._output = output_stream if output_stream is not None else sys.stdout

    def print_report(self, report: TaxReport) -> None:
        self._print_header()
        self._print_common_body(report)
        self._print_contract_specifics(report)
        self._print_footer(report)

    @abstractmethod
    def _print_header(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def _print_contract_specifics(self, report: TaxReport) -> None:
        raise NotImplementedError

    def _print_common_body(self, report: TaxReport) -> None:
        calc = report.calculation
        social = calc.social_security
        health = calc.health_insurance
        taxable = calc.taxable_income

        print(f"Income: {self._money(calc.base_income)}", file=self._output)
        print(
            f"Retirement contribution: "
            f"{self._money(social.retirement_contribution)}",
            file=self._output,
        )
        print(
            f"Pension contribution: "
            f"{self._money(social.pension_contribution)}",
            file=self._output,
        )
        print(
            f"Sickness contribution: "
            f"{self._money(social.sickness_contribution)}",
            file=self._output,
        )
        print(
            f"Social security contribution base: "
            f"{self._money(social.contribution_base)}",
            file=self._output,
        )
        print(
            f"Health insurance contribution (9%): "
            f"{self._money(health.contribution)}",
            file=self._output,
        )
        print(
            f"Deductible health contribution (7.75%): "
            f"{self._money(health.deductible_contribution)}",
            file=self._output,
        )
        print(
            f"Deductible expenses: "
            f"{self._money(taxable.deductible_expenses)}",
            file=self._output,
        )
        print(
            f"Taxable income: {self._money(taxable.amount)} "
            f"(rounded: {taxable.rounded_amount:.0f})",
            file=self._output,
        )
        print(
            f"Tax before deductions (18%): "
            f"{self._money(calc.tax_before_deductions)}",
            file=self._output,
        )

    def _print_footer(self, report: TaxReport) -> None:
        calc = report.calculation
        print(
            f"Tax advance before rounding: {self._money(calc.tax_advance)}",
            file=self._output,
        )
        print(
            f"Tax advance rounded: {calc.rounded_tax_advance:.0f}",
            file=self._output,
        )
        print(
            f"\nNet income: {self._money(calc.net_income)}",
            file=self._output,
        )

    @staticmethod
    def _money(amount: Decimal) -> str:
        return f"{amount.quantize(TaxRates.TWO_DECIMAL_PLACES):.2f}"


class EmploymentTaxReportPresenter(TaxReportPresenter):
    def _print_header(self) -> None:
        print("EMPLOYMENT CONTRACT", file=self._output)

    def _print_contract_specifics(self, report: TaxReport) -> None:
        if not isinstance(report, EmploymentTaxReport):
            raise TypeError("Employment presenter requires an employment report.")

        print(
            f"Tax-free amount: {self._money(report.tax_free_income)}",
            file=self._output,
        )
        print(
            f"Tax after tax-free amount: "
            f"{self._money(report.calculation.tax_after_tax_free_amount)}",
            file=self._output,
        )


class CivilTaxReportPresenter(TaxReportPresenter):
    def _print_header(self) -> None:
        print("CIVIL CONTRACT", file=self._output)

    def _print_contract_specifics(self, report: TaxReport) -> None:
        if not isinstance(report, CivilTaxReport):
            raise TypeError("Civil presenter requires a civil report.")

        print(
            f"Calculated tax: {self._money(report.calculated_tax)}",
            file=self._output,
        )


class TaxReportPresenterFactory:

    @staticmethod
    def create(report: TaxReport) -> TaxReportPresenter:
        if isinstance(report, EmploymentTaxReport):
            return EmploymentTaxReportPresenter()

        if isinstance(report, CivilTaxReport):
            return CivilTaxReportPresenter()

        raise ValueError(
            f"Unsupported report type: {type(report).__name__}"
        )


def main() -> None:
    try:
        input_data = InputHandler.collect_input()
        calculator = TaxCalculatorFactory.create(input_data.contract_type)

        report = calculator.calculate(input_data.base_income)

        presenter = TaxReportPresenterFactory.create(report)
        presenter.print_report(report)

    except ValueError as error:
        print(f"Input error: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
