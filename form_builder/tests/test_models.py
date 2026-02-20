from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AnonymousUser

from core.test_helpers import create_test_interactive_user
from ..models import FormDefinition, FormSubmission


class FormDefinitionModelTest(TestCase):
    def setUp(self):
        self.user = create_test_interactive_user(
            username="testuser",
            password="testpass"
        )

    def test_form_definition_creation(self):
        """Test creating a valid FormDefinition"""
        form_def = FormDefinition.objects.create(
            name="Test Form",
            description="A test form",
            form_type="standalone",
            schema={"fields": []},
            entry_point="test_menu"
        )
        self.assertEqual(form_def.name, "Test Form")
        self.assertEqual(form_def.form_type, "standalone")
        self.assertEqual(form_def.schema, {"fields": []})

    def test_form_definition_str(self):
        """Test string representation"""
        form_def = FormDefinition.objects.create(
            name="Test Form",
            form_type="standalone",
            schema={"fields": []},
            entry_point="test_menu"
        )
        self.assertEqual(str(form_def), "Test Form")

    def test_form_type_choices(self):
        """Test form_type field choices"""
        # Valid choices
        form_def1 = FormDefinition.objects.create(
            name="Standalone Form",
            form_type="standalone",
            schema={"fields": []},
            entry_point="menu1"
        )
        form_def2 = FormDefinition.objects.create(
            name="Extension Form",
            form_type="extension",
            target_model="Individual",
            schema={"fields": []},
            entry_point="extension1"
        )
        self.assertEqual(form_def1.form_type, "standalone")
        self.assertEqual(form_def2.form_type, "extension")

    def test_extension_requires_target_model(self):
        """Test that extension forms require target_model"""
        with self.assertRaises(ValidationError):
            form_def = FormDefinition(
                name="Extension Form",
                form_type="extension",
                schema={"fields": []},
                entry_point="extension1"
            )
            form_def.full_clean()  # This should raise ValidationError

    def test_json_schema_storage(self):
        """Test JSON schema field storage and retrieval"""
        schema = {
            "fields": [
                {"name": "field1", "type": "text"},
                {"name": "field2", "type": "number"}
            ]
        }
        form_def = FormDefinition.objects.create(
            name="Complex Form",
            form_type="standalone",
            schema=schema,
            entry_point="complex_menu"
        )
        # Refresh from database
        form_def.refresh_from_db()
        self.assertEqual(form_def.schema, schema)


class FormSubmissionModelTest(TestCase):
    def setUp(self):
        self.user = create_test_interactive_user(
            username="testuser",
            password="testpass"
        )
        self.form_def = FormDefinition.objects.create(
            name="Test Form",
            form_type="standalone",
            schema={"fields": []},
            entry_point="test_menu"
        )

    def test_form_submission_creation(self):
        """Test creating a valid FormSubmission"""
        submission = FormSubmission.objects.create(
            form=self.form_def,
            submission_data={"field1": "value1"},
            status="draft"
        )
        self.assertEqual(submission.form, self.form_def)
        self.assertEqual(submission.submission_data, {"field1": "value1"})
        self.assertEqual(submission.status, "draft")
        self.assertIsNone(submission.submitted_by)

    def test_form_submission_str(self):
        """Test string representation"""
        submission = FormSubmission.objects.create(
            form=self.form_def,
            submission_data={},
            status="draft"
        )
        expected_str = f"Submission for {self.form_def.name} by {submission.submitted_by}"
        self.assertEqual(str(submission), expected_str)

    def test_status_choices(self):
        """Test status field choices"""
        statuses = ['draft', 'submitted', 'processed', 'rejected']
        for status in statuses:
            submission = FormSubmission.objects.create(
                form=self.form_def,
                submission_data={},
                status=status
            )
            self.assertEqual(submission.status, status)

    def test_submitted_by_assignment(self):
        """Test submitted_by is set when status is submitted"""
        submission = FormSubmission.objects.create(
            form=self.form_def,
            submission_data={},
            status="submitted",
            submitted_by=self.user
        )
        self.assertEqual(submission.submitted_by, self.user)

    def test_default_status(self):
        """Test default status is draft"""
        submission = FormSubmission.objects.create(
            form=self.form_def,
            submission_data={}
        )
        self.assertEqual(submission.status, "draft")

    def test_json_data_storage(self):
        """Test JSON data field storage and retrieval"""
        data = {
            "personal_info": {
                "name": "John Doe",
                "age": 30
            },
            "responses": ["yes", "no", "maybe"]
        }
        submission = FormSubmission.objects.create(
            form=self.form_def,
            submission_data=data,
            status="submitted",
            submitted_by=self.user
        )
        # Refresh from database
        submission.refresh_from_db()
        self.assertEqual(submission.submission_data, data)
