from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase, BaseTestContext
from core.test_helpers import create_test_interactive_user
from django.contrib.auth.models import AnonymousUser
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
                formDefinition {
                    id
                    name
                    description
                    formType
                    schema
                }
                clientMutationId
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

        response = self.query(
            mutation,
            variables=variables,
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        )
        self.assertResponseNoErrors(response)

        content = response.json()
        form_def = content['data']['createFormDefinition']['formDefinition']
        self.assertEqual(form_def['name'], "New Test Form")
        self.assertEqual(form_def['formType'], "standalone")

        # Verify in database
        db_form = FormDefinition.objects.get(name="New Test Form")
        self.assertEqual(db_form.description, "A newly created test form")

    def test_create_form_definition_mutation_missing_required(self):
        """Test createFormDefinition mutation fails with missing required fields"""
        mutation = """
        mutation createFormDefinition($input: CreateFormDefinitionMutationInput!) {
            createFormDefinition(input: $input) {
                formDefinition {
                    id
                    name
                }
            }
        }
        """

        variables = {
            "input": {
                "name": "Incomplete Form",
                # Missing schema
                "formType": "standalone"
            }
        }

        response = self.query(
            mutation,
            variables=variables,
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        )

        content = response.json()
        self.assertIn('errors', content)
        self.assertIn("Name and schema are required", content['errors'][0]['message'])

    def test_create_form_definition_mutation_unauthenticated(self):
        """Test createFormDefinition mutation fails for anonymous user"""
        mutation = """
        mutation createFormDefinition($input: CreateFormDefinitionMutationInput!) {
            createFormDefinition(input: $input) {
                formDefinition {
                    id
                }
            }
        }
        """

        variables = {
            "input": {
                "name": "Unauthorized Form",
                "formType": "standalone",
                "schema": '{"fields": []}'
            }
        }

        response = self.query(mutation, variables=variables)
        content = response.json()
        self.assertIn('errors', content)
        self.assertEqual(content['errors'][0]['message'], "Authentication required")

    def test_update_form_definition_mutation_success(self):
        """Test updateFormDefinition mutation updates a record"""
        # Create initial form
        form_def = FormDefinition.objects.create(
            name="Original Form",
            description="Original description",
            form_type="standalone",
            schema={"fields": []}
        )

        mutation = """
        mutation updateFormDefinition($input: UpdateFormDefinitionMutationInput!) {
            updateFormDefinition(input: $input) {
                formDefinition {
                    id
                    name
                    description
                }
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

        response = self.query(
            mutation,
            variables=variables,
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        )
        self.assertResponseNoErrors(response)

        content = response.json()
        updated_form = content['data']['updateFormDefinition']['formDefinition']
        self.assertEqual(updated_form['name'], "Updated Form")
        self.assertEqual(updated_form['description'], "Updated description")

    def test_update_form_definition_mutation_not_found(self):
        """Test updateFormDefinition mutation fails for non-existent ID"""
        mutation = """
        mutation updateFormDefinition($input: UpdateFormDefinitionMutationInput!) {
            updateFormDefinition(input: $input) {
                formDefinition {
                    id
                }
            }
        }
        """

        variables = {
            "input": {
                "id": "99999",  # Non-existent ID
                "name": "Should Fail"
            }
        }

        response = self.query(
            mutation,
            variables=variables,
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        )

        content = response.json()
        self.assertIn('errors', content)
        self.assertIn("FormDefinition not found", content['errors'][0]['message'])

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
                success
            }
        }
        """

        variables = {
            "input": {
                "id": str(form_def.id)
            }
        }

        response = self.query(
            mutation,
            variables=variables,
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        )
        self.assertResponseNoErrors(response)

        content = response.json()
        self.assertTrue(content['data']['deleteFormDefinition']['success'])

        # Verify soft delete
        form_def.refresh_from_db()
        self.assertIsNotNone(form_def.validity_to)

    def test_create_extension_form_definition_success(self):
        """Test creating an extension form definition"""
        mutation = """
        mutation createFormDefinition($input: CreateFormDefinitionMutationInput!) {
            createFormDefinition(input: $input) {
                formDefinition {
                    id
                    name
                    formType
                    targetModel
                }
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

        response = self.query(
            mutation,
            variables=variables,
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        )
        self.assertResponseNoErrors(response)

        content = response.json()
        form_def = content['data']['createFormDefinition']['formDefinition']
        self.assertEqual(form_def['formType'], "extension")
        self.assertEqual(form_def['targetModel'], "Individual")