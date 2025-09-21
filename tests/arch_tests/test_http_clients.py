from .base_arch_test import BaseArchTest
from pytestarch import Rule
import pytest


class TestHttpClients(BaseArchTest):
    """Test HTTP client usage restrictions following Clean Architecture principles."""

    def test_domain_layer_should_not_import_http_clients(self):
        """
        Test that domain layer modules do not import HTTP client libraries directly.
        
        This enforces the Clean Architecture principle that the domain layer should be
        independent of external concerns like HTTP communication.
        """
        if self._is_empty_package(f"{self.ROOT}.domain"):
            pytest.skip("Domain package is empty - skipping test")
            
        ev = self._evaluable()
        http_libs_pattern = r"(requests|httpx|urllib3|aiohttp|http\.client|http\.server)"
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.domain") \
                .should_not().import_modules_that().have_name_matching(http_libs_pattern) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 DOMAIN LAYER HTTP CLIENT VIOLATION\n"
                f"❌ Why it failed: Domain modules are importing HTTP client libraries directly\n"
                f"🏗️  Why this matters in Clean Architecture:\n"
                f"   • The Domain layer represents your business logic and should be pure\n"
                f"   • HTTP clients are infrastructure concerns, not business concerns\n"
                f"   • Direct HTTP dependencies make your domain hard to test and maintain\n"
                f"   • It violates the Dependency Inversion Principle\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove HTTP client imports from domain modules\n"
                f"   2. Define domain ports (interfaces) for external communication\n"
                f"   3. Implement HTTP clients in infrastructure.clients\n"
                f"   4. Use dependency injection to provide implementations\n\n"
                f"💡 Recommended concepts to study:\n"
                f"   • Ports and Adapters (Hexagonal Architecture)\n"
                f"   • Dependency Inversion Principle (DIP)\n"
                f"   • Interface Segregation Principle (ISP)\n"
                f"   • Domain-Driven Design boundaries\n\n"
                f"🛠️  Tools that can help:\n"
                f"   • dependency-injector library\n"
                f"   • abc module for abstract base classes\n"
                f"   • typing.Protocol for structural subtyping\n\n"
                f"Original error: {str(e)}"
            )

    def test_application_layer_should_not_import_http_clients(self):
        """
        Test that application layer modules do not import HTTP client libraries directly.
        
        Application services should orchestrate domain logic, not handle HTTP communication.
        """
        if self._is_empty_package(f"{self.ROOT}.application"):
            pytest.skip("Application package is empty - skipping test")
            
        ev = self._evaluable()
        http_libs_pattern = r"(requests|httpx|urllib3|aiohttp|http\.client|http\.server)"
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.application") \
                .should_not().import_modules_that().have_name_matching(http_libs_pattern) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 APPLICATION LAYER HTTP CLIENT VIOLATION\n"
                f"❌ Why it failed: Application services are importing HTTP client libraries\n"
                f"🏗️  Why this matters in Clean Architecture:\n"
                f"   • Application layer should orchestrate domain logic, not handle I/O\n"
                f"   • HTTP clients are infrastructure concerns that change frequently\n"
                f"   • Direct HTTP dependencies make application services hard to unit test\n"
                f"   • It couples business logic to specific HTTP implementations\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove HTTP client imports from application services\n"
                f"   2. Define repository or gateway interfaces in domain.ports\n"
                f"   3. Inject HTTP-based implementations from infrastructure layer\n"
                f"   4. Use abstract base classes or protocols for contracts\n\n"
                f"💡 Recommended patterns to implement:\n"
                f"   • Repository Pattern for data access\n"
                f"   • Gateway Pattern for external service calls\n"
                f"   • Command/Query Responsibility Segregation (CQRS)\n"
                f"   • Application Service Pattern\n\n"
                f"🛠️  Tools that can help:\n"
                f"   • pytest with mocking for testing\n"
                f"   • Factory Pattern for creating implementations\n"
                f"   • Configuration-based dependency injection\n\n"
                f"Original error: {str(e)}"
            )

    def test_inbound_adapters_should_not_import_http_clients(self):
        """
        Test that inbound adapters do not import HTTP client libraries.
        
        Inbound adapters should receive requests, not make them.
        """
        if self._is_empty_package(f"{self.ROOT}.adapters.inbound"):
            pytest.skip("Inbound adapters package is empty - skipping test")
            
        ev = self._evaluable()
        http_libs_pattern = r"(requests|httpx|urllib3|aiohttp|http\.client|http\.server)"
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.adapters.inbound") \
                .should_not().import_modules_that().have_name_matching(http_libs_pattern) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 INBOUND ADAPTER HTTP CLIENT VIOLATION\n"
                f"❌ Why it failed: Inbound adapters are importing HTTP client libraries\n"
                f"🏗️  Why this matters in Ports and Adapters:\n"
                f"   • Inbound adapters receive requests from external actors\n"
                f"   • They should not make outbound HTTP calls themselves\n"
                f"   • This violates single responsibility principle\n"
                f"   • It creates confusion about data flow direction\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove HTTP client imports from inbound adapters\n"
                f"   2. Move HTTP client usage to outbound adapters\n"
                f"   3. Use application services to coordinate between adapters\n"
                f"   4. Keep inbound adapters focused on request/response translation\n\n"
                f"💡 Architectural concepts to understand:\n"
                f"   • Inbound vs Outbound adapter responsibilities\n"
                f"   • Single Responsibility Principle (SRP)\n"
                f"   • Separation of Concerns\n"
                f"   • Request/Response transformation patterns\n\n"
                f"🛠️  Better alternatives:\n"
                f"   • Use application services for orchestration\n"
                f"   • Implement outbound adapters for external calls\n"
                f"   • Consider event-driven architecture for async operations\n\n"
                f"Original error: {str(e)}"
            )

    def test_outbound_adapters_should_not_import_http_clients_directly(self):
        """
        Test that outbound adapters delegate HTTP client usage to infrastructure.clients.
        
        Even outbound adapters should use centralized HTTP client infrastructure.
        """
        if self._is_empty_package(f"{self.ROOT}.adapters.outbound"):
            pytest.skip("Outbound adapters package is empty - skipping test")
            
        ev = self._evaluable()
        http_libs_pattern = r"(requests|httpx|urllib3|aiohttp|http\.client|http\.server)"
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.adapters.outbound") \
                .should_not().import_modules_that().have_name_matching(http_libs_pattern) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 OUTBOUND ADAPTER HTTP CLIENT VIOLATION\n"
                f"❌ Why it failed: Outbound adapters are importing HTTP clients directly\n"
                f"🏗️  Why this matters for maintainability:\n"
                f"   • HTTP client configuration should be centralized\n"
                f"   • Direct imports scatter HTTP concerns across adapters\n"
                f"   • It makes it hard to apply cross-cutting concerns (logging, retries, etc.)\n"
                f"   • Testing becomes more complex with multiple HTTP dependencies\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Create infrastructure.clients with HTTP client wrappers\n"
                f"   2. Inject HTTP client instances into outbound adapters\n"
                f"   3. Use factory patterns for creating configured clients\n"
                f"   4. Implement common concerns (retries, timeouts) in one place\n\n"
                f"💡 Design patterns to implement:\n"
                f"   • Factory Pattern for HTTP client creation\n"
                f"   • Decorator Pattern for cross-cutting concerns\n"
                f"   • Strategy Pattern for different HTTP implementations\n"
                f"   • Adapter Pattern for third-party HTTP libraries\n\n"
                f"🛠️  Implementation strategies:\n"
                f"   • Create HttpClientFactory in infrastructure\n"
                f"   • Use configuration files for HTTP settings\n"
                f"   • Implement circuit breaker patterns\n"
                f"   • Add centralized logging and monitoring\n\n"
                f"Original error: {str(e)}"
            )

    def test_domain_should_not_import_infrastructure_clients(self):
        """
        Test that domain modules do not import infrastructure.clients.
        
        Domain should be completely independent of infrastructure concerns.
        """
        infra_clients_path = f"{self.ROOT}.infrastructure.clients"
        
        if self._is_empty_package(infra_clients_path) or self._is_empty_package(f"{self.ROOT}.domain"):
            pytest.skip("Infrastructure clients or domain package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.domain") \
                .should_not().import_modules_that().are_sub_modules_of(infra_clients_path) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 DOMAIN INFRASTRUCTURE DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Domain modules are importing infrastructure.clients\n"
                f"🏗️  Why this violates Clean Architecture:\n"
                f"   • Domain layer must be at the center with no dependencies pointing outward\n"
                f"   • Infrastructure is the outermost layer and should depend on domain\n"
                f"   • This creates a circular dependency that breaks the architecture\n"
                f"   • It makes domain logic dependent on infrastructure details\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove all imports of infrastructure.clients from domain\n"
                f"   2. Define abstract interfaces (ports) in domain.ports\n"
                f"   3. Let infrastructure.clients implement domain interfaces\n"
                f"   4. Use dependency injection to provide implementations at runtime\n\n"
                f"💡 Fundamental principles to understand:\n"
                f"   • Dependency Inversion Principle (depend on abstractions)\n"
                f"   • Clean Architecture dependency rule (inward only)\n"
                f"   • Domain-Driven Design bounded contexts\n"
                f"   • Ports and Adapters pattern\n\n"
                f"🛠️  Concrete steps:\n"
                f"   • Move interfaces to domain.ports\n"
                f"   • Use abc.ABC for abstract base classes\n"
                f"   • Implement dependency injection container\n"
                f"   • Consider using typing.Protocol for structural typing\n\n"
                f"Original error: {str(e)}"
            )

    def test_application_should_not_import_infrastructure_clients(self):
        """
        Test that application services do not import infrastructure.clients directly.
        
        Application layer should depend on domain abstractions, not infrastructure implementations.
        """
        infra_clients_path = f"{self.ROOT}.infrastructure.clients"
        
        if self._is_empty_package(infra_clients_path) or self._is_empty_package(f"{self.ROOT}.application"):
            pytest.skip("Infrastructure clients or application package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.application") \
                .should_not().import_modules_that().are_sub_modules_of(infra_clients_path) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 APPLICATION INFRASTRUCTURE DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Application services are importing infrastructure.clients\n"
                f"🏗️  Why this breaks Clean Architecture:\n"
                f"   • Application layer should only depend on domain layer\n"
                f"   • Infrastructure dependencies make application services hard to test\n"
                f"   • It couples business logic to specific infrastructure implementations\n"
                f"   • Changes in infrastructure force changes in application logic\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove infrastructure.clients imports from application services\n"
                f"   2. Depend only on interfaces defined in domain.ports\n"
                f"   3. Let the composition root inject infrastructure implementations\n"
                f"   4. Use constructor injection or dependency injection framework\n\n"
                f"💡 Patterns that will help:\n"
                f"   • Dependency Injection pattern\n"
                f"   • Repository pattern for data access\n"
                f"   • Service Layer pattern\n"
                f"   • Composition Root pattern\n\n"
                f"🛠️  Implementation techniques:\n"
                f"   • Use dependency-injector or similar DI container\n"
                f"   • Create factory functions for application services\n"
                f"   • Use pytest fixtures for testing with mocks\n"
                f"   • Consider using dataclasses or Pydantic for DTOs\n\n"
                f"Original error: {str(e)}"
            )
