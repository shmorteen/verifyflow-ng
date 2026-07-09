from django.test import SimpleTestCase
from django.urls import reverse


class PublicLegalPageTests(SimpleTestCase):
    def test_legal_pages_are_public_and_marked_for_review(self):
        route_names = [
            "privacy_policy",
            "terms_of_use",
            "data_retention_policy",
            "data_subject_rights",
        ]

        for route_name in route_names:
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Placeholder content - legal review required.")

    def test_landing_page_links_to_every_legal_page(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        for route_name in [
            "privacy_policy",
            "terms_of_use",
            "data_retention_policy",
            "data_subject_rights",
        ]:
            with self.subTest(route_name=route_name):
                self.assertContains(response, reverse(route_name))
