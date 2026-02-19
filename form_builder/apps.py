from django.apps import AppConfig


class FormBuilderConfig(AppConfig):
    name = 'form_builder'
    default_auto_field = 'django.db.models.BigAutoField'

    # Rights for form designers (create/edit/delete forms)
    gql_form_designer_perms = [151001]

    # Rights for viewing form definitions (to render forms)
    gql_form_definition_viewer_perms = [151002]

    # Rights for submitting standalone forms
    gql_form_submit_perms = [151003]

    # Rights for viewing form submissions
    gql_form_submission_viewer_perms = [151004]

    # Rights for writing form data into model json_ext (extensions)
    gql_form_extension_write_perms = [151005]