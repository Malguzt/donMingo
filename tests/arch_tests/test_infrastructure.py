from pytestarch import Rule
from .base_arch_test import BaseArchTest
import pytest


class TestInfrastructure(BaseArchTest):
    """Test infrastructure layer constraints following Clean Architecture principles."""

    def test_infrastructure_should_not_import_domain_layer(self):
        """
        Test that infrastructure layer does not import domain layer directly.

        Infrastructure should implement domain interfaces, not import domain directly.
        """
        if self._is_empty_package(f"{self.ROOT}.infrastructure"):
            pytest.skip("Infrastructure package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.infrastructure") \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.domain(\\..+)?") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 INFRASTRUCTURE → DOMAIN DIRECT IMPORT VIOLATION\n"
                f"❌ Why it failed: Infrastructure modules are importing domain layer directly\n"
                f"🏗️  Why this can be problematic:\n"
                f"   • Infrastructure should implement domain contracts, not depend on domain internals\n"
                f"   • Direct domain imports can create circular dependencies\n"
                f"   • It couples infrastructure implementations to domain structure\n"
                f"   • Better to depend on domain interfaces (ports) only\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Identify what domain concepts infrastructure actually needs\n"
                f"   2. Ensure those are exposed through domain.ports interfaces\n"
                f"   3. Import and implement only the port interfaces\n"
                f"   4. Use dependency injection to provide implementations\n\n"
                f"💡 Preferred dependency pattern:\n"
                f"   • Infrastructure implements domain.ports interfaces\n"
                f"   • Domain defines contracts without knowing implementations\n"
                f"   • Application layer depends on domain.ports abstractions\n"
                f"   • Composition root wires infrastructure implementations to ports\n\n"
                f"🛠️  Implementation strategies:\n"
                f"   • Create clear port interfaces in domain.ports\n"
                f"   • Use abstract base classes or typing.Protocol\n"
                f"   • Implement adapter patterns for external libraries\n"
                f"   • Consider using factory patterns for complex setups\n\n"
                f"Original error: {str(e)}"
            )

    def test_infrastructure_should_not_import_application_layer(self):
        """
        Test that infrastructure layer does not import application layer.

        Infrastructure should be independent of application orchestration logic.
        """
        if self._is_empty_package(f"{self.ROOT}.infrastructure"):
            pytest.skip("Infrastructure package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.infrastructure") \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.application(\\..+)?") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 INFRASTRUCTURE → APPLICATION DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Infrastructure modules are importing application layer\n"
                f"🏗️  Why this violates Clean Architecture:\n"
                f"   • Infrastructure is the outermost layer and should be independent\n"
                f"   • Application layer contains use case orchestration logic\n"
                f"   • Infrastructure should provide services, not consume application logic\n"
                f"   • This creates unwanted coupling between technical and business concerns\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove application layer imports from infrastructure\n"
                f"   2. Focus infrastructure on technical concerns only\n"
                f"   3. Use events or callbacks for infrastructure to communicate with application\n"
                f"   4. Keep infrastructure focused on external system integrations\n\n"
                f"💡 Infrastructure layer responsibilities:\n"
                f"   • Database access and ORM configuration\n"
                f"   • External API integrations\n"
                f"   • Message brokers and event buses\n"
                f"   • Framework and library configurations\n\n"
                f"🛠️  Better architectural patterns:\n"
                f"   • Use domain events for decoupled communication\n"
                f"   • Implement observer pattern for notifications\n"
                f"   • Create infrastructure services that implement domain ports\n"
                f"   • Use configuration-driven dependency injection\n\n"
                f"Original error: {str(e)}"
            )

    def test_infrastructure_should_not_import_inbound_adapters(self):
        """
        Test that infrastructure layer does not import inbound adapters.

        Infrastructure should not depend on request handling mechanisms.
        """
        if self._is_empty_package(f"{self.ROOT}.infrastructure"):
            pytest.skip("Infrastructure package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.infrastructure") \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.adapters\.inbound(\\..+)?") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 INFRASTRUCTURE → INBOUND ADAPTER DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Infrastructure modules are importing inbound adapters\n"
                f"🏗️  Why this violates separation of concerns:\n"
                f"   • Infrastructure handles external system integration\n"
                f"   • Inbound adapters handle request processing\n"
                f"   • These are different concerns that should not be mixed\n"
                f"   • It creates unnecessary coupling between technical layers\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove inbound adapter imports from infrastructure\n"
                f"   2. Keep infrastructure focused on outbound concerns\n"
                f"   3. Use shared configurations or events for cross-cutting concerns\n"
                f"   4. Consider creating separate modules for shared utilities\n\n"
                f"💡 Clear separation of adapter responsibilities:\n"
                f"   • Inbound adapters: receive and process requests\n"
                f"   • Outbound adapters: make calls to external systems\n"
                f"   • Infrastructure: provide technical capabilities\n"
                f"   • Each should be independently testable and deployable\n\n"
                f"🛠️  Design alternatives:\n"
                f"   • Create shared utility modules for common concerns\n"
                f"   • Use dependency injection for shared services\n"
                f"   • Implement event-driven architecture for decoupling\n"
                f"   • Consider using middleware patterns for cross-cutting concerns\n\n"
                f"Original error: {str(e)}"
            )

    def test_infrastructure_orm_modules_should_not_import_core_layers(self):
        """
        Test that infrastructure ORM modules maintain proper boundaries.

        ORM configurations should be independent of core business logic.
        """
        orm_module = f"{self.ROOT}.infrastructure.orm"
        if self._is_empty_package(orm_module):
            pytest.skip("Infrastructure ORM package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(orm_module) \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.(domain|application|adapters\.inbound)(\\..+)?") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 INFRASTRUCTURE ORM → CORE LAYERS VIOLATION\n"
                f"❌ Why it failed: ORM modules are importing core layers inappropriately\n"
                f"🏗️  Why this creates architectural problems:\n"
                f"   • ORM is a database technology concern, not business logic\n"
                f"   • Direct imports can create tight coupling to domain structure\n"
                f"   • It makes database schema changes affect business logic\n"
                f"   • Testing becomes harder with database-business logic coupling\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove core layer imports from ORM modules\n"
                f"   2. Create separate database models from domain entities\n"
                f"   3. Use mapping functions to convert between database and domain models\n"
                f"   4. Keep ORM focused on database schema and relationships\n\n"
                f"💡 Data mapping strategies:\n"
                f"   • Create separate database models and domain entities\n"
                f"   • Use mapper classes to convert between representations\n"
                f"   • Apply Repository pattern for data access abstraction\n"
                f"   • Consider using Data Transfer Objects (DTOs)\n\n"
                f"🛠️  Implementation approaches:\n"
                f"   • Use SQLAlchemy models for database schema\n"
                f"   • Create domain entities as pure Python classes\n"
                f"   • Implement repository classes for data access\n"
                f"   • Use factory patterns for complex object creation\n\n"
                f"Original error: {str(e)}"
            )

    def test_infrastructure_http_modules_should_not_import_core_layers(self):
        """
        Test that infrastructure HTTP modules maintain proper boundaries.

        HTTP client configurations should be independent of business logic.
        """
        http_module = f"{self.ROOT}.infrastructure.http"
        if self._is_empty_package(http_module):
            pytest.skip("Infrastructure HTTP package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(http_module) \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.(domain|application|adapters\.inbound)(\\..+)?") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 INFRASTRUCTURE HTTP → CORE LAYERS VIOLATION\n"
                f"❌ Why it failed: HTTP infrastructure modules are importing core layers\n"
                f"🏗️  Why this violates infrastructure boundaries:\n"
                f"   • HTTP infrastructure should provide technical capabilities only\n"
                f"   • Business logic should not be mixed with HTTP client configuration\n"
                f"   • It creates coupling between network concerns and business rules\n"
                f"   • Testing becomes more complex with mixed responsibilities\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove core layer imports from HTTP infrastructure\n"
                f"   2. Focus on HTTP client configuration and utilities\n"
                f"   3. Let outbound adapters use HTTP infrastructure services\n"
                f"   4. Keep HTTP concerns separate from business logic\n\n"
                f"💡 HTTP infrastructure responsibilities:\n"
                f"   • HTTP client factories and configuration\n"
                f"   • Connection pooling and retry mechanisms\n"
                f"   • Authentication and security concerns\n"
                f"   • Logging and monitoring of HTTP requests\n\n"
                f"🛠️  Better design patterns:\n"
                f"   • Create HttpClientFactory for configured clients\n"
                f"   • Implement decorator pattern for cross-cutting concerns\n"
                f"   • Use dependency injection for HTTP client configuration\n"
                f"   • Consider using adapter pattern for different HTTP libraries\n\n"
                f"Original error: {str(e)}"
            )

    def test_infrastructure_config_modules_should_not_import_core_layers(self):
        """
        Test that infrastructure configuration modules maintain proper boundaries.

        Configuration should be technical concern, not business logic.
        """
        config_module = f"{self.ROOT}.infrastructure.config"
        if self._is_empty_package(config_module):
            pytest.skip("Infrastructure config package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(config_module) \
                .should_not().import_modules_that().have_name_matching(
                    rf"{self.ROOT}\.(domain|application|adapters\.inbound)(\\..+)?"
            ) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 INFRASTRUCTURE CONFIG → CORE LAYERS VIOLATION\n"
                f"❌ Why it failed: Configuration modules are importing core layers\n"
                f"🏗️  Why configuration should be independent:\n"
                f"   • Configuration is about environment and deployment concerns\n"
                f"   • Business logic should not be mixed with configuration\n"
                f"   • It makes configuration dependent on business domain changes\n"
                f"   • Testing configuration becomes unnecessarily complex\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove core layer imports from configuration modules\n"
                f"   2. Focus on environment variables and settings management\n"
                f"   3. Use configuration objects that can be injected where needed\n"
                f"   4. Keep configuration simple and domain-agnostic\n\n"
                f"💡 Configuration design principles:\n"
                f"   • Configuration should be external to application logic\n"
                f"   • Use environment variables for deployment-specific settings\n"
                f"   • Create configuration classes for type safety\n"
                f"   • Validate configuration at application startup\n"
                f"   • Consider using factory pattern for creating configured objects\n"
                f"   • Consider using configuration files for complex setups\n\n"
                f"Original error: {str(e)}"
            )