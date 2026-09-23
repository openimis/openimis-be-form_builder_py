from django.db import models
from django.conf import settings
from core.models import OpenIMISBusinessModel


class FormDefinition(OpenIMISBusinessModel):
    """
    Stores form definitions created by the form designer.
    The schema field contains the full form definition as an opaque JSON blob.
    """

    @classmethod
    def get_rights(cls, action):
        """
        Les droits regissant une action sur une definition de formulaire.

        Ne redeclare rien : la table des droits est `form_builder.apps.DJANGO_PERMS`,
        par entite puis par action. `configured_perms` y lit la valeur *configuree* -
        celle que ModuleConfiguration a pu surcharger - et non le defaut declare, et la
        lit a l'appel : les attributs `_perms` ne valent leur valeur qu'apres `ready()`.

        Actions : "query" (lire/afficher) et "design" (concevoir, c'est-a-dire creer,
        modifier ou supprimer).
        """
        from form_builder.apps import configured_perms

        return configured_perms("formDefinition", action)

    name = models.CharField(max_length=200, help_text="Human-readable title")
    description = models.TextField(blank=True, null=True, help_text="Optional description")
    form_type = models.CharField(
        max_length=20,
        choices=[('standalone', 'Standalone'), ('extension', 'Extension')],
        help_text="Standalone forms create submissions; extensions modify model json_ext"
    )
    target_model = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Model name for extensions (e.g., 'Individual', 'Policy')"
    )
    schema = models.JSONField(help_text="Full form definition JSON (opaque to BE)")
    entry_point = models.CharField(
        max_length=200,
        help_text="Standalone: submenu key; Extension: contribution point key",
        blank=True,
        null=True
    )
    submit_actions = models.JSONField(
        blank=True,
        null=True,
        help_text="ETL mapping, processing pipelines (null for extensions)"
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Form Definition"
        verbose_name_plural = "Form Definitions"

    def __str__(self):
        return self.name


class FormSubmission(OpenIMISBusinessModel):
    """
    Stores submitted data for standalone forms only.
    Extensions write directly to model.json_ext.
    """

    # Pas de `scope_parent` vers `form` : une soumission n'est pas une sous-ressource
    # de sa definition. Elle a ses propres droits (151003/151004) parce que les deux
    # populations different - qui remplit un formulaire ne le concoit pas - et son
    # proprietaire metier est `submitted_by`, pas le formulaire. Heriter du droit de la
    # definition ferait de tout lecteur de formulaire un lecteur des reponses.

    @classmethod
    def get_rights(cls, action):
        """
        Les droits regissant une action sur une soumission.

        Meme point d'acces que `FormDefinition.get_rights`, sur l'entite
        "formSubmission" : "query" (relire les soumissions et leur `submission_data`)
        et "submit" (deposer, modifier ou supprimer sa soumission).
        """
        from form_builder.apps import configured_perms

        return configured_perms("formSubmission", action)

    form = models.ForeignKey(
        FormDefinition,
        on_delete=models.CASCADE,
        limit_choices_to={'form_type': 'standalone'}
    )
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    submission_data = models.JSONField(help_text="Raw submitted field values {field_name: value, ...}")
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('processed', 'Processed'),
            ('rejected', 'Rejected')
        ],
        default='draft'
    )
    date_submitted = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Form Submission"
        verbose_name_plural = "Form Submissions"

    def __str__(self):
        return f"Submission for {self.form.name} by {self.submitted_by}"