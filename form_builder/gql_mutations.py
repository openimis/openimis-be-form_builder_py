import graphene
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied

from core.schema import OpenIMISMutation
from .services import FormDefinitionService, FormSubmissionService
from .gql_queries import FormDefinitionGQLType, FormSubmissionGQLType


class CreateFormDefinitionMutation(OpenIMISMutation):
    """
    Create a new form definition.
    """
    _mutation_module = "form_builder"
    _mutation_name = "FormDefinition"
    _mutation_action = "C"

    class Input(OpenIMISMutation.Input):
        name = graphene.String(required=True)
        description = graphene.String()
        form_type = graphene.String(required=True)
        target_model = graphene.String()
        schema = graphene.JSONString(required=True)
        entry_point = graphene.String()

    @classmethod
    def async_mutate(cls, user, **data):
        if not user or user.is_anonymous:
            raise PermissionDenied("Authentication required")

        service = FormDefinitionService(user)
        form_definition = service.create(
            name=data['name'],
            description=data.get('description'),
            form_type=data['form_type'],
            target_model=data.get('target_model'),
            schema=data['schema'],
            entry_point=data.get('entry_point')
        )
        return cls(form_definition=form_definition)


class UpdateFormDefinitionMutation(OpenIMISMutation):
    """
    Update an existing form definition.
    """
    _mutation_module = "form_builder"
    _mutation_name = "FormDefinition"
    _mutation_action = "U"

    class Input(OpenIMISMutation.Input):
        id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()
        form_type = graphene.String()
        target_model = graphene.String()
        schema = graphene.JSONString()
        entry_point = graphene.String()

    @classmethod
    def async_mutate(cls, user, **data):
        if not user or user.is_anonymous:
            raise PermissionDenied("Authentication required")

        try:
            form_definition = FormDefinitionGQLType._meta.model.objects.get(id=data['id'])
        except FormDefinitionGQLType._meta.model.DoesNotExist:
            raise ValueError("FormDefinition not found")

        service = FormDefinitionService(user)
        form_definition = service.update(
            form_definition=form_definition,
            name=data.get('name'),
            description=data.get('description'),
            form_type=data.get('form_type'),
            target_model=data.get('target_model'),
            schema=data.get('schema'),
            entry_point=data.get('entry_point')
        )
        return cls(form_definition=form_definition)


class DeleteFormDefinitionMutation(OpenIMISMutation):
    """
    Delete a form definition.
    """
    _mutation_module = "form_builder"
    _mutation_name = "FormDefinition"
    _mutation_action = "D"

    class Input(OpenIMISMutation.Input):
        id = graphene.ID(required=True)

    @classmethod
    def async_mutate(cls, user, **data):
        if not user or user.is_anonymous:
            raise PermissionDenied("Authentication required")

        try:
            form_definition = FormDefinitionGQLType._meta.model.objects.get(id=data['id'])
        except FormDefinitionGQLType._meta.model.DoesNotExist:
            raise ValueError("FormDefinition not found")

        service = FormDefinitionService(user)
        form_definition = service.delete(form_definition)
        return cls(success=True)


class CreateFormSubmissionMutation(OpenIMISMutation):
    """
    Create a new form submission.
    """
    _mutation_module = "form_builder"
    _mutation_name = "FormSubmission"
    _mutation_action = "C"

    class Input(OpenIMISMutation.Input):
        form_definition_id = graphene.ID(required=True)
        data = graphene.JSONString()
        status = graphene.String()

    @classmethod
    def async_mutate(cls, user, **data):
        if not user or user.is_anonymous:
            raise PermissionDenied("Authentication required")

        try:
            form_definition = FormDefinitionGQLType._meta.model.objects.get(id=data['form_definition_id'])
        except FormDefinitionGQLType._meta.model.DoesNotExist:
            raise ValueError("FormDefinition not found")

        service = FormSubmissionService(user)
        form_submission = service.create(
            form_definition=form_definition,
            data=data.get('data'),
            status=data.get('status', 'draft')
        )
        return cls(form_submission=form_submission)


class UpdateFormSubmissionMutation(OpenIMISMutation):
    """
    Update an existing form submission.
    """
    _mutation_module = "form_builder"
    _mutation_name = "FormSubmission"
    _mutation_action = "U"

    class Input(OpenIMISMutation.Input):
        id = graphene.ID(required=True)
        data = graphene.JSONString()
        status = graphene.String()

    @classmethod
    def async_mutate(cls, user, **data):
        if not user or user.is_anonymous:
            raise PermissionDenied("Authentication required")

        try:
            form_submission = FormSubmissionGQLType._meta.model.objects.get(id=data['id'])
        except FormSubmissionGQLType._meta.model.DoesNotExist:
            raise ValueError("FormSubmission not found")

        service = FormSubmissionService(user)
        form_submission = service.update(
            form_submission=form_submission,
            data=data.get('data'),
            status=data.get('status')
        )
        return cls(form_submission=form_submission)


class DeleteFormSubmissionMutation(OpenIMISMutation):
    """
    Delete a form submission.
    """
    _mutation_module = "form_builder"
    _mutation_name = "FormSubmission"
    _mutation_action = "D"

    class Input(OpenIMISMutation.Input):
        id = graphene.ID(required=True)

    @classmethod
    def async_mutate(cls, user, **data):
        if not user or user.is_anonymous:
            raise PermissionDenied("Authentication required")

        try:
            form_submission = FormSubmissionGQLType._meta.model.objects.get(id=data['id'])
        except FormSubmissionGQLType._meta.model.DoesNotExist:
            raise ValueError("FormSubmission not found")

        service = FormSubmissionService(user)
        form_submission = service.delete(form_submission)
        return cls(success=True)