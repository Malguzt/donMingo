from pytestarch import Rule
from .base_arch_test import BaseArchTest
import pytest


class TestLayers(BaseArchTest):
    """Test high-level architectural layer constraints following Clean Architecture."""

    def test_domain_layer_has_no_outward_dependencies(self):
        """
        Test that domain layer does not import from outer layers.
        
        Domain is the innermost layer and should have no outward dependencies.
        """
        if self._is_empty_package(f"{self.ROOT}.domain"):
            pytest.skip("Domain package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.domain") \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.(application|adapters(\.inbound|\.outbound)?|infrastructure)(\..+)?"
                ) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 DOMAIN LAYER OUTWARD DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Domain layer is importing from outer layers\n"
                f"🏗️  Why this violates Clean Architecture:\n"
                f"   • Domain is the center of the architecture and should be pure\n"
                f"   • All dependencies should point inward toward the domain\n"
                f"   • Outward dependencies make domain logic coupled to external concerns\n"
                f"   • It breaks the fundamental rule of Clean Architecture\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove all imports of application, adapters, and infrastructure from domain\n"
                f"   2. Define what domain needs as interfaces in domain.ports\n"
                f"   3. Let outer layers implement and inject these interfaces\n"
                f"   4. Use dependency inversion to maintain proper direction\n\n"
                f"💡 Clean Architecture principles:\n"
                f"   • The Dependency Rule: dependencies can only point inward\n"
                f"   • Inner layers define interfaces, outer layers implement them\n"
                f"   • Domain should be framework and technology independent\n"
                f"   • Business logic should not depend on delivery mechanisms\n\n"
                f"🛠️  Concrete steps:\n"
                f"   • Move interfaces to domain.ports\n"
                f"   • Use abstract base classes or typing.Protocol\n"
                f"   • Implement dependency injection container\n"
                f"   • Consider using domain events for decoupling\n\n"
                f"Original error: {str(e)}"
            )

    def test_application_layer_only_depends_on_domain(self):
        """
        Test that application layer only imports from domain layer.
        
        Application orchestrates domain logic without depending on outer layers.
        """
        if self._is_empty_package(f"{self.ROOT}.application"):
            pytest.skip("Application package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.application") \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.(adapters(\.inbound|\.outbound)?|infrastructure)(\..+)?"
                ) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 APPLICATION LAYER OUTWARD DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Application layer is importing from outer layers\n"
                f"🏗️  Why this breaks Clean Architecture:\n"
                f"   • Application layer should only orchestrate domain logic\n"
                f"   • Dependencies on adapters/infrastructure make it hard to test\n"
                f"   • It couples business workflows to specific implementations\n"
                f"   • Changes in outer layers force changes in application logic\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove adapter and infrastructure imports from application services\n"
                f"   2. Depend only on domain entities, services, and ports\n"
                f"   3. Use dependency injection to provide implementations\n"
                f"   4. Define application-specific DTOs if needed\n\n"
                f"💡 Application layer responsibilities:\n"
                f"   • Coordinate domain objects to fulfill use cases\n"
                f"   • Implement transaction boundaries\n"
                f"   • Handle application-specific logic (not business logic)\n"
                f"   • Translate between external and domain representations\n\n"
                f"🛠️  Design patterns that help:\n"
                f"   • Application Service pattern\n"
                f"   • Unit of Work pattern for transactions\n"
                f"   • Command/Query Responsibility Segregation (CQRS)\n"
                f"   • Mediator pattern for complex workflows\n\n"
                f"Original error: {str(e)}"
            )

    def test_inbound_adapters_should_not_access_domain_directly(self):
        """
        Test that inbound adapters do not import domain layer directly.
        
        Inbound adapters should go through the application layer.
        """
        if self._is_empty_package(f"{self.ROOT}.adapters.inbound"):
            pytest.skip("Inbound adapters package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.adapters.inbound") \
                .should_not().import_modules_that().are_sub_modules_of(f"{self.ROOT}.domain") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 INBOUND ADAPTER → DOMAIN DIRECT ACCESS VIOLATION\n"
                f"❌ Why it failed: Inbound adapters are importing domain layer directly\n"
                f"🏗️  Why this violates layered architecture:\n"
                f"   • Inbound adapters should go through application layer\n"
                f"   • Direct domain access bypasses application orchestration\n"
                f"   • It creates tight coupling between presentation and business logic\n"
                f"   • It makes it harder to apply cross-cutting concerns\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove direct domain imports from inbound adapters\n"
                f"   2. Create application services for use cases\n"
                f"   3. Let inbound adapters call application services\n"
                f"   4. Use DTOs for data transfer between layers\n\n"
                f"💡 Proper request flow:\n"
                f"   • Inbound Adapter → Application Service → Domain\n"
                f"   • Each layer has specific responsibilities\n"
                f"   • Application layer coordinates and orchestrates\n"
                f"   • Domain layer contains pure business logic\n\n"
                f"🛠️  Implementation strategies:\n"
                f"   • Create use case classes in application layer\n"
                f"   • Use command objects for complex operations\n"
                f"   • Implement proper error handling at application level\n"
                f"   • Consider using API versioning for external interfaces\n\n"
                f"Original error: {str(e)}"
            )

    def test_outbound_adapters_should_not_access_application_layer(self):
        """
        Test that outbound adapters do not import application layer.
        
        Outbound adapters should implement domain interfaces without application dependencies.
        """
        if self._is_empty_package(f"{self.ROOT}.adapters.outbound"):
            pytest.skip("Outbound adapters package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.adapters.outbound") \
                .should_not().import_modules_that().are_sub_modules_of(f"{self.ROOT}.application") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 OUTBOUND ADAPTER → APPLICATION DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Outbound adapters are importing application layer\n"
                f"🏗️  Why this violates dependency direction:\n"
                f"   • Outbound adapters should implement domain contracts (ports)\n"
                f"   • Application layer should depend on domain ports, not adapters\n"
                f"   • This creates circular dependencies between layers\n"
                f"   • It couples infrastructure implementations to application logic\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove application layer imports from outbound adapters\n"
                f"   2. Implement domain port interfaces in outbound adapters\n"
                f"   3. Let application services depend on domain ports only\n"
                f"   4. Use dependency injection to wire adapters to ports\n\n"
                f"💡 Ports and Adapters pattern:\n"
                f"   • Ports define what domain needs (interfaces)\n"
                f"   • Adapters provide implementations of those interfaces\n"
                f"   • Application depends on ports, not adapters\n"
                f"   • Adapters depend on domain ports and external systems\n\n"
                f"🛠️  Correct implementation:\n"
                f"   • Define IRepository, IEmailService, etc. in domain.ports\n"
                f"   • Implement these interfaces in adapters.outbound\n"
                f"   • Use composition root for dependency wiring\n"
                f"   • Consider using factory patterns for complex setups\n\n"
                f"Original error: {str(e)}"
            )

    def test_infrastructure_layer_should_not_import_core_layers(self):
        """
        Test that infrastructure layer does not import domain or application layers.
        
        Infrastructure should be the outermost layer with minimal inward dependencies.
        """
        if self._is_empty_package(f"{self.ROOT}.infrastructure"):
            pytest.skip("Infrastructure package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.infrastructure") \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.(domain|application|adapters\.inbound)(\..+)?"
                ) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 INFRASTRUCTURE → CORE LAYERS DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Infrastructure is importing core layers inappropriately\n"
                f"🏗️  Why this violates architectural boundaries:\n"
                f"   • Infrastructure should be the outermost layer\n"
                f"   • It should primarily contain framework and technology concerns\n"
                f"   • Direct imports of core layers create tight coupling\n"
                f"   • It makes infrastructure dependent on business logic\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove core layer imports from infrastructure modules\n"
                f"   2. Let infrastructure implement interfaces defined in domain.ports\n"
                f"   3. Use configuration and dependency injection for wiring\n"
                f"   4. Keep infrastructure focused on technical concerns\n\n"
                f"💡 Infrastructure layer responsibilities:\n"
                f"   • Database connections and ORM configuration\n"
                f"   • Web framework setup and routing\n"
                f"   • External service integrations\n"
                f"   • Cross-cutting concerns (logging, monitoring)\n\n"
                f"🛠️  Proper infrastructure design:\n"
                f"   • Use composition root pattern for dependency wiring\n"
                f"   • Implement adapter interfaces in infrastructure\n"
                f"   • Use factory patterns for complex object creation\n"
                f"   • Consider using configuration files for settings\n\n"
                f"Original error: {str(e)}"
            )
