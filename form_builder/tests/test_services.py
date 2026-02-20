from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser

from core.test_helpers import create_test_interactive_user
from ..models import FormDefinition, FormSubmission
from ..services import FormDefinitionService, FormSubmissionService


class FormDefinitionServiceTest(TestCase):
    def setUp(self):
        self.user = create_test_interactive_user(
            username="testuser",
            password="testpass",
            is_superuser=True
        )
        self.anonymous_user = AnonymousUser()

    def test_create_form_definition_success(self):
        """Test successful creation of FormDefinition"""
        service = FormDefinitionService(self.user)
        form_def = service.create(
            name="Test Form",
            description="A test form",
            form_type="standalone",
            schema={"fields": []},
            entry_point="test_menu"
        )
        self.assertEqual(form_def.name, "Test Form")
        self.assertEqual(form_def.form_type, "standalone")

    def test_create_form_definition_missing_required_fields(self):
        """Test creation fails with missing required fields"""
        service = FormDefinitionService(self.user)
        with self.assertRaises(ValueError):
            service.create(name="Test Form")  # Missing schema

        with self.assertRaises(ValueError):
            service.create(schema={"fields": []})  # Missing name

    def test_create_form_definition_invalid_form_type(self):
        """Test creation fails with invalid form_type"""
        service = FormDefinitionService(self.user)
        with self.assertRaises(ValueError):
            service.create(
                name="Test Form",
                form_type="invalid",
                schema={"fields": []},
                entry_point="test_menu"
            )

    def test_create_extension_form_requires_target_model(self):
        """Test extension form requires target_model"""
        service = FormDefinitionService(self.user)
        with self.assertRaises(ValueError):
            service.create(
                name="Extension Form",
                form_type="extension",
                schema={"fields": []}
            )

    def test_create_form_definition_extension_success(self):
        """Test successful creation of extension FormDefinition"""
        service = FormDefinitionService(self.user)
        form_def = service.create(
            name="Extension Form",
            form_type="extension",
            target_model="Individual",
            schema={"fields": []},
            entry_point="individual_extension"
        )
        self.assertEqual(form_def.form_type, "extension")
        self.assertEqual(form_def.target_model, "Individual")

    def test_update_form_definition_success(self):
        """Test successful update of FormDefinition"""
        # Create initial form
        service = FormDefinitionService(self.user)
        form_def = service.create(
            name="Original Name",
            form_type="standalone",
            schema={"fields": []},
            entry_point="original_menu"
        )

        # Update it
        updated_form = service.update(
            form_definition=form_def,
            name="Updated Name",
            description="Updated description"
        )

        self.assertEqual(updated_form.name, "Updated Name")
        self.assertEqual(updated_form.description, "Updated description")

    def test_update_form_definition_invalid_form_type(self):
        """Test update fails with invalid form_type"""
        service = FormDefinitionService(self.user)
        form_def = service.create(
            name="Test Form",
            form_type="standalone",
            schema={"fields": []},
            entry_point="test_menu"
        )

        with self.assertRaises(ValueError):
            service.update(
                form_definition=form_def,
                form_type="invalid"
            )

    def test_delete_form_definition_success(self):
        """Test successful deletion of FormDefinition"""
        service = FormDefinitionService(self.user)
        form_def = service.create(
            name="Test Form",
            form_type="standalone",
            schema={"fields": []},
            entry_point="test_menu"
        )

        result = service.delete(form_def)
        self.assertEqual(result, form_def)

        # Check it's marked as invalid (soft delete)
        form_def.refresh_from_db()
        self.assertFalse(form_def.validity_to is None)

    def test_create_form_definition_unauthenticated(self):
        """Test creation fails for unauthenticated user"""
        service = FormDefinitionService(self.anonymous_user)
        with self.assertRaises(PermissionDenied):
            service.create(
                name="Test Form",
                form_type="standalone",
                schema={"fields": []}
            )


