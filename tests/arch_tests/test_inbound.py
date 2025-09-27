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
                rf"({self.ROOT}\.application(\\..+)?|{self.ROOT}\.adapters\.inbound\.controllers(\\..+)?)"
            ) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"""
💔 INBOUND CONTROLLER BOUNDARY VIOLATION
❌ Why it failed: Controllers are importing modules outside application layer
🏗️  Why this violates Ports and Adapters:
   • Controllers are inbound adapters that translate external requests
   • They should only communicate with application layer (use cases)
   • Direct domain or infrastructure imports bypass proper layering
   • It creates tight coupling between presentation and business logic

🔧 How to fix this:
   1. Remove imports of domain, infrastructure, or outbound adapters
   2. Create application services/use cases for business operations
   3. Use DTOs for data transfer between controller and application
   4. Let application layer handle all business logic coordination

💡 Controller responsibilities in Clean Architecture:
   • Receive and validate HTTP requests
   • Convert request data to application DTOs
   • Call appropriate application use cases
   • Convert application responses to HTTP responses

🛠️  Best practices for controllers:
   • Keep controllers thin (no business logic)
   • Use dependency injection for application services
   • Implement proper error handling and status codes
   • Consider using command/query objects for complex requests

Original error: {str(e)}"""
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
                    rf"({self.ROOT}\.application(\\..+)?|{self.ROOT}\.adapters\.inbound\.cli(\\..+)?)"
            ) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"""
💔 INBOUND CLI BOUNDARY VIOLATION
❌ Why it failed: CLI adapters are importing modules outside application layer
🏗️  Why this violates architectural boundaries:
   • CLI is an inbound adapter that provides command-line interface
   • It should only interact with application layer for business operations
   • Direct access to domain or infrastructure creates coupling
   • It makes CLI dependent on implementation details

🔧 How to fix this:
   1. Remove non-application imports from CLI modules
   2. Create command classes that call application use cases
   3. Use application DTOs for data exchange
   4. Let application layer handle all business logic

💡 CLI adapter design principles:
   • Parse command-line arguments and options
   • Convert CLI input to application DTOs
   • Call application services for business operations
   • Format and display results to the user

🛠️  Implementation strategies:
   • Use click or argparse for command parsing
   • Create command classes for each CLI operation
   • Implement proper error handling and user feedback
   • Consider using rich library for better CLI experience

Original error: {str(e)}"""
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
                    rf"({self.ROOT}\.application(\\..+)?|{self.ROOT}\.adapters\.inbound\.graphql(\\..+)?)"
            ) \
                .assert_applies(ev)
        except Exception as e:
            pytest.fail(
                f"""
💔 INBOUND GRAPHQL BOUNDARY VIOLATION
❌ Why it failed: GraphQL adapters are importing modules outside application layer
🏗️  Why this violates layered architecture:
   • GraphQL resolvers are inbound adapters for query/mutation handling
   • They should only coordinate with application layer for business logic
   • Direct domain or infrastructure access breaks architectural boundaries
   • It creates tight coupling between GraphQL schema and implementation

🔧 How to fix this:
   1. Remove non-application imports from GraphQL modules
   2. Create resolver functions that call application use cases
   3. Use application DTOs for data transfer
   4. Let application layer handle all business operations

💡 GraphQL resolver responsibilities:
   • Parse GraphQL queries and mutations
   • Convert GraphQL input to application DTOs
   • Call appropriate application services
   • Convert application responses to GraphQL format

🛠️  GraphQL best practices:
   • Use data loaders to avoid N+1 query problems
   • Implement proper error handling in resolvers
   • Use GraphQL types that match application DTOs
   • Consider using federation for microservices

Original error: {str(e)}"""
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
                f"""
💔 INBOUND ADAPTER → DOMAIN DIRECT ACCESS VIOLATION
❌ Why it failed: Inbound adapters are importing domain layer directly
🏗️  Why this violates Clean Architecture:
   • Inbound adapters should not access domain directly
   • Application layer should orchestrate domain operations
   • Direct domain access bypasses application-level concerns
   • It makes presentation layer dependent on domain structure

🔧 How to fix this:
   1. Remove direct domain imports from inbound adapters
   2. Create application services that encapsulate domain operations
   3. Use application DTOs instead of domain entities in adapters
   4. Let application layer handle domain coordination

💡 Proper request flow:
   • Inbound Adapter → Application Service → Domain
   • Each layer has clear responsibilities
   • Application layer provides facade for domain operations
   • Domain remains independent of delivery mechanisms

🛠️  Architectural patterns to implement:
   • Application Service pattern for use case coordination
   • DTO pattern for data transfer between layers
   • Facade pattern for simplifying domain access
   • Command/Query pattern for complex operations

Original error: {str(e)}"""
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
                f"""
💔 INBOUND ADAPTER → INFRASTRUCTURE DEPENDENCY VIOLATION
❌ Why it failed: Inbound adapters are importing infrastructure layer
🏗️  Why this violates separation of concerns:
   • Inbound adapters handle request processing and response formatting
   • Infrastructure handles external system integration
   • These are different concerns that should not be mixed
   • It creates unnecessary coupling between adapter types

🔧 How to fix this:
   1. Remove infrastructure imports from inbound adapters
   2. Use dependency injection for shared services
   3. Let application layer coordinate with infrastructure when needed
   4. Keep inbound adapters focused on request/response handling

💡 Clear separation of adapter responsibilities:
   • Inbound: receive requests, format responses
   • Outbound: make external calls, implement domain ports
   • Infrastructure: provide technical capabilities
   • Application: orchestrate use cases and business logic

🛠️  Better architectural approaches:
   • Use application services as the coordination layer
   • Implement shared utilities in separate modules
   • Use events for decoupled communication
   • Consider middleware patterns for cross-cutting concerns

Original error: {str(e)}"""
            )
