from pytestarch import Rule
from .base_arch_test import BaseArchTest
import pytest


class TestInbound(BaseArchTest):
    """Test inbound adapter architecture constraints following Ports and Adapters pattern."""

    def test_inbound_controllers_should_only_access_application_layer(self):
        """
        Test that inbound controllers only import from application layer.
        
        Controllers should translate external requests to application use cases.
        """
        controllers_module = f"{self.ROOT}.adapters.inbound.controllers"
        if self._is_empty_package(controllers_module):
            pytest.skip("Inbound controllers package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(controllers_module) \
                .should_not().import_modules_except_modules_that().have_name_matching(
                    rf"({self.ROOT}\.application(\..+)?|{self.ROOT}\.adapters\.inbound\.controllers(\..+)?)"
                ) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 INBOUND CONTROLLER BOUNDARY VIOLATION\n"
                f"❌ Why it failed: Controllers are importing modules outside application layer\n"
                f"🏗️  Why this violates Ports and Adapters:\n"
                f"   • Controllers are inbound adapters that translate external requests\n"
                f"   • They should only communicate with application layer (use cases)\n"
                f"   • Direct domain or infrastructure imports bypass proper layering\n"
                f"   • It creates tight coupling between presentation and business logic\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove imports of domain, infrastructure, or outbound adapters\n"
                f"   2. Create application services/use cases for business operations\n"
                f"   3. Use DTOs for data transfer between controller and application\n"
                f"   4. Let application layer handle all business logic coordination\n\n"
                f"💡 Controller responsibilities in Clean Architecture:\n"
                f"   • Receive and validate HTTP requests\n"
                f"   • Convert request data to application DTOs\n"
                f"   • Call appropriate application use cases\n"
                f"   • Convert application responses to HTTP responses\n\n"
                f"🛠️  Best practices for controllers:\n"
                f"   • Keep controllers thin (no business logic)\n"
                f"   • Use dependency injection for application services\n"
                f"   • Implement proper error handling and status codes\n"
                f"   • Consider using command/query objects for complex requests\n\n"
                f"Original error: {str(e)}"
            )

    def test_inbound_cli_should_only_access_application_layer(self):
        """
        Test that CLI adapters only import from application layer.
        
        CLI interfaces should provide command-line access to application use cases.
        """
        cli_module = f"{self.ROOT}.adapters.inbound.cli"
        if self._is_empty_package(cli_module):
            pytest.skip("Inbound CLI package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(cli_module) \
                .should_not().import_modules_except_modules_that().have_name_matching(
                    rf"({self.ROOT}\.application(\..+)?|{self.ROOT}\.adapters\.inbound\.cli(\..+)?)"
                ) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 INBOUND CLI BOUNDARY VIOLATION\n"
                f"❌ Why it failed: CLI adapters are importing modules outside application layer\n"
                f"🏗️  Why this violates architectural boundaries:\n"
                f"   • CLI is an inbound adapter that provides command-line interface\n"
                f"   • It should only interact with application layer for business operations\n"
                f"   • Direct access to domain or infrastructure creates coupling\n"
                f"   • It makes CLI dependent on implementation details\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove non-application imports from CLI modules\n"
                f"   2. Create command classes that call application use cases\n"
                f"   3. Use application DTOs for data exchange\n"
                f"   4. Let application layer handle all business logic\n\n"
                f"💡 CLI adapter design principles:\n"
                f"   • Parse command-line arguments and options\n"
                f"   • Convert CLI input to application DTOs\n"
                f"   • Call application services for business operations\n"
                f"   • Format and display results to the user\n\n"
                f"🛠️  Implementation strategies:\n"
                f"   • Use click or argparse for command parsing\n"
                f"   • Create command classes for each CLI operation\n"
                f"   • Implement proper error handling and user feedback\n"
                f"   • Consider using rich library for better CLI experience\n\n"
                f"Original error: {str(e)}"
            )

    def test_inbound_graphql_should_only_access_application_layer(self):
        """
        Test that GraphQL adapters only import from application layer.
        
        GraphQL resolvers should translate GraphQL queries to application use cases.
        """
        graphql_module = f"{self.ROOT}.adapters.inbound.graphql"
        if self._is_empty_package(graphql_module):
            pytest.skip("Inbound GraphQL package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(graphql_module) \
                .should_not().import_modules_except_modules_that().have_name_matching(
                    rf"({self.ROOT}\.application(\..+)?|{self.ROOT}\.adapters\.inbound\.graphql(\..+)?)"
                ) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 INBOUND GRAPHQL BOUNDARY VIOLATION\n"
                f"❌ Why it failed: GraphQL adapters are importing modules outside application layer\n"
                f"🏗️  Why this violates layered architecture:\n"
                f"   • GraphQL resolvers are inbound adapters for query/mutation handling\n"
                f"   • They should only coordinate with application layer for business logic\n"
                f"   • Direct domain or infrastructure access breaks architectural boundaries\n"
                f"   • It creates tight coupling between GraphQL schema and implementation\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove non-application imports from GraphQL modules\n"
                f"   2. Create resolver functions that call application use cases\n"
                f"   3. Use application DTOs for data transfer\n"
                f"   4. Let application layer handle all business operations\n\n"
                f"💡 GraphQL resolver responsibilities:\n"
                f"   • Parse GraphQL queries and mutations\n"
                f"   • Convert GraphQL input to application DTOs\n"
                f"   • Call appropriate application services\n"
                f"   • Convert application responses to GraphQL format\n\n"
                f"🛠️  GraphQL best practices:\n"
                f"   • Use data loaders to avoid N+1 query problems\n"
                f"   • Implement proper error handling in resolvers\n"
                f"   • Use GraphQL types that match application DTOs\n"
                f"   • Consider using federation for microservices\n\n"
                f"Original error: {str(e)}"
            )

    def test_inbound_adapters_should_not_import_domain_directly(self):
        """
        Test that inbound adapters do not import domain layer directly.
        
        Inbound adapters should go through application layer for domain access.
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
                f"🏗️  Why this violates Clean Architecture:\n"
                f"   • Inbound adapters should not access domain directly\n"
                f"   • Application layer should orchestrate domain operations\n"
                f"   • Direct domain access bypasses application-level concerns\n"
                f"   • It makes presentation layer dependent on domain structure\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove direct domain imports from inbound adapters\n"
                f"   2. Create application services that encapsulate domain operations\n"
                f"   3. Use application DTOs instead of domain entities in adapters\n"
                f"   4. Let application layer handle domain coordination\n\n"
                f"💡 Proper request flow:\n"
                f"   • Inbound Adapter → Application Service → Domain\n"
                f"   • Each layer has clear responsibilities\n"
                f"   • Application layer provides facade for domain operations\n"
                f"   • Domain remains independent of delivery mechanisms\n\n"
                f"🛠️  Architectural patterns to implement:\n"
                f"   • Application Service pattern for use case coordination\n"
                f"   • DTO pattern for data transfer between layers\n"
                f"   • Facade pattern for simplifying domain access\n"
                f"   • Command/Query pattern for complex operations\n\n"
                f"Original error: {str(e)}"
            )

    def test_inbound_adapters_should_not_import_infrastructure(self):
        """
        Test that inbound adapters do not import infrastructure layer.
        
        Inbound adapters should focus on request processing, not infrastructure concerns.
        """
        if self._is_empty_package(f"{self.ROOT}.adapters.inbound"):
            pytest.skip("Inbound adapters package is empty - skipping test")
            
        ev = self._evaluable()
        
        try:
            Rule().modules_that().are_sub_modules_of(f"{self.ROOT}.adapters.inbound") \
                .should_not().import_modules_that().are_sub_modules_of(f"{self.ROOT}.infrastructure") \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"\n💔 INBOUND ADAPTER → INFRASTRUCTURE DEPENDENCY VIOLATION\n"
                f"❌ Why it failed: Inbound adapters are importing infrastructure layer\n"
                f"🏗️  Why this violates separation of concerns:\n"
                f"   • Inbound adapters handle request processing and response formatting\n"
                f"   • Infrastructure handles external system integration\n"
                f"   • These are different concerns that should not be mixed\n"
                f"   • It creates unnecessary coupling between adapter types\n\n"
                f"🔧 How to fix this:\n"
                f"   1. Remove infrastructure imports from inbound adapters\n"
                f"   2. Use dependency injection for shared services\n"
                f"   3. Let application layer coordinate with infrastructure when needed\n"
                f"   4. Keep inbound adapters focused on request/response handling\n\n"
                f"💡 Clear separation of adapter responsibilities:\n"
                f"   • Inbound: receive requests, format responses\n"
                f"   • Outbound: make external calls, implement domain ports\n"
                f"   • Infrastructure: provide technical capabilities\n"
                f"   • Application: orchestrate use cases and business logic\n\n"
                f"🛠️  Better architectural approaches:\n"
                f"   • Use application services as the coordination layer\n"
                f"   • Implement shared utilities in separate modules\n"
                f"   • Use events for decoupled communication\n"
                f"   • Consider middleware patterns for cross-cutting concerns\n\n"
                f"Original error: {str(e)}"
            )