class FormSubmissionServiceTest(TestCase):
    def setUp(self):
        self.user = create_test_interactive_user(
            username="testuser",
            password="testpass"
        )
        self.anonymous_user = AnonymousUser()
        self.form_def = FormDefinition.objects.create(
            name="Test Form",
            form_type="standalone",
            schema={"fields": []},
            entry_point="test_menu"
        )

    def test_create_form_submission_success(self):
        """Test successful creation of FormSubmission"""
        service = FormSubmissionService(self.user)
        submission = service.create(
            form=self.form_def,
            submission_data={"field1": "value1"},
            status="draft"
        )
        self.assertEqual(submission.form, self.form_def)
        self.assertEqual(submission.submission_data, {"field1": "value1"})
        self.assertEqual(submission.status, "draft")

    def test_create_form_submission_missing_form_definition(self):
        """Test creation fails without form_definition"""
        service = FormSubmissionService(self.user)
        with self.assertRaises(ValueError):
            service.create(data={"field1": "value1"})

    def test_create_form_submission_invalid_status(self):
        """Test creation fails with invalid status"""
        service = FormSubmissionService(self.user)
        with self.assertRaises(ValueError):
            service.create(
                form=self.form_def,
                status="invalid_status"
            )

    def test_create_form_submission_submitted_sets_user(self):
        """Test submitted status sets submitted_by"""
        service = FormSubmissionService(self.user)
        submission = service.create(
            form=self.form_def,
            status="submitted"
        )
        self.assertEqual(submission.status, "submitted")
        self.assertEqual(submission.submitted_by, self.user)

    def test_update_form_submission_success(self):
        """Test successful update of FormSubmission"""
        service = FormSubmissionService(self.user)
        submission = service.create(
            form=self.form_def,
            submission_data={"field1": "value1"},
            status="draft"
        )

        updated_submission = service.update(
            form_submission=submission,
            submission_data={"field1": "updated_value"},
            status="submitted"
        )

        self.assertEqual(updated_submission.submission_data, {"field1": "updated_value"})
        self.assertEqual(updated_submission.status, "submitted")
        self.assertEqual(updated_submission.submitted_by, self.user)

    def test_update_form_submission_invalid_status(self):
        """Test update fails with invalid status"""
        service = FormSubmissionService(self.user)
        submission = service.create(
            form=self.form_def,
            status="draft"
        )

        with self.assertRaises(ValueError):
            service.update(
                form_submission=submission,
                status="invalid_status"
            )

    def test_delete_form_submission_draft_success(self):
        """Test successful deletion of draft FormSubmission"""
        service = FormSubmissionService(self.user)
        submission = service.create(
            form=self.form_def,
            status="draft"
        )

        result = service.delete(submission)
        self.assertEqual(result, submission, "test deletion fails")

        # Check it's marked as invalid (soft delete)
        submission.refresh_from_db()
        self.assertFalse(submission.validity_to is None)

    def test_delete_form_submission_submitted_fails(self):
        """Test deletion fails for non-draft submissions"""
        service = FormSubmissionService(self.user)
        submission = service.create(
            form=self.form_def,
            status="submitted"
        )

        with self.assertRaises(PermissionDenied):
            service.delete(submission)

    def test_delete_form_submission_wrong_user_fails(self):
        """Test deletion fails for draft submissions by different user"""
        # Create submission as user
        service1 = FormSubmissionService(self.user)
        submission = service1.create(
            form=self.form_def,
            status="draft"
        )

        # Try to delete as different user
        user2 = create_test_interactive_user(
            username="otheruser",
            password="testpass"
        )
        service2 = FormSubmissionService(user2)

        with self.assertRaises(PermissionDenied):
            service2.delete(submission)

    def test_create_form_submission_unauthenticated(self):
        """Test creation fails for unauthenticated user"""
        service = FormSubmissionService(self.anonymous_user)
        with self.assertRaises(PermissionDenied):
            service.create(
                form=self.form_def,
                submission_data={"field1": "value1"}
            )
