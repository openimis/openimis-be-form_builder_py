"""
Garde-fous sur la declaration des droits de form_builder.

Meme structure que `claim`, `core` et `api_etl` : `DJANGO_PERMS` par entite puis par
action, `_PERM_CFG` qui en derive les cles de config, et `Model.get_rights` comme point
d'acces. Deux particularites de ce module sont verrouillees ici :

  * les valeurs etaient des entiers (`[151002]`) et non des chaines. Les deux
    fonctionnent - `User.has_perm` compare `str(perm)` - mais la forme chaine est celle
    des autres modules, et ce test l'epingle pour qu'on n'y revienne pas par accident ;
  * `gql_form_extension_write_perms` (151005) n'a aucun site d'appel : le chemin
    d'ecriture des formulaires "extension" (ecrire dans le `json_ext` d'un modele
    tiers) n'est pas implemente. C'est une declaration en avance de phase, conservee
    parce que l'identifiant est deja catalogue et peut etre porte par des roles.

Ce qui est verrouille : le couple entite/action, pas seulement les valeurs.
  * un identifiant a un seul endroit (DJANGO_PERMS), donc pas de derive ;
  * une cle de config sans attribut de classe est illisible au site d'appel ;
  * `has_perms([])` renvoie True, donc une liste vide accorde a tous.
"""

import json
import os

from django.test import TestCase

from form_builder.apps import (
    DJANGO_PERMS,
    FormBuilderConfig,
    _PERM_CFG,
    configured_perms,
    django_perms,
    perms,
)
from form_builder.models import FormDefinition, FormSubmission

# The identifiers as deployed. Changing one is incompatible with the existing roles:
# this test has to be updated *and* the new right granted.
EXPECTED_RIGHTS = {
    "gql_form_designer_perms": ["151001"],
    "gql_form_definition_viewer_perms": ["151002"],
    "gql_form_submit_perms": ["151003"],
    "gql_form_submission_viewer_perms": ["151004"],
    "gql_form_extension_write_perms": ["151005"],
}

# The `permissions_map.json` keys that carry these same identifiers. Elles sont
# derivees des noms de cles `_perms`, pas des noms django, d'ou la forme
# `form_builder.form_designer`.
EXPECTED_MAP_ENTRIES = {
    "form_builder.form_designer": "151001",
    "form_builder.form_definition_viewer": "151002",
    "form_builder.form_submit": "151003",
    "form_builder.form_submission_viewer": "151004",
    "form_builder.form_extension_write": "151005",
}

# Droits declares que rien ne controle encore, et pourquoi on les garde.
DORMANT = {("formExtension", "write")}


