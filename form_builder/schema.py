import graphene
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from core.schema import OrderedDjangoFilterConnectionField
from core.utils import append_validity_filter
from .apps import FormBuilderConfig
from .gql_mutations import (
    CreateFormDefinitionMutation,
    UpdateFormDefinitionMutation,
    DeleteFormDefinitionMutation,
    CreateFormSubmissionMutation,
    UpdateFormSubmissionMutation,
    DeleteFormSubmissionMutation,
)
from .gql_queries import FormDefinitionGQLType, FormSubmissionGQLType


class Query(graphene.ObjectType):
    formDefinition = OrderedDjangoFilterConnectionField(
        FormDefinitionGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        uuid=graphene.UUID(),
        dateValidFrom__Gte=graphene.DateTime(),
        dateValidTo__Lte=graphene.DateTime(),
        applyDefaultValidityFilter=graphene.Boolean(),
        client_mutation_id=graphene.String(),
    )

    formSubmission = OrderedDjangoFilterConnectionField(
        FormSubmissionGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        dateValidFrom__Gte=graphene.DateTime(),
        dateValidTo__Lte=graphene.DateTime(),
        applyDefaultValidityFilter=graphene.Boolean(),
        client_mutation_id=graphene.String(),
    )

    formControlsSchema = graphene.JSONString()

    def resolve_formDefinition(self, info, **kwargs):
        if not info.context.user or info.context.user.is_anonymous:
            raise PermissionDenied("Authentication required")
        qs = FormDefinitionGQLType.get_queryset(None, info)
        if kwargs.get('uuid'):
            qs = qs.filter(uuid=kwargs['uuid'])
        return qs

    def resolve_formSubmission(self, info, **kwargs):
        if not info.context.user or info.context.user.is_anonymous:
            raise PermissionDenied("Authentication required")
        return FormSubmissionGQLType.get_queryset(None, info)

    def resolve_formControlsSchema(self, info, **kwargs):
        if not info.context.user or info.context.user.is_anonymous:
            raise PermissionDenied("Authentication required")
        # Return JSON schema for available controls in the form designer toolbox
        # Can be expanded to load from fixtures/demo/controls/control.json
        return {
            "controls": [
                {"type": "text", "label": "Text Input", "category": "basic"},
                {"type": "textarea", "label": "Text Area", "category": "basic"},
                {"type": "number", "label": "Number", "category": "basic"},
                {"type": "select", "label": "Select", "category": "basic"},
                {"type": "checkbox", "label": "Checkbox", "category": "basic"},
                {"type": "radio", "label": "Radio Group", "category": "basic"},
                {"type": "date", "label": "Date", "category": "advanced"},
                {"type": "file", "label": "File Upload", "category": "advanced"},
            ],
            "layouts": ["grid", "flex"]
        }


class Mutation(graphene.ObjectType):
    createFormDefinition = CreateFormDefinitionMutation.Field()
    updateFormDefinition = UpdateFormDefinitionMutation.Field()
    deleteFormDefinition = DeleteFormDefinitionMutation.Field()

    createFormSubmission = CreateFormSubmissionMutation.Field()
    updateFormSubmission = UpdateFormSubmissionMutation.Field()
    deleteFormSubmission = DeleteFormSubmissionMutation.Field()
