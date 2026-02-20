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
    form_definition = OrderedDjangoFilterConnectionField(
        FormDefinitionGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        dateValidFrom__Gte=graphene.DateTime(),
        dateValidTo__Lte=graphene.DateTime(),
        applyDefaultValidityFilter=graphene.Boolean(),
        client_mutation_id=graphene.String(),
    )

    form_submission = OrderedDjangoFilterConnectionField(
        FormSubmissionGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        dateValidFrom__Gte=graphene.DateTime(),
        dateValidTo__Lte=graphene.DateTime(),
        applyDefaultValidityFilter=graphene.Boolean(),
        client_mutation_id=graphene.String(),
    )

    def resolve_form_definition(self, info, **kwargs):
        if not info.context.user or info.context.user.is_anonymous:
            raise PermissionDenied("Authentication required")
        return FormDefinitionGQLType.get_queryset(None, info)

    def resolve_form_submission(self, info, **kwargs):
        if not info.context.user or info.context.user.is_anonymous:
            raise PermissionDenied("Authentication required")
        return FormSubmissionGQLType.get_queryset(None, info)


class Mutation(graphene.ObjectType):
    create_form_definition = CreateFormDefinitionMutation.Field()
    update_form_definition = UpdateFormDefinitionMutation.Field()
    delete_form_definition = DeleteFormDefinitionMutation.Field()

    create_form_submission = CreateFormSubmissionMutation.Field()
    update_form_submission = UpdateFormSubmissionMutation.Field()
    delete_form_submission = DeleteFormSubmissionMutation.Field()