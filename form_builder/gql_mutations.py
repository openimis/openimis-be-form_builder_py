import graphene
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from core.schema import OpenIMISMutation
from core.gql.gql_mutations.base_mutation import (
    BaseHistoryModelCreateMutationMixin,
    BaseHistoryModelUpdateMutationMixin,
    BaseHistoryModelDeleteMutationMixin,
    BaseMutation
)
from .services import FormDefinitionService, FormSubmissionService
from .gql_queries import FormDefinitionGQLType, FormSubmissionGQLType
from .models import FormDefinition, FormSubmission
from .apps import FormBuilderConfig


class CreateFormDefinitionMutation(BaseHistoryModelCreateMutationMixin, BaseMutation):
    """
    Create a new form definition.
    """
    _mutation_class = "CreateFormDefinitionMutation"
    _mutation_module = "form_builder"
    _model = FormDefinitionGQLType._meta.model

    class Input(OpenIMISMutation.Input):
        name = graphene.String(required=True)
        description = graphene.String()
        form_type = graphene.String(required=True)
        target_model = graphene.String()
        schema = graphene.JSONString()
        entry_point = graphene.String()

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        if not user.has_perms(FormBuilderConfig.gql_form_designer_perms):
            raise PermissionDenied("Unauthorized")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        service = FormDefinitionService(user)
        service.create(
            name=data['name'],
            description=data.get('description'),
            form_type=data['form_type'],
            target_model=data.get('target_model'),
            schema=data.get('schema'),
            entry_point=data.get('entry_point')
        )
        return None


class UpdateFormDefinitionMutation(BaseHistoryModelUpdateMutationMixin, BaseMutation):
    """
    Update an existing form definition.
    """
    _mutation_class = "UpdateFormDefinitionMutation"
    _mutation_module = "form_builder"
    _model = FormDefinitionGQLType._meta.model

    class Input(OpenIMISMutation.Input):
        id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()
        form_type = graphene.String()
        target_model = graphene.String()
        schema = graphene.JSONString()
        entry_point = graphene.String()

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        if not user.has_perms(FormBuilderConfig.gql_form_designer_perms):
            raise PermissionDenied("Unauthorized")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        try:
            form_definition = FormDefinitionGQLType._meta.model.objects.get(id=data['id'])
        except FormDefinition.DoesNotExist:
            raise Exception("FormDefinition not found")

        service = FormDefinitionService(user)
        service.update(
            form_definition=form_definition,
            name=data.get('name'),
            description=data.get('description'),
            form_type=data.get('form_type'),
            target_model=data.get('target_model'),
            schema=data.get('schema'),
            entry_point=data.get('entry_point')
        )
        return None


class DeleteFormDefinitionMutation(BaseHistoryModelDeleteMutationMixin, BaseMutation):
    """
    Delete a form definition.
    """
    _mutation_class = "DeleteFormDefinitionMutation"
    _mutation_module = "form_builder"
    _model = FormDefinitionGQLType._meta.model

    class Input(OpenIMISMutation.Input):
        id = graphene.ID(required=True)

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        if not user.has_perms(FormBuilderConfig.gql_form_designer_perms):
            raise PermissionDenied("Unauthorized")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        try:
            form_definition = FormDefinitionGQLType._meta.model.objects.get(id=data['id'])
        except FormDefinition.DoesNotExist:
            raise Exception("FormDefinition not found")

        service = FormDefinitionService(user)
        service.delete(form_definition)
        return None


class CreateFormSubmissionMutation(BaseHistoryModelCreateMutationMixin, BaseMutation):
    """
    Create a new form submission.
    """
    _mutation_class = "CreateFormSubmissionMutation"
    _mutation_module = "form_builder"
    _model = FormSubmissionGQLType._meta.model

    class Input(OpenIMISMutation.Input):
        form_definition_id = graphene.ID(required=True)
        data = graphene.JSONString()
        status = graphene.String()

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        if not user.has_perms(FormBuilderConfig.gql_form_submit_perms):
            raise PermissionDenied("Unauthorized")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        form_definition_id = data.get('form_definition_id')
        try:
            form_definition = FormDefinition.objects.get(id=form_definition_id)
        except FormDefinition.DoesNotExist:
            raise Exception("FormDefinition not found")

        service = FormSubmissionService(user)
        service.create(
            form_definition=form_definition,
            data=data.get('data'),
            status=data.get('status', 'draft')
        )
        return None


class UpdateFormSubmissionMutation(BaseHistoryModelUpdateMutationMixin, BaseMutation):
    """
    Update an existing form submission.
    """
    _mutation_class = "UpdateFormSubmissionMutation"
    _mutation_module = "form_builder"
    _model = FormSubmissionGQLType._meta.model

    class Input(OpenIMISMutation.Input):
        id = graphene.ID(required=True)
        data = graphene.JSONString()
        status = graphene.String()

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        if not user.has_perms(FormBuilderConfig.gql_form_submit_perms):
            raise PermissionDenied("Unauthorized")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        try:
            form_submission = FormSubmissionGQLType._meta.model.objects.get(id=data['id'])
        except FormSubmission.DoesNotExist:
            raise Exception("FormSubmission not found")

        service = FormSubmissionService(user)
        service.update(
            form_submission=form_submission,
            data=data.get('data'),
            status=data.get('status')
        )
        return None


class DeleteFormSubmissionMutation(BaseHistoryModelDeleteMutationMixin, BaseMutation):
    """
    Delete a form submission.
    """
    _mutation_class = "DeleteFormSubmissionMutation"
    _mutation_module = "form_builder"
    _model = FormSubmissionGQLType._meta.model

    class Input(OpenIMISMutation.Input):
        id = graphene.ID(required=True)

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        if not user.has_perms(FormBuilderConfig.gql_form_submit_perms):
            raise PermissionDenied("Unauthorized")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        try:
            form_submission = FormSubmissionGQLType._meta.model.objects.get(id=data['id'])
        except FormSubmission.DoesNotExist:
            raise Exception("FormSubmission not found")

        service = FormSubmissionService(user)
        service.delete(form_submission)
        return None
