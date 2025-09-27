from pytestarch import Rule
from .base_arch_test import BaseArchTest
import pytest


class TestDomain(BaseArchTest):
    """Test domain layer architecture constraints following DDD principles."""

    def test_entities_should_not_import_domain_services(self):
        """
        Test that entities do not import domain services.

        Entities should be pure business objects without service dependencies.
        """
        if self._is_empty_package(f"{self.ROOT}.domain.entities"):
            pytest.skip("Domain entities package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.domain.entities") \
                .should_not().import_modules_that().are_sub_modules_of(f"{self.ROOT}.domain.services") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 ENTITY → DOMAIN SERVICE DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Domain entities are importing domain services\n"
                f"🏗️  Why this violates DDD principles:\n"
                f"   • Entities should contain business data and behavior, not orchestration\n"
                f"   • Services handle complex business logic that doesn't belong in entities\n"
                f"   • This creates circular dependencies between core domain concepts\n"
                f"   • It makes entities heavy and difficult to test and understand\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove domain service imports from entity classes\n"
                f"   2. Move complex business logic from entities to domain services\n"
                f"   3. Keep entities focused on their intrinsic properties and behavior\n"
                f"   4. Use domain services to coordinate between multiple entities\n\n"
                f"💡 DDD concepts to understand:\n"
                f"   • Entity identity and lifecycle\n"
                f"   • Domain Services for business operations\n"
                f"   • Aggregate patterns and boundaries\n"
                f"   • Rich domain model vs anemic domain model\n\n"
                f"🛠️  Design guidelines:\n"
                f"   • Entities should have rich behavior related to their data\n"
                f"   • Use domain services for operations involving multiple entities\n"
                f"   • Consider using domain events for loose coupling\n"
                f"   • Apply Tell Don't Ask principle\n\n"
                f"Original error: {str(e)}"
            )

    def test_value_objects_should_not_import_domain_services(self):
        """
        Test that value objects do not import domain services.

        Value objects should be immutable and self-contained.
        """
        if self._is_empty_package(f"{self.ROOT}.domain.value_objects"):
            pytest.skip("Domain value objects package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.domain.value_objects") \
                .should_not().import_modules_that().are_sub_modules_of(f"{self.ROOT}.domain.services") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 VALUE OBJECT → DOMAIN SERVICE DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Value objects are importing domain services\n"
                f"🏗️  Why this violates DDD principles:\n"
                f"   • Value objects should be immutable and side-effect free\n"
                f"   • They represent descriptive concepts without identity\n"
                f"   • Dependencies on services break their self-contained nature\n"
                f"   • It makes value objects context-dependent and harder to reuse\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove all domain service imports from value objects\n"
                f"   2. Make value objects purely functional and immutable\n"
                f"   3. Move any business logic to entities or domain services\n"
                f"   4. Use value objects for validation and computation only\n\n"
                f"💡 Value Object design principles:\n"
                f"   • Immutability (no setters, return new instances)\n"
                f"   • Equality based on values, not identity\n"
                f"   • Self-validation in constructor\n"
                f"   • No side effects or external dependencies\n\n"
                f"🛠️  Implementation patterns:\n"
                f"   • Use @dataclass(frozen=True) in Python\n"
                f"   • Implement __eq__ and __hash__ methods\n"
                f"   • Use factory methods for complex creation\n"
                f"   • Consider using typing for better validation\n\n"
                f"Original error: {str(e)}"
            )

    def test_domain_services_should_not_import_application_layer(self):
        """
        Test that domain services do not import application layer modules.

        Domain services should be pure business logic without application concerns.
        """
        if self._is_empty_package(f"{self.ROOT}.domain.services"):
            pytest.skip("Domain services package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.domain.services") \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.application(\. D+)?") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 DOMAIN SERVICE → APPLICATION DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Domain services are importing application layer modules\n"
                f"🏗️  Why this violates Clean Architecture:\n"
                f"   • Domain is the innermost layer and should have no outward dependencies\n"
                f"   • Application layer orchestrates domain services, not vice versa\n"
                f"   • This creates circular dependencies between core layers\n"
                f"   • It makes domain logic dependent on application concerns\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove application layer imports from domain services\n"
                f"   2. Keep domain services focused on pure business logic\n"
                f"   3. Let application services orchestrate domain services\n"
                f"   4. Use domain events for loose coupling between domains\n\n"
                f"💡 Domain Service design principles:\n"
                f"   • Stateless operations on domain objects\n"
                f"   • Business logic that doesn't belong to specific entities\n"
                f"   • Coordination between multiple aggregates\n"
                f"   • Pure functions without side effects\n\n"
                f"🛠️  Better alternatives:\n"
                f"   • Use domain events for cross-boundary communication\n"
                f"   • Implement domain service interfaces in domain.ports\n"
                f"   • Apply Command pattern for complex operations\n"
                f"   • Consider using specification pattern for business rules\n\n"
                f"Original error: {str(e)}"
            )

    def test_domain_services_should_not_import_adapters(self):
        """
        Test that domain services do not import adapter modules.

        Domain should be independent of all infrastructure and adapter concerns.
        """
        if self._is_empty_package(f"{self.ROOT}.domain.services"):
            pytest.skip("Domain services package is empty - skipping test")

        ev = self._evaluable()

        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.domain.services") \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.adapters(\.inbound|\.outbound)?(\. D+)?") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 DOMAIN SERVICE → ADAPTER DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Domain services are importing adapter modules\n"
                f"🏗️  Why this breaks architecture boundaries:\n"
                f"   • Domain should be technology-agnostic and pure business logic\n"
                f"   • Adapters are implementation details that change frequently\n"
                f"   • This makes domain logic dependent on external concerns\n"
                f"   • It violates the dependency inversion principle\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove all adapter imports from domain services\n"
                f"   2. Define abstract interfaces in domain.ports\n"
                f"   3. Let adapters implement domain interfaces\n"
                f"   4. Use dependency injection for providing implementations\n\n"
                f"💡 Architectural patterns to implement:\n"
                f"   • Repository pattern for data access\n"
                f"   • Gateway pattern for external services\n"
                f"   • Port and Adapter pattern\n"
                f"   • Domain events for decoupling\n\n"
                f"🛠️  Implementation strategies:\n"
                f"   • Create abstract base classes in domain.ports\n"
                f"   • Use typing.Protocol for interface definitions\n"
                f"   • Implement dependency injection container\n"
                f"   • Consider using factory pattern for complex creation\n\n"
                f"Original error: {str(e)}"
            )

    def test_domain_services_should_not_import_infrastructure(self):
        """
        Test that domain services do not import infrastructure modules.

        Domain must remain independent of all infrastructure concerns.
        """
        if self._is_empty_package(f"{self.ROOT}.domain.services"):
            pytest.skip("Domain services package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.domain.services") \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.infrastructure(\. D+)?") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 DOMAIN SERVICE → INFRASTRUCTURE DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Domain services are importing infrastructure modules\n"
                f"🏗️  Why this is critical in Clean Architecture:\n"
                f"   • Infrastructure is the outermost layer (databases, web, frameworks)\n"
                f"   • Domain is the innermost layer and must be pure business logic\n"
                f"   • This dependency goes in the wrong direction\n"
                f"   • It makes domain logic dependent on specific technologies\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove all infrastructure imports from domain services\n"
                f"   2. Define what you need as interfaces in domain.ports\n"
                f"   3. Let infrastructure implement these domain interfaces\n"
                f"   4. Use composition root for wiring dependencies\n\n"
                f"💡 Core principles being violated:\n"
                f"   • Dependency Inversion Principle (depend on abstractions)\n"
                f"   • Clean Architecture dependency rule (inward only)\n"
                f"   • Separation of Concerns\n"
                f"   • Technology independence\n\n"
                f"🛠️  Concrete steps to take:\n"
                f"   • Create IRepository, IEventBus, ILogger interfaces\n"
                f"   • Move infrastructure-specific code to infrastructure layer\n"
                f"   • Use composition root pattern for dependency wiring\n"
                f"   • Apply interface segregation principle\n\n"
                f"Original error: {str(e)}"
            )

    def test_domain_ports_should_not_import_application_layer(self):
        """
        Test that domain ports do not import application layer modules.

        Ports define domain contracts and should be independent of application logic.
        """
        if self._is_empty_package(f"{self.ROOT}.domain.ports"):
            pytest.skip("Domain ports package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.domain.ports") \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.application(\. D+)?") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 DOMAIN PORTS → APPLICATION DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Domain ports are importing application layer modules\n"
                f"🏗️  Why this violates Ports and Adapters:\n"
                f"   • Ports define domain contracts and should be stable\n"
                f"   • Application layer should depend on ports, not vice versa\n"
                f"   • This creates circular dependencies between layers\n"
                f"   • It couples domain contracts to application-specific concerns\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove application layer imports from domain ports\n"
                f"   2. Keep ports as pure interface definitions\n"
                f"   3. Let application services depend on domain ports\n"
                f"   4. Use domain events for cross-layer communication\n\n"
                f"💡 Port design principles:\n"
                f"   • Ports are contracts, not implementations\n"
                f"   • They express domain needs without implementation details\n"
                f"   • Should be stable and change infrequently\n"
                f"   • Use domain language, not technical language\n\n"
                f"🛠️  Best practices for ports:\n"
                f"   • Use abstract base classes or typing.Protocol\n"
                f"   • Focus on business operations, not technical details\n"
                f"   • Apply interface segregation principle\n"
                f"   • Consider using domain-specific return types\n\n"
                f"Original error: {str(e)}"
            )

    def test_domain_ports_should_not_import_adapters_or_infrastructure(self):
        """
        Test that domain ports do not import adapters or infrastructure.

        Ports should be pure abstractions without implementation dependencies.
        """
        if self._is_empty_package(f"{self.ROOT}.domain.ports"):
            pytest.skip("Domain ports package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.domain.ports") \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.(adapters(\.inbound|\.outbound)?|infrastructure)(\. D+)?") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 DOMAIN PORTS → ADAPTERS/INFRASTRUCTURE DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Domain ports are importing adapters or infrastructure\n"
                f"🏗️  Why this defeats the purpose of ports:\n"
                f"   • Ports are abstractions that hide implementation details\n"
                f"   • Importing adapters/infrastructure ties ports to specific implementations\n"
                f"   • This breaks the inversion of control that ports provide\n"
                f"   • It makes domain dependent on external concerns\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove all adapter/infrastructure imports from ports\n"
                f"   2. Keep ports as pure abstract interfaces\n"
                f"   3. Let adapters implement port interfaces\n"
                f"   4. Use dependency injection to provide implementations\n\n"
                f"💡 Ports and Adapters pattern principles:\n"
                f"   • Ports are about WHAT the domain needs\n"
                f"   • Adapters are about HOW to provide it\n"
                f"   • Ports should be technology-agnostic\n"
                f"   • Adapters handle technology-specific details\n\n"
                f"🛠️  Implementation guidelines:\n"
                f"   • Use abc.ABC for abstract base classes\n"
                f"   • Define methods using domain language\n"
                f"   • Return domain objects, not infrastructure objects\n"
                f"   • Consider using typing.Protocol for structural subtyping\n\n"
                f"Original error: {str(e)}"
            )