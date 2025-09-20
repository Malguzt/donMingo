from pytestarch import Rule
from .base_arch_test import BaseArchTest
import pytest


class TestOutbound(BaseArchTest):
    """Test outbound adapter architecture constraints following Ports and Adapters pattern."""

    def test_outbound_repositories_must_implement_domain_ports(self):
        """
        Test that repository adapters implement domain port interfaces.
        
        Repositories provide data persistence according to domain contracts.
        """
        repositories_module = f"{self.ROOT}.adapters.outbound.repositories"
        if self._is_empty_package(repositories_module):
            pytest.skip("Outbound repositories package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(repositories_module) \
                .should().import_modules_that().are_sub_modules_of(f"{self.ROOT}.domain.ports") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 REPOSITORY MISSING DOMAIN PORT IMPLEMENTATION\n"
                f"❌ Why it failed: Repositories are not implementing domain port interfaces\n"
                f"🏗️  Why this is critical in Ports and Adapters:\n"
                f"   • Repositories are adapters that implement domain persistence contracts\n"
                f"   • Domain ports define what persistence operations the domain needs\n"
                f"   • Without implementing ports, repositories don't fulfill domain contracts\n"
                f"   • It breaks the dependency inversion that makes domain testable\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Define repository interfaces in domain.ports\n"
                f"   2. Implement these interfaces in outbound repository adapters\n"
                f"   3. Use abstract base classes or typing.Protocol for contracts\n"
                f"   4. Ensure repositories return domain entities, not database models\n\n"
                f"💡 Repository pattern principles:\n"
                f"   • Encapsulate data access logic\n"
                f"   • Provide collection-like interface for domain objects\n"
                f"   • Abstract away database implementation details\n"
                f"   • Return domain entities, not database records\n\n"
                f"🛠️  Implementation steps:\n"
                f"   • Create IUserRepository, IOrderRepository in domain.ports\n"
                f"   • Implement SQLUserRepository, MongoOrderRepository in adapters\n"
                f"   • Use dependency injection to provide implementations\n"
                f"   • Consider using Unit of Work pattern for transactions\n\n"
                f"Original error: {str(e)}"
            )

    def test_outbound_repositories_should_only_import_domain_layer(self):
        """
        Test that repositories only import from domain layer.
        
        Repositories should implement domain contracts without application dependencies.
        """
        repositories_module = f"{self.ROOT}.adapters.outbound.repositories"
        if self._is_empty_package(repositories_module):
            pytest.skip("Outbound repositories package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(repositories_module) \
                .should_not().import_modules_except_modules_that().have_name_matching(
                    rf"({self.ROOT}\.domain(\..+)?|{self.ROOT}\.adapters\.outbound\.repositories(\..+)?)"
                ) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 REPOSITORY INAPPROPRIATE DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Repositories are importing non-domain modules\n"
                f"🏗️  Why repositories should only depend on domain:\n"
                f"   • Repositories implement domain persistence contracts\n"
                f"   • They should be independent of application logic\n"
                f"   • Dependencies on application create circular references\n"
                f"   • It makes repositories coupled to use case specifics\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove application, infrastructure, or inbound adapter imports\n"
                f"   2. Only import domain entities, value objects, and ports\n"
                f"   3. Use dependency injection for external dependencies\n"
                f"   4. Keep repositories focused on data access only\n\n"
                f"💡 Repository responsibilities:\n"
                f"   • Implement domain repository interfaces\n"
                f"   • Convert between domain objects and database models\n"
                f"   • Handle data persistence and retrieval\n"
                f"   • Provide query capabilities for domain objects\n\n"
                f"🛠️  Clean repository design:\n"
                f"   • Create separate database models and domain entities\n"
                f"   • Use mapper classes for object conversion\n"
                f"   • Implement specification pattern for complex queries\n"
                f"   • Consider using repository base classes for common operations\n\n"
                f"Original error: {str(e)}"
            )

    def test_outbound_gateways_should_not_import_application_layer(self):
        """
        Test that gateway adapters do not import application layer.
        
        Gateways should implement domain contracts for external service access.
        """
        gateways_module = f"{self.ROOT}.adapters.outbound.gateways"
        if self._is_empty_package(gateways_module):
            pytest.skip("Outbound gateways package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(gateways_module) \
                .should_not().import_modules_that().are_sub_modules_of(f"{self.ROOT}.application") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 GATEWAY → APPLICATION DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Gateways are importing application layer modules\n"
                f"🏗️  Why this violates architectural boundaries:\n"
                f"   • Gateways are adapters that implement domain external service contracts\n"
                f"   • Application layer should depend on domain ports, not gateways\n"
                f"   • This creates circular dependencies between layers\n"
                f"   • It couples external service integration to application logic\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove application layer imports from gateways\n"
                f"   2. Implement domain gateway interfaces in domain.ports\n"
                f"   3. Let application services depend on domain ports only\n"
                f"   4. Use dependency injection to wire gateway implementations\n\n"
                f"💡 Gateway pattern principles:\n"
                f"   • Encapsulate external service communication\n"
                f"   • Implement domain-defined interfaces for external access\n"
                f"   • Abstract away external service implementation details\n"
                f"   • Convert between domain objects and external formats\n\n"
                f"🛠️  Gateway implementation strategies:\n"
                f"   • Define IPaymentGateway, IEmailGateway in domain.ports\n"
                f"   • Implement StripePaymentGateway, SendGridEmailGateway\n"
                f"   • Use adapter pattern for external library integration\n"
                f"   • Consider using circuit breaker for resilience\n\n"
                f"Original error: {str(e)}"
            )

    def test_outbound_gateways_should_only_import_domain_layer(self):
        """
        Test that gateways only import from domain layer.
        
        Gateways should implement domain contracts without other layer dependencies.
        """
        gateways_module = f"{self.ROOT}.adapters.outbound.gateways"
        if self._is_empty_package(gateways_module):
            pytest.skip("Outbound gateways package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(gateways_module) \
                .should_not().import_modules_except_modules_that().have_name_matching(
                    rf"({self.ROOT}\.domain(\..+)?|{self.ROOT}\.adapters\.outbound\.gateways(\..+)?)"
                ) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 GATEWAY INAPPROPRIATE DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Gateways are importing non-domain modules\n"
                f"🏗️  Why gateways should only depend on domain:\n"
                f"   • Gateways implement domain contracts for external services\n"
                f"   • They should be independent of application orchestration\n"
                f"   • Dependencies on other layers create coupling\n"
                f"   • It makes gateways dependent on implementation details\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove non-domain imports from gateway modules\n"
                f"   2. Only import domain entities, value objects, and ports\n"
                f"   3. Use dependency injection for infrastructure services\n"
                f"   4. Keep gateways focused on external service integration\n\n"
                f"💡 Gateway design principles:\n"
                f"   • Implement domain-defined external service interfaces\n"
                f"   • Handle protocol translation (REST, GraphQL, etc.)\n"
                f"   • Manage external service authentication and configuration\n"
                f"   • Convert between domain and external service formats\n\n"
                f"🛠️  Implementation best practices:\n"
                f"   • Use HTTP clients provided by infrastructure layer\n"
                f"   • Implement retry and circuit breaker patterns\n"
                f"   • Handle external service errors gracefully\n"
                f"   • Consider using factory pattern for gateway creation\n\n"
                f"Original error: {str(e)}"
            )

    def test_outbound_cache_implementations_should_only_import_domain_layer(self):
        """
        Test that cache implementations only import from domain layer.
        
        Cache adapters should implement domain caching contracts.
        """
        cache_module = f"{self.ROOT}.adapters.outbound.cache_impl"
        if self._is_empty_package(cache_module):
            pytest.skip("Outbound cache implementations package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(cache_module) \
                .should_not().import_modules_except_modules_that().have_name_matching(
                    rf"({self.ROOT}\.domain(\..+)?|{self.ROOT}\.adapters\.outbound\.cache_impl(\..+)?)"
                ) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 CACHE IMPLEMENTATION INAPPROPRIATE DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Cache implementations are importing non-domain modules\n"
                f"🏗️  Why cache implementations should only depend on domain:\n"
                f"   • Cache adapters implement domain caching contracts\n"
                f"   • They should be independent of application and infrastructure layers\n"
                f"   • Dependencies on other layers create unnecessary coupling\n"
                f"   • It makes caching dependent on application-specific logic\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove non-domain imports from cache implementation modules\n"
                f"   2. Only import domain entities, value objects, and ports\n"
                f"   3. Use dependency injection for cache infrastructure\n"
                f"   4. Keep cache implementations focused on caching logic only\n\n"
                f"💡 Cache adapter responsibilities:\n"
                f"   • Implement domain-defined caching interfaces\n"
                f"   • Handle serialization/deserialization of domain objects\n"
                f"   • Manage cache keys and expiration policies\n"
                f"   • Provide cache invalidation strategies\n\n"
                f"🛠️  Cache implementation strategies:\n"
                f"   • Define ICacheRepository in domain.ports\n"
                f"   • Implement RedisCache, MemoryCache adapters\n"
                f"   • Use decorator pattern for adding caching to repositories\n"
                f"   • Consider using cache-aside or write-through patterns\n\n"
                f"Original error: {str(e)}"
            )

    def test_outbound_adapters_should_not_import_inbound_adapters(self):
        """
        Test that outbound adapters do not import inbound adapters.
        
        Outbound and inbound adapters serve different purposes and should be independent.
        """
        if self._is_empty_package(f"{self.ROOT}.adapters.outbound"):
            pytest.skip("Outbound adapters package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.adapters.outbound") \
                .should_not().import_modules_that().are_sub_modules_of(f"{self.ROOT}.adapters.inbound") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 OUTBOUND → INBOUND ADAPTER DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Outbound adapters are importing inbound adapters\n"
                f"🏗️  Why this violates separation of concerns:\n"
                f"   • Outbound adapters handle external service calls and data persistence\n"
                f"   • Inbound adapters handle request processing and response formatting\n"
                f"   • These are orthogonal concerns that should not be mixed\n"
                f"   • It creates unnecessary coupling between adapter types\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove inbound adapter imports from outbound adapters\n"
                f"   2. Use application services for coordination between adapters\n"
                f"   3. Consider using domain events for decoupled communication\n"
                f"   4. Keep adapter types focused on their specific responsibilities\n\n"
                f"💡 Adapter separation principles:\n"
                f"   • Inbound: receive requests, translate to domain operations\n"
                f"   • Outbound: implement domain ports for external concerns\n"
                f"   • Application: coordinate between inbound and outbound adapters\n"
                f"   • Domain: define contracts that adapters implement\n\n"
                f"🛠️  Better architectural approaches:\n"
                f"   • Use application services as coordination layer\n"
                f"   • Implement event-driven communication between adapters\n"
                f"   • Create shared DTOs in application layer if needed\n"
                f"   • Consider using message bus for complex workflows\n\n"
                f"Original error: {str(e)}"
            )
