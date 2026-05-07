from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase, BaseTestContext
from core.test_helpers import create_test_interactive_user
from django.contrib.auth.models import AnonymousUser
from core.models.base_mutation import MutationLog
from ..models import FormDefinition, FormSubmission


class FormSubmissionGQLTest(openIMISGraphQLTestCase):
    admin_user = None
    admin_username = "AdminFormSubmission"
    admin_password = "EdfmD3!12@#"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = create_test_interactive_user(
            username=cls.admin_username, password=cls.admin_password
        )
        cls.admin_token_context = BaseTestContext(user=cls.admin_user)
        cls.admin_token = cls.admin_token_context.get_jwt()

        # Create test form definition
        cls.form_def = FormDefinition.objects.create(
            name="Test Form for Submissions",
            form_type="standalone",
            schema={"fields": []}
        )

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

    def test_query_form_submission_authenticated(self):
        """Test formSubmission query returns results for authenticated user"""
        # Create test submission
        submission = FormSubmission.objects.create(
            form=self.form_def,
            submission_data={"field1": "value1"},
            status="draft"
        )

        query = """
        query {
            formSubmission {
                edges {
                    node {
                        id
                        data
                        status
                        formDefinition {
                            id
                            name
                        }
                    }
                }
            }
        }
        """

        response = self.query(query, headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"})
        self.assertResponseNoErrors(response)

        content = response.json()
        self.assertEqual(len(content['data']['formSubmission']['edges']), 1)
        node = content['data']['formSubmission']['edges'][0]['node']
        self.assertEqual(node['status'], "draft")
        self.assertEqual(node['formDefinition']['name'], "Test Form for Submissions")

    def test_query_form_submission_unauthenticated(self):
        """Test formSubmission query fails for anonymous user"""
        query = """
        query {
            formSubmission {
                edges {
                    node {
                        id
                    }
                }
            }
        }
        """

        response = self.query(query)
        content = response.json()
        self.assertIn('errors', content)
        self.assertEqual(content['errors'][0]['message'], "Authentication required")

    def test_create_form_submission_mutation_success(self):
        """Test createFormSubmission mutation creates a record"""
        mutation = """
        mutation createFormSubmission($input: CreateFormSubmissionMutationInput!) {
            createFormSubmission(input: $input) {
                internalId
            }
        }
        """

        variables = {
            "input": {
                "formDefinitionId": str(self.form_def.id),
                "data": '{"field1": "test value", "field2": 123}',
                "status": "draft"
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
        db_submission = FormSubmission.objects.filter(form=self.form_def, status='draft').latest('id')
        self.assertEqual(db_submission.submission_data, {"field1": "test value", "field2": 123})

    def test_create_form_submission_mutation_submitted_status(self):
        """Test createFormSubmission with submitted status sets submitted_by"""
        mutation = """
        mutation createFormSubmission($input: CreateFormSubmissionMutationInput!) {
            createFormSubmission(input: $input) {
                internalId
            }
        }
        """

        variables = {
            "input": {
                "formDefinitionId": str(self.form_def.id),
                "data": '{"response": "submitted data"}',
                "status": "submitted"
            }
        }

        response = self.send_mutation_raw(
            mutation,
            self.admin_token,
            variables_param=variables,
        )

        mutation_log = response['data']['mutationLogs']['edges'][0]['node']
        self.assertEqual(mutation_log['status'], MutationLog.SUCCESS)

        # Verify submitted_by in database
        db_submission = FormSubmission.objects.filter(form=self.form_def, status='submitted').latest('id')
        self.assertIsNotNone(db_submission.submitted_by)
        self.assertEqual(db_submission.submitted_by.username, self.admin_username)

    def test_create_form_submission_mutation_invalid_form_definition(self):
        """Test createFormSubmission fails with invalid form_definition_id"""
        mutation = """
        mutation createFormSubmission($input: CreateFormSubmissionMutationInput!) {
            createFormSubmission(input: $input) {
                internalId
            }
        }
        """

        variables = {
            "input": {
                "formDefinitionId": "99999",  # Non-existent ID
                "data": '{"field1": "value"}'
            }
        }

        response = self.send_mutation_raw(
            mutation,
            self.admin_token,
            variables_param=variables,
            follow=False,
        )

        internal_id = response['data']['createFormSubmission']['internalId']
        self.assert_mutation_error(internal_id, "FormDefinition not found")

    def test_create_form_submission_mutation_unauthenticated(self):
        """Test createFormSubmission mutation fails for anonymous user"""
        mutation = """
        mutation createFormSubmission($input: CreateFormSubmissionMutationInput!) {
            createFormSubmission(input: $input) {
                internalId
            }
        }
        """

        variables = {
            "input": {
                "formDefinitionId": str(self.form_def.id),
                "data": '{"field1": "value"}'
            }
        }

        # Send with empty token (anonymous)
        response = self.send_mutation_raw(
            mutation,
            token='',
            variables_param=variables,
            follow=False,
        )

        internal_id = response['data']['createFormSubmission']['internalId']
        self.assert_mutation_error(internal_id, "User must be authenticated")

    def test_update_form_submission_mutation_success(self):
        """Test updateFormSubmission mutation updates a record"""
        # Create initial submission
        submission = FormSubmission.objects.create(
            form=self.form_def,
            submission_data={"original": "data"},
            status="draft"
        )

        mutation = """
        mutation updateFormSubmission($input: UpdateFormSubmissionMutationInput!) {
            updateFormSubmission(input: $input) {
                internalId
            }
        }
        """

        variables = {
            "input": {
                "id": str(submission.id),
                "data": '{"updated": "data"}',
                "status": "submitted"
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
        submission.refresh_from_db()
        self.assertEqual(submission.submission_data, {"updated": "data"})
        self.assertEqual(submission.status, "submitted")
        self.assertEqual(submission.submitted_by, self.admin_user)

    def test_update_form_submission_mutation_not_found(self):
        """Test updateFormSubmission mutation fails for non-existent ID"""
        mutation = """
        mutation updateFormSubmission($input: UpdateFormSubmissionMutationInput!) {
            updateFormSubmission(input: $input) {
                internalId
            }
        }
        """

        variables = {
            "input": {
                "id": "99999",  # Non-existent ID
                "status": "submitted"
            }
        }

        response = self.send_mutation_raw(
            mutation,
            self.admin_token,
            variables_param=variables,
            follow=False,
        )

        internal_id = response['data']['updateFormSubmission']['internalId']
        self.assert_mutation_error(internal_id, "does not exist")

    def test_delete_form_submission_mutation_draft_success(self):
        """Test deleteFormSubmission mutation succeeds for draft submissions"""
        # Create draft submission
        submission = FormSubmission.objects.create(
            form=self.form_def,
            submission_data={"draft": "data"},
            status="draft"
        )

        mutation = """
        mutation deleteFormSubmission($input: DeleteFormSubmissionMutationInput!) {
            deleteFormSubmission(input: $input) {
                internalId
            }
        }
        """

        variables = {
            "input": {
                "id": str(submission.id)
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
        submission.refresh_from_db()
        self.assertIsNotNone(submission.validity_to)

    def test_delete_form_submission_mutation_submitted_fails(self):
        """Test deleteFormSubmission mutation fails for submitted submissions"""
        # Create submitted submission
        submission = FormSubmission.objects.create(
            form=self.form_def,
            submission_data={"submitted": "data"},
            status="submitted",
            submitted_by=self.admin_user
        )

        mutation = """
        mutation deleteFormSubmission($input: DeleteFormSubmissionMutationInput!) {
            deleteFormSubmission(input: $input) {
                internalId
            }
        }
        """

        variables = {
            "input": {
                "id": str(submission.id)
            }
        }

        response = self.send_mutation_raw(
            mutation,
            self.admin_token,
            variables_param=variables,
            follow=False,
        )

        internal_id = response['data']['deleteFormSubmission']['internalId']
        self.assert_mutation_error(internal_id, "Only draft submissions can be deleted")

    def test_form_submission_filtering_by_status(self):
        """Test formSubmission query filtering by status"""
        # Create submissions with different statuses
        FormSubmission.objects.create(
            form=self.form_def,
            submission_data={"status": "draft"},
            status="draft"
        )
        FormSubmission.objects.create(
            form=self.form_def,
            submission_data={"status": "submitted"},
            status="submitted",
            submitted_by=self.admin_user
        )

        query = """
        query($status: String) {
            formSubmission(status: $status) {
                edges {
                    node {
                        status
                    }
                }
            }
        }
        """

        # Filter by draft
        response = self.query(
            query,
            variables={"status": "draft"},
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        )
        self.assertResponseNoErrors(response)

        content = response.json()
        submissions = content['data']['formSubmission']['edges']
        self.assertEqual(len(submissions), 1)
        self.assertEqual(submissions[0]['node']['status'], "draft")

        # Filter by submitted
        response = self.query(
            query,
            variables={"status": "submitted"},
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        )
        self.assertResponseNoErrors(response)

        content = response.json()
        submissions = content['data']['formSubmission']['edges']
        self.assertEqual(len(submissions), 1)
        self.assertEqual(submissions[0]['node']['status'], "submitted")
