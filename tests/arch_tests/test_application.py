from .base_arch_test import BaseArchTest
from pytestarch import Rule
import pytest


class TestApplication(BaseArchTest):
    """Test application layer architecture constraints following Clean Architecture principles."""

    def test_application_should_not_import_inbound_adapters(self):
        """
        Test that application services do not import inbound adapters.
        
        This enforces proper dependency direction in Clean Architecture.
        """
        if self._is_empty_package(f"{self.ROOT}.application"):
            pytest.skip("Application package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.application") \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.adapters\.inbound(\..+)?"
                )\
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 APPLICATION → INBOUND ADAPTER DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Application services are importing inbound adapters\n"
                f"🏗️  Why this violates Clean Architecture:\n"
                f"   • Application layer should be independent of how requests arrive\n"
                f"   • Inbound adapters should depend on application, not vice versa\n"
                f"   • This creates circular dependencies and tight coupling\n"
                f"   • It makes application services dependent on delivery mechanisms\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove inbound adapter imports from application services\n"
                f"   2. Let inbound adapters call application services directly\n"
                f"   3. Use dependency injection to provide application services to adapters\n"
                f"   4. Define clear interfaces between layers\n\n"
                f"💡 Architectural principles to understand:\n"
                f"   • Dependency Inversion Principle (DIP)\n"
                f"   • Clean Architecture dependency rule (dependencies point inward)\n"
                f"   • Separation of Concerns\n"
                f"   • Single Responsibility Principle (SRP)\n\n"
                f"🛠️  Implementation strategies:\n"
                f"   • Create application service interfaces\n"
                f"   • Use constructor injection in inbound adapters\n"
                f"   • Consider using command/query objects for communication\n"
                f"   • Apply the Mediator pattern for complex interactions\n\n"
                f"Original error: {str(e)}"
            )

    def test_application_should_not_import_outbound_adapters(self):
        """
        Test that application services do not import outbound adapters directly.
        
        Application should depend on abstractions, not concrete adapters.
        """
        if self._is_empty_package(f"{self.ROOT}.application"):
            pytest.skip("Application package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.application") \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.adapters\.outbound(\..+)?"
                )\
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 APPLICATION → OUTBOUND ADAPTER DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Application services are importing outbound adapters\n"
                f"🏗️  Why this breaks Clean Architecture:\n"
                f"   • Application should depend on domain abstractions (ports)\n"
                f"   • Outbound adapters are implementation details\n"
                f"   • Direct dependencies make testing and maintenance difficult\n"
                f"   • It violates the Dependency Inversion Principle\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove outbound adapter imports from application services\n"
                f"   2. Define repository/gateway interfaces in domain.ports\n"
                f"   3. Let outbound adapters implement these interfaces\n"
                f"   4. Inject implementations through dependency injection\n\n"
                f"💡 Design patterns that help:\n"
                f"   • Repository Pattern for data access\n"
                f"   • Gateway Pattern for external service calls\n"
                f"   • Port and Adapter Pattern\n"
                f"   • Strategy Pattern for different implementations\n\n"
                f"🛠️  Concrete steps:\n"
                f"   • Create abstract base classes in domain.ports\n"
                f"   • Use typing.Protocol for duck typing\n"
                f"   • Implement dependency injection container\n"
                f"   • Mock interfaces for unit testing\n\n"
                f"Original error: {str(e)}"
            )

    def test_application_should_not_import_infrastructure(self):
        """
        Test that application services do not import infrastructure modules.
        
        Infrastructure is the outermost layer and should not be imported by application.
        """
        if self._is_empty_package(f"{self.ROOT}.application"):
            pytest.skip("Application package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.application") \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.infrastructure(\..+)?"
                )\
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 APPLICATION → INFRASTRUCTURE DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Application services are importing infrastructure modules\n"
                f"🏗️  Why this violates Clean Architecture:\n"
                f"   • Infrastructure is the outermost layer (frameworks, databases, web)\n"
                f"   • Application layer should only depend on domain layer\n"
                f"   • Infrastructure dependencies make application hard to test\n"
                f"   • It couples business logic to specific technologies\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove all infrastructure imports from application services\n"
                f"   2. Define abstractions in domain.ports for infrastructure needs\n"
                f"   3. Let infrastructure implement domain interfaces\n"
                f"   4. Use composition root for wiring dependencies\n\n"
                f"💡 Key concepts to master:\n"
                f"   • Clean Architecture's concentric circles\n"
                f"   • Dependency Inversion Principle\n"
                f"   • Infrastructure as implementation detail\n"
                f"   • Testable architecture patterns\n\n"
                f"🛠️  Recommended approach:\n"
                f"   • Create IRepository, IEmailService, ILogger interfaces\n"
                f"   • Implement these in infrastructure layer\n"
                f"   • Use dependency injection frameworks\n"
                f"   • Consider using factory patterns for complex setups\n\n"
                f"Original error: {str(e)}"
            )
