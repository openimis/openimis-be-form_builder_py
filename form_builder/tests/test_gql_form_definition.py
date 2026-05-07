from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase, BaseTestContext
from core.test_helpers import create_test_interactive_user
from django.contrib.auth.models import AnonymousUser
from core.models.base_mutation import MutationLog
from ..models import FormDefinition


class FormDefinitionGQLTest(openIMISGraphQLTestCase):
    admin_user = None
    admin_username = "AdminFormBuilder"
    admin_password = "EdfmD3!12@#"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = create_test_interactive_user(
            username=cls.admin_username, password=cls.admin_password
        )
        cls.admin_token_context = BaseTestContext(user=cls.admin_user)
        cls.admin_token = cls.admin_token_context.get_jwt()

    def setUp(self):
        super().setUp()
        FormDefinition.objects.all().delete()

    def assert_mutation_success(self, uuid):
        mutation_result = self.get_mutation_result(uuid, self.admin_token, internal=True)
        mutation_status = mutation_result['data']['mutationLogs']['edges'][0]['node']['status']
        self.assertEqual(
            mutation_status,
            MutationLog.SUCCESS,
            mutation_result['data']['mutationLogs']['edges'][0]['node']['error']
        )

    def assert_mutation_error(self, uuid, expected_error):
        try:
            self.get_mutation_result(uuid, self.admin_token, internal=True)
            self.fail(f"Expected mutation error containing '{expected_error}' but mutation succeeded")
        except ValueError as e:
            self.assertIn(expected_error, str(e))

    def test_query_form_definition_authenticated(self):
        """Test formDefinition query returns results for authenticated user"""
        # Create test data
        form_def = FormDefinition.objects.create(
            name="Test Form",
            description="A test form",
            form_type="standalone",
            schema={"fields": []}
        )

        query = """
        query {
            formDefinition {
                edges {
                    node {
                        id
                        name
                        description
                        formType
                        schema
                    }
                }
            }
        }
        """

        response = self.query(query, headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"})
        self.assertResponseNoErrors(response)

        content = response.json()
        self.assertEqual(len(content['data']['formDefinition']['edges']), 1)
        node = content['data']['formDefinition']['edges'][0]['node']
        self.assertEqual(node['name'], "Test Form")
        self.assertEqual(node['formType'], "standalone")

    def test_query_form_definition_unauthenticated(self):
        """Test formDefinition query fails for anonymous user"""
        query = """
        query {
            formDefinition {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
        """

        response = self.query(query)
        self.assertEqual(response.status_code, 200)

        content = response.json()
        self.assertIn('errors', content)
        self.assertEqual(content['errors'][0]['message'], "Authentication required")

    def test_create_form_definition_mutation_success(self):
        """Test createFormDefinition mutation creates a record"""
        mutation = """
        mutation createFormDefinition($input: CreateFormDefinitionMutationInput!) {
            createFormDefinition(input: $input) {
                internalId
            }
        }
        """

        variables = {
            "input": {
                "name": "New Test Form",
                "description": "A newly created test form",
                "formType": "standalone",
                "schema": '{"fields": [{"name": "field1", "type": "text"}]}',
                "clientMutationId": "test-123"
            }
        }

        response = self.send_mutation_raw(
            mutation,
            self.admin_token,
            variables_param=variables,
        )

        mutation_log = response['data']['mutationLogs']['edges'][0]['node']
        self.assertEqual(mutation_log['status'], MutationLog.SUCCESS)
        # Verify in database
        db_form = FormDefinition.objects.filter(name="New Test Form").first()
        self.assertIsNotNone(db_form)
        self.assertEqual(db_form.description, "A newly created test form")
        self.assertEqual(db_form.form_type, "standalone")

    def test_create_form_definition_mutation_missing_required(self):
        """Test createFormDefinition mutation fails with missing required fields"""
        mutation = """
        mutation createFormDefinition($input: CreateFormDefinitionMutationInput!) {
            createFormDefinition(input: $input) {
                internalId
            }
        }
        """

        variables = {
            "input": {
                "name": "Incomplete Form",
                # Missing schema - should fail in service validation
                "formType": "standalone"
            }
        }

        # Use follow=False to get internalId, then check mutation log for error
        response = self.send_mutation_raw(
            mutation,
            self.admin_token,
            variables_param=variables,
            follow=False,
        )

        internal_id = response['data']['createFormDefinition']['internalId']
        self.assert_mutation_error(internal_id, "Name and schema are required")

    def test_create_form_definition_mutation_unauthenticated(self):
        """Test createFormDefinition mutation fails for anonymous user"""
        mutation = """
        mutation createFormDefinition($input: CreateFormDefinitionMutationInput!) {
            createFormDefinition(input: $input) {
                internalId
            }
        }
        """

        variables = {
            "input": {
                "name": "Should Fail",
                "formType": "standalone",
                "schema": '{"fields": []}'
            }
        }

        # Send with empty token (anonymous), get internalId from raw response
        response = self.send_mutation_raw(
            mutation,
            token='',
            variables_param=variables,
            follow=False,
        )

        internal_id = response['data']['createFormDefinition']['internalId']
        # Mutation log should contain an auth error
        self.assert_mutation_error(internal_id, "User must be authenticated")

    def test_update_form_definition_mutation_success(self):
        """Test updateFormDefinition mutation updates a record"""
        # Create form to update
        form_def = FormDefinition.objects.create(
            name="Original Form",
            description="Original description",
            form_type="standalone",
            schema={"fields": []}
        )

        mutation = """
        mutation updateFormDefinition($input: UpdateFormDefinitionMutationInput!) {
            updateFormDefinition(input: $input) {
                internalId
            }
        }
        """

        variables = {
            "input": {
                "id": str(form_def.id),
                "name": "Updated Form",
                "description": "Updated description"
            }
        }

        response = self.send_mutation_raw(
            mutation,
            self.admin_token,
            variables_param=variables,
        )

        mutation_log = response['data']['mutationLogs']['edges'][0]['node']
        self.assertEqual(mutation_log['status'], MutationLog.SUCCESS)

        # Verify in database
        form_def.refresh_from_db()
        self.assertEqual(form_def.name, "Updated Form")
        self.assertEqual(form_def.description, "Updated description")

    def test_update_form_definition_mutation_not_found(self):
        """Test updateFormDefinition mutation fails for non-existent ID"""
        mutation = """
        mutation updateFormDefinition($input: UpdateFormDefinitionMutationInput!) {
            updateFormDefinition(input: $input) {
                internalId
            }
        }
        """

        variables = {
            "input": {
                "id": "99999",  # Non-existent ID
                "name": "Should Fail"
            }
        }

        response = self.send_mutation_raw(
            mutation,
            self.admin_token,
            variables_param=variables,
            follow=False,
        )

        internal_id = response['data']['updateFormDefinition']['internalId']
        self.assert_mutation_error(internal_id, "does not exist")

    def test_delete_form_definition_mutation_success(self):
        """Test deleteFormDefinition mutation soft-deletes a record"""
        # Create form to delete
        form_def = FormDefinition.objects.create(
            name="Form to Delete",
            form_type="standalone",
            schema={"fields": []}
        )

        mutation = """
        mutation deleteFormDefinition($input: DeleteFormDefinitionMutationInput!) {
            deleteFormDefinition(input: $input) {
                internalId
            }
        }
        """

        variables = {
            "input": {
                "id": str(form_def.id)
            }
        }

        response = self.send_mutation_raw(
            mutation,
            self.admin_token,
            variables_param=variables,
        )

        mutation_log = response['data']['mutationLogs']['edges'][0]['node']
        self.assertEqual(mutation_log['status'], MutationLog.SUCCESS)

        # Verify soft delete
        form_def.refresh_from_db()
        self.assertIsNotNone(form_def.validity_to)

    def test_create_extension_form_definition_success(self):
        """Test creating an extension form definition"""
        mutation = """
        mutation createFormDefinition($input: CreateFormDefinitionMutationInput!) {
            createFormDefinition(input: $input) {
                internalId
            }
        }
        """

        variables = {
            "input": {
                "name": "Extension Form",
                "formType": "extension",
                "targetModel": "Individual",
                "schema": '{"fields": [{"name": "extra_field", "type": "text"}]}'
            }
        }

        response = self.send_mutation_raw(
            mutation,
            self.admin_token,
            variables_param=variables,
        )

        mutation_log = response['data']['mutationLogs']['edges'][0]['node']
        self.assertEqual(mutation_log['status'], MutationLog.SUCCESS)

        # Query the created object to verify its properties
        query = """
        query {
            formDefinition {
                edges {
                    node {
                        id
                        name
                        formType
                        targetModel
                    }
                }
            }
        }
        """

        response = self.query(query, headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"})
        self.assertResponseNoErrors(response)

        content = response.json()
        forms = content['data']['formDefinition']['edges']
        self.assertEqual(len(forms), 1)
        form_def = forms[0]['node']
        self.assertEqual(form_def['formType'], "extension")
        self.assertEqual(form_def['targetModel'], "Individual")
