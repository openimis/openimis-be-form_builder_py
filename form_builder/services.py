from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from core.services import BaseService
from .apps import FormBuilderConfig
from .models import FormDefinition, FormSubmission


class FormDefinitionService(BaseService):
    OBJECT_TYPE = FormDefinition

    def __init__(self, user, **kwargs):
        super().__init__(user, **kwargs)

    def create(self, name=None, description=None, form_type='standalone', target_model=None, schema=None, entry_point=None):
        # Check authentication
        if not self.user or isinstance(self.user, AnonymousUser) or not self.user.id:
            raise PermissionDenied("Authentication required")

        # Check permissions
        if not self.user.has_perms(FormBuilderConfig.gql_form_designer_perms) and not getattr(self.user, 'is_superuser', False):
            raise PermissionDenied("Permission denied")

        # Extract name from schema if not provided
        if not name and schema and isinstance(schema, dict) and 'name' in schema:
            name = schema['name']

        if not name or schema is None:
            raise ValueError("Name and schema are required")

        if form_type not in ['standalone', 'extension']:
            raise ValueError("Invalid form_type")

        if form_type == 'extension' and not target_model:
            raise ValueError("target_model is required for extension forms")

        form_definition = FormDefinition(
            name=name,
            description=description,
            form_type=form_type,
            target_model=target_model,
            schema=schema,
            entry_point=entry_point
        )
        form_definition.save()
        return form_definition

    def update(self, form_definition, name=None, description=None, form_type=None, target_model=None, schema=None, entry_point=None):
        # Check authentication
        if not self.user or isinstance(self.user, AnonymousUser) or not self.user.id:
            raise PermissionDenied("Authentication required")

        # Check permissions
        if not self.user.has_perms(FormBuilderConfig.gql_form_designer_perms) and not getattr(self.user, 'is_superuser', False):
            raise PermissionDenied("Permission denied")

        if not form_definition:
            raise ValueError("FormDefinition is required")

        if name is not None:
            form_definition.name = name
        if description is not None:
            form_definition.description = description
        if form_type is not None:
            if form_type not in ['standalone', 'extension']:
                raise ValueError("Invalid form_type")
            form_definition.form_type = form_type
        if target_model is not None:
            form_definition.target_model = target_model
        if schema is not None:
            form_definition.schema = schema
        if entry_point is not None:
            form_definition.entry_point = entry_point

        form_definition.save()
        return form_definition

    def delete(self, form_definition):
        # Check authentication
        if not self.user or isinstance(self.user, AnonymousUser) or not self.user.id:
            raise PermissionDenied("Authentication required")

        # Check permissions
        if not self.user.has_perms(FormBuilderConfig.gql_form_designer_perms) and not getattr(self.user, 'is_superuser', False):
            raise PermissionDenied("Permission denied")

        if not form_definition:
            raise ValueError("FormDefinition is required")

        # Soft delete by setting validity_to
        form_definition.validity_to = timezone.now()
        form_definition.save()
        return form_definition


class FormSubmissionService(BaseService):
    OBJECT_TYPE = FormSubmission

    def __init__(self, user, **kwargs):
        super().__init__(user, **kwargs)

    def create(self, form_definition=None, form=None, data=None, submission_data=None, status='draft'):
        # Check authentication
        if not self.user or isinstance(self.user, AnonymousUser) or not self.user.id:
            raise PermissionDenied("Authentication required")

        # Check permissions
        if not self.user.has_perms(FormBuilderConfig.gql_form_submit_perms) and not getattr(self.user, 'is_superuser', False):
            raise PermissionDenied("Permission denied")

        # Handle both parameter naming conventions
        form_def = form_definition or form
        submission_data_final = submission_data or data or {}

        if not form_def:
            raise ValueError("FormDefinition is required")

        if status not in ['draft', 'submitted', 'processed', 'rejected']:
            raise ValueError("Invalid status")

        form_submission = FormSubmission(
            form=form_def,
            submission_data=submission_data_final,
            status=status,
            submitted_by=self.user  # Always set submitted_by to the creator
        )
        if status == 'submitted':
            form_submission.date_submitted = timezone.now()
        form_submission.save()
        return form_submission

    def update(self, form_submission, data=None, status=None, submission_data=None):
        # Check authentication
        if not self.user or isinstance(self.user, AnonymousUser) or not self.user.id:
            raise PermissionDenied("Authentication required")

        # Check permissions - use submit or designer perms
        if not (self.user.has_perms(FormBuilderConfig.gql_form_submit_perms) or 
                self.user.has_perms(FormBuilderConfig.gql_form_designer_perms)) and not getattr(self.user, 'is_superuser', False):
            raise PermissionDenied("Permission denied")

        if not form_submission:
            raise ValueError("FormSubmission is required")

        # Handle both parameter naming conventions
        data_final = submission_data or data

        if data_final is not None:
            form_submission.submission_data = data_final
        if status is not None:
            if status not in ['draft', 'submitted', 'processed', 'rejected']:
                raise ValueError("Invalid status")
            form_submission.status = status
            if status == 'submitted':
                if not getattr(form_submission, 'date_submitted', None):
                    form_submission.date_submitted = timezone.now()
                if not form_submission.submitted_by:
                    form_submission.submitted_by = self.user

        form_submission.save()
        return form_submission

    def delete(self, form_submission):
        # Check authentication
        if not self.user or isinstance(self.user, AnonymousUser) or not self.user.id:
            raise PermissionDenied("Authentication required")

        # Check permissions
        if not (self.user.has_perms(FormBuilderConfig.gql_form_submit_perms) or 
                self.user.has_perms(FormBuilderConfig.gql_form_designer_perms)) and not getattr(self.user, 'is_superuser', False):
            raise PermissionDenied("Permission denied")

        if not form_submission:
            raise ValueError("FormSubmission is required")

        # Only allow deletion of draft submissions by the creator
        if form_submission.status != 'draft':
            raise PermissionDenied("Only draft submissions can be deleted")

        if form_submission.submitted_by and form_submission.submitted_by != self.user:
            raise PermissionDenied("Only the creator can delete their draft submission")

        # Soft delete by setting validity_to
        form_submission.validity_to = timezone.now()
        form_submission.save()
        return form_submission
