from django.apps import AppConfig

from core.rights_declaration import RightsDeclaration

MODULE_NAME = "form_builder"


# Droits, par entite puis par action.
#
# Deux entites portent un modele - `formDefinition` (le formulaire concu) et
# `formSubmission` (les reponses saisies) - et chacune separe sa lecture de son
# ecriture, parce que ce sont deux populations distinctes : on remplit un formulaire
# sans avoir le droit de le concevoir, et on relit les soumissions sans avoir celui
# d'en deposer.
#
# `design` et `submit` ne sont pas des actions canoniques et ne sont volontairement pas
# eclatees en create/update/delete : le module n'a qu'un seul entier pour les trois
# ecritures de chaque entite (151001 cote definition, 151003 cote soumission), et
# declarer trois actions pour un seul identifiant laisserait croire a trois droits
# separes. `design` est le vocabulaire du module lui-meme (le "form designer").
#
# Les noms django sont declaratifs : les modeles ne declarent pas `design_`, `submit_`
# ni `write_` dans leur `Meta.permissions`, donc ces noms ne sont pas encore des lignes
# `auth_permission` accordables. C'est l'entier qui est applique.
DJANGO_PERMS = {
    "formDefinition": {
        "query": ("form_builder.view_formdefinition", 151002),
        "design": ("form_builder.design_formdefinition", 151001),
    },
    "formSubmission": {
        "query": ("form_builder.view_formsubmission", 151004),
        "submit": ("form_builder.submit_formsubmission", 151003),
    },
    # Declaration en avance de phase : un formulaire de type "extension" ecrit dans le
    # `json_ext` d'un modele tiers (Individual, Policy...) plutot que dans une
    # FormSubmission. Ce chemin d'ecriture n'existe pas encore cote backend - 151005
    # n'a aucun site d'appel - mais l'identifiant est deja catalogue dans
    # `permissions_map.json` et des roles peuvent le porter. On le conserve plutot que
    # de le supprimer puis de le recreer avec un autre entier.
    "formExtension": {
        "write": ("form_builder.write_formextension", 151005),
    },
}

_PERM_CFG = {
    "gql_form_definition_viewer_perms": ("formDefinition", "query"),
    "gql_form_designer_perms": ("formDefinition", "design"),
    "gql_form_submission_viewer_perms": ("formSubmission", "query"),
    "gql_form_submit_perms": ("formSubmission", "submit"),
    "gql_form_extension_write_perms": ("formExtension", "write"),
}

RIGHTS = RightsDeclaration(MODULE_NAME, DJANGO_PERMS, _PERM_CFG)

perms = RIGHTS.perms
django_perms = RIGHTS.django_perm_names
configured_perms = RIGHTS.configured
require = RIGHTS.require


class FormBuilderConfig(AppConfig):
    name = MODULE_NAME
    default_auto_field = 'django.db.models.BigAutoField'

    # Droits: constantes, plus surchargeables. Ils ne passent ni par un DEFAULT_CFG ni
    # par ready(): `ModuleConfiguration.get_or_default` ignore toute cle `_perms`
    # stockee en base. Les valeurs sont des chaines decimales, comme dans les autres
    # modules - `has_perms` compare `str(perm)`, donc les entiers utilises jusqu'ici
    # fonctionnaient, mais une seule forme evite d'avoir a le savoir.

    # Concevoir un formulaire : le creer, le modifier, le supprimer.
    gql_form_designer_perms = RIGHTS.perms("formDefinition", "design")

    # Lire une definition de formulaire, c'est-a-dire pouvoir l'afficher.
    gql_form_definition_viewer_perms = RIGHTS.perms("formDefinition", "query")

    # Deposer une soumission sur un formulaire autonome.
    gql_form_submit_perms = RIGHTS.perms("formSubmission", "submit")

    # Relire les soumissions, `submission_data` compris.
    gql_form_submission_viewer_perms = RIGHTS.perms("formSubmission", "query")

    # Droit dormant : aucun site d'appel, voir le commentaire sur `formExtension`.
    gql_form_extension_write_perms = RIGHTS.perms("formExtension", "write")
