# Clean code - summary

## The Hierarchy of Refactoring

1. **Clarity and cleanup**: Ensured variables and functions have clear, intent-revealing names, and removed redundant or meaningless comments before changing any logic.
2. **Domain snd precision:** Fix math accuracy first (replacing `float` with `Decimal`).
3. **Decoupling (Single Responsibility):** Separate I/O (inputs/prints) from pure logic.
4. **Data Flow:** Secure how data moves between functions to prevent runtime errors.
5. **Extensibility (Polymorphism):** Replace hardcoded conditions with dynamic patterns to allow easy future additions.

---

## Main Code Smells and Solutions

### 1. Switch Statements
* **The Problem:** The old `TaxReportPrinter` used a hardcoded if/else block based on the contract type (EMPLOYMENT vs CIVIL). This matches the definition where a method contains a complex multi-level if or switch statement.   
* **The Solution:** We extracted the branches of the conditional statement to polymorphic classes. We created `TaxReportPresenter` and its specific subclasses, resolving the condition dynamically via a Factory.   
* **Why:** Adding a new contract type (like B2B) no longer requires modifying existing print logic, adhering to the Open-Closed Principle.

### 2. Large Class (God Object)
* **The Problem:** The original system tried to handle data collection, mathematical logic, state holding, and printing all in a very tight scope. The class bears too much responsibility.   
* **The Solution:** We extracted new classes and delegated responsibilities. `InputHandler` now strictly manages inputs, `TaxCalculator` only handles pure math, and `TaxReportPresenter` only formats the output.   
* **Why:** This isolates changes. A change in console output formatting will never accidentally break the tax mathematics.

### 3. Data Clumps and Primitive Obsession
* **The Problem:** The old calculator generated a giant dictionary mapping strings to numbers and passed it around. A set of data is always passed together. Furthermore, magic numbers (tax rates) were scattered.   
* **The Solution:** We created a new class from the clump. We replaced dictionaries with strictly typed, immutable `@dataclass` structures (e.g., `SocialSecurityResult`). We also gathered all magic numbers into a single `TaxRates` class.   
* **Why:** Dictionaries lack type safety, meaning typos crash the program at runtime. Dataclasses ensure the IDE catches missing or misspelled fields immediately.

### 4. Mutable State (Hidden Side Effects)
* **The Problem:** The old `TaxCalculator` initialized attributes to zero and mutated them sequentially by calling its own internal methods.
* **The Solution:** The calculator was made stateless. Methods now take inputs, process them as local variables, and return a final object.
* **Why:** Stateful calculators bleed data if reused. Stateless design guarantees thread safety and allows the same instance to be used infinitely without data corruption.
