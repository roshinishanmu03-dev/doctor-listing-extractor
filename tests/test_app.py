import unittest
from app import app
class AppTests(unittest.TestCase):
    def setUp(self): self.client=app.test_client()
    def test_home_renders_named_form_controls(self):
        response=self.client.get("/"); self.assertEqual(response.status_code,200)
        for name in ("url","card","name","specialty","address","city","rating","reviews"): self.assertIn(f'name="{name}"',response.get_data(as_text=True))
    def test_extract_rejects_a_non_https_url(self): self.assertEqual(self.client.post("/extract",json={"url":"http://example.com"}).status_code,400)
    def test_csv_download_uses_expected_columns(self): self.assertIn("name,specialty,address,city,rating,reviews,website",self.client.post("/csv",json={"rows":[{"name":"Example"}]}).get_data(as_text=True))