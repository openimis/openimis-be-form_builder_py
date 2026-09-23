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

    # Les trois lectures du module ne testaient que l'authentification. Les droits
    # existent pourtant, ils sont catalogues dans `permissions_map.json` et les roles
    # peuvent les porter - mais 151002 et 151004 n'avaient aucune occurrence en
    # dehors de `apps.py`. Or `FormSubmissionGQLType.get_queryset` renvoie *toutes*
    # les soumissions valides, sans filtre sur `submitted_by` ni sur le formulaire, et
    # le champ `data` expose `submission_data`, c'est-a-dire les reponses saisies
    # brutes. Un compte sans aucun droit `form_builder` lisait donc tout.
    def resolve_formDefinition(self, info, **kwargs):
        if not info.context.user or info.context.user.is_anonymous:
            raise PermissionDenied("Authentication required")
        if not info.context.user.has_perms(
            FormBuilderConfig.gql_form_definition_viewer_perms
        ):
            raise PermissionDenied("Unauthorized")
        qs = FormDefinitionGQLType.get_queryset(None, info)
        if kwargs.get('uuid'):
            qs = qs.filter(uuid=kwargs['uuid'])
        return qs

    def resolve_formSubmission(self, info, **kwargs):
        if not info.context.user or info.context.user.is_anonymous:
            raise PermissionDenied("Authentication required")
        if not info.context.user.has_perms(
            FormBuilderConfig.gql_form_submission_viewer_perms
        ):
            raise PermissionDenied("Unauthorized")
        return FormSubmissionGQLType.get_queryset(None, info)

    # Contenu statique (la liste des types de contrôles de la boite a outils), donc
    # sans enjeu de donnees - mais il n'y a pas de raison de le laisser ouvert. Le OU
    # entre les deux droits est **voulu et dit ici** : la boite a outils sert aussi
    # bien a concevoir un formulaire (151001) qu'a en afficher un (151002), et rien
    # ne justifie d'exiger les deux.
    def resolve_formControlsSchema(self, info, **kwargs):
        if not info.context.user or info.context.user.is_anonymous:
            raise PermissionDenied("Authentication required")
        if not info.context.user.has_perms(
            list(FormBuilderConfig.gql_form_designer_perms)
            + list(FormBuilderConfig.gql_form_definition_viewer_perms)
        ):
            raise PermissionDenied("Unauthorized")
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