def _load_permissions_map():
    """`permissions_map.json` lives in the assembly, not in the package."""
    from django.conf import settings

    candidates = [
        os.path.join(str(settings.BASE_DIR), "permissions_map.json"),
        os.path.join(os.path.dirname(str(settings.BASE_DIR)), "permissions_map.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            with open(path) as handle:
                return json.load(handle)
    return None


class FormBuilderPermissionDeclarationTestCase(TestCase):
    def test_right_ids_unchanged(self):
        self.assertEqual(
            {key: getattr(FormBuilderConfig, key) for key in EXPECTED_RIGHTS},
            EXPECTED_RIGHTS,
        )

    def test_rights_are_decimal_strings(self):
        """Les entiers marchaient, mais la convention des autres modules est la chaine."""
        for key in _PERM_CFG:
            with self.subTest(key=key):
                for right in getattr(FormBuilderConfig, key):
                    self.assertIsInstance(right, str)

    def test_perm_cfg_covers_every_declared_action(self):
        declared = {
            (entity, action)
            for entity, actions in DJANGO_PERMS.items()
            for action in actions
        }
        self.assertEqual(set(_PERM_CFG.values()), declared)

    def test_perm_cfg_matches_config_attributes(self):
        missing = [key for key in _PERM_CFG if not hasattr(FormBuilderConfig, key)]
        self.assertEqual(missing, [])

    def test_no_right_list_is_empty(self):
        empty = [key for key in _PERM_CFG if not getattr(FormBuilderConfig, key)]
        self.assertEqual(empty, [])

    def test_attributes_carry_the_declared_right(self):
        """
        The rights are constants set from DJANGO_PERMS: the attribute must equal the
        declaration, without going through the config.
        """
        for key, (entity, action) in _PERM_CFG.items():
            with self.subTest(key=key):
                self.assertEqual(getattr(FormBuilderConfig, key), perms(entity, action))

    def test_reading_and_writing_are_distinct_rights(self):
        """
        Concevoir un formulaire et l'afficher sont deux droits ; deposer une soumission
        et relire les soumissions aussi. C'est ce qui permet a un utilisateur de
        remplir un formulaire sans lire les reponses des autres.
        """
        self.assertNotEqual(
            perms("formDefinition", "design"), perms("formDefinition", "query")
        )
        self.assertNotEqual(
            perms("formSubmission", "submit"), perms("formSubmission", "query")
        )
        self.assertNotEqual(
            perms("formDefinition", "query"), perms("formSubmission", "query")
        )

    def test_no_shared_right_ids(self):
        """No identifier sharing is intended in this module."""
        seen = {}
        for entity, actions in DJANGO_PERMS.items():
            for action, (_, right_id) in actions.items():
                seen.setdefault(right_id, []).append((entity, action))
        shared = {rid: who for rid, who in seen.items() if len(who) > 1}
        self.assertEqual(shared, {})

    def test_django_permission_names_are_unique(self):
        seen = {}
        for entity, actions in DJANGO_PERMS.items():
            for action, (name, _) in actions.items():
                seen.setdefault(name, []).append(f"{entity}.{action}")
        shared = {name: who for name, who in seen.items() if len(who) > 1}
        self.assertEqual(shared, {})

    def test_django_permission_names_use_the_app_label(self):
        """L'app_label dans cet assemblage est `form_builder`, pas le nom du paquet pip
        (`openimis-be-form_builder_py`)."""
        for entity, actions in DJANGO_PERMS.items():
            for action, (name, _) in actions.items():
                with self.subTest(entity=entity, action=action):
                    self.assertTrue(name.startswith("form_builder."))

    def test_unknown_entity_or_action_raises(self):
        with self.assertRaises(KeyError):
            perms("nosuchentity", "query")
        with self.assertRaises(KeyError):
            perms("formDefinition", "nosuchaction")
        with self.assertRaises(KeyError):
            django_perms("formSubmission", "nosuchaction")

    def test_extension_write_is_a_declared_but_dormant_right(self):
        """
        151005 est declare et catalogue, mais le chemin d'ecriture des formulaires
        "extension" n'existe pas cote backend : aucun site d'appel ne le controle. On le
        conserve pour ne pas avoir a recreer un autre identifiant le jour ou ce chemin
        sera implemente ; ce test constate l'etat, il ne le valide pas.
        """
        self.assertEqual(perms("formExtension", "write"), ["151005"])
        self.assertIn(("formExtension", "write"), DORMANT)

    # --- the access point through the model -------------------------------
    def test_models_expose_every_action_of_their_entity(self):
        for model, entity in ((FormDefinition, "formDefinition"), (FormSubmission, "formSubmission")):
            for action in DJANGO_PERMS[entity]:
                with self.subTest(entity=entity, action=action):
                    self.assertEqual(
                        model.get_rights(action), configured_perms(entity, action)
                    )
                    self.assertTrue(model.get_rights(action))

    def test_models_return_none_for_an_undeclared_action(self):
        """None means "no rule": the caller must fail closed."""
        self.assertIsNone(FormDefinition.get_rights("nosuchaction"))
        self.assertIsNone(FormSubmission.get_rights("nosuchaction"))
        # Les actions ne fuient pas d'une entite a l'autre.
        self.assertIsNone(FormDefinition.get_rights("submit"))
        self.assertIsNone(FormSubmission.get_rights("design"))

    def test_submission_declares_no_scope_parent(self):
        """
        Une soumission n'herite pas des droits de sa definition : elle a les siens, et
        son proprietaire metier est `submitted_by`. Un `scope_parent = "form"` ferait de
        tout lecteur de formulaire un lecteur des reponses.
        """
        self.assertIsNone(getattr(FormSubmission, "scope_parent", None))

    def test_model_reads_the_configured_value_not_the_declared_default(self):
        original = FormBuilderConfig.gql_form_submission_viewer_perms
        try:
            FormBuilderConfig.gql_form_submission_viewer_perms = ["999999"]
            self.assertEqual(FormSubmission.get_rights("query"), ["999999"])
            self.assertEqual(perms("formSubmission", "query"), ["151004"])
        finally:
            FormBuilderConfig.gql_form_submission_viewer_perms = original

    def test_ids_match_permissions_map(self):
        """The assembly's rights map must carry the same integers."""
        mapping = _load_permissions_map()
        if mapping is None:
            self.skipTest("permissions_map.json not found in this assembly")
        for key, right_id in EXPECTED_MAP_ENTRIES.items():
            with self.subTest(key=key):
                self.assertEqual(str(mapping.get(key)), right_id)
        declared_ids = {
            str(right_id)
            for actions in DJANGO_PERMS.values()
            for _, right_id in actions.values()
        }
        self.assertEqual(set(EXPECTED_MAP_ENTRIES.values()), declared_ids)
