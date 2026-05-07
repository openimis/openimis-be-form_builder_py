import graphene
from django.db.models import Q
from graphene_django import DjangoObjectType

from core import ExtendedConnection
from core.schema import OrderedDjangoFilterConnectionField
from core.utils import append_validity_filter
from .models import FormDefinition, FormSubmission


class FormDefinitionGQLType(DjangoObjectType):
    form_type = graphene.String()
    uuid = graphene.UUID(source='uuid')

    class Meta:
        model = FormDefinition
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            'name': ['exact', 'icontains'],
            'form_type': ['exact'],
            'target_model': ['exact', 'icontains'],
            'entry_point': ['exact', 'icontains'],
        }
        connection_class = ExtendedConnection

    @classmethod
    def get_queryset(cls, queryset, info):
        return FormDefinition.objects.filter(*append_validity_filter())


class FormSubmissionGQLType(DjangoObjectType):
    status = graphene.String()
    data = graphene.JSONString()
    form_definition = graphene.Field(FormDefinitionGQLType)
    uuid = graphene.String(source='uuid')

    class Meta:
        model = FormSubmission
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            'uuid': ['exact'],
            'status': ['exact'],
            'date_submitted': ['gte', 'lte'],
            'submitted_by': ['exact'],
            'form': ['exact'],
            'form__uuid': ['exact'],
            'form__name': ['exact', 'icontains'],
            'form__form_type': ['exact'],
        }
        connection_class = ExtendedConnection

    def resolve_data(self, info):
        return self.submission_data

    def resolve_form_definition(self, info):
        return self.form

    def resolve_submitted_by(self, info):
        return self.submitted_by

    @classmethod
    def get_queryset(cls, queryset, info):
        return FormSubmission.objects.filter(*append_validity_filter())
