import unittest
from unittest.mock import Mock

from core.documentation_standards_checker import DocumentationStandardsChecker, UnknownObjectException


class TestDocumentationStandardsChecker404(unittest.TestCase):
    def test_check_repository_returns_error_on_404(self):
        # Arrange: mock Github client to raise UnknownObjectException for get_repo
        mock_github = Mock()
        mock_github.get_repo.side_effect = UnknownObjectException(404, "Not Found", None)

        checker = DocumentationStandardsChecker(github_client=mock_github, standards_content="")

        # Act
        result = checker.check_repository("nonexistent_owner/nonexistent_repo")

        # Assert
        self.assertFalse(result.get("success"))
        self.assertIn("Repository not found", result.get("error", ""))
        self.assertEqual(result.get("repository"), "nonexistent_owner/nonexistent_repo")


if __name__ == '__main__':
    unittest.main()
